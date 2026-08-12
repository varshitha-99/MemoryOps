"""
agent.py
The decision-making core of Member 3.

Given an Incident + a list of HistoricalIncidents (with their past solutions),
this module asks an LLM to rank the candidate actions and explain its reasoning.

Design choice: everything here is a pure function of
(incident, historical_incidents) -> RecommendationResponse.
That means Member 3 can be built, tested, and demoed completely on its own,
using hand-written mock data that *simulates* what Member 1 and Member 2
will eventually send.
"""

import os
import json
import httpx
from typing import List

from models import (
    Incident,
    HistoricalIncident,
    RecommendationResponse,
    RankedAction,
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
# Verify the current recommended model string in the Claude API docs before
# shipping to production: https://docs.claude.com/en/docs/about-claude/models/overview
MODEL_NAME = os.environ.get("AGENT_MODEL", "claude-sonnet-5")


def _build_prompt(incident: Incident, history: List[HistoricalIncident]) -> str:
    history_block = []
    for h in history:
        sols = "; ".join(
            f"{s.action_taken} ({'worked' if s.was_successful else 'failed'})"
            for s in h.solutions
        ) or "no recorded solutions"
        history_block.append(
            f"- Past incident {h.incident_id} ({h.incident_type}, "
            f"service={h.affected_service}, similarity={h.similarity_score}): {sols}"
        )
    history_text = "\n".join(history_block) if history_block else "No similar past incidents found."

    return f"""You are an SRE incident-response assistant.

CURRENT INCIDENT
- ID: {incident.incident_id}
- Type: {incident.incident_type}
- Severity: {incident.severity}
- Affected service: {incident.affected_service}
- Suspected root cause: {incident.root_cause or "unknown"}
- Summary: {incident.summary}

SIMILAR PAST INCIDENTS AND THEIR OUTCOMES
{history_text}

TASK
Recommend the single best next action to resolve the current incident, using the
past incidents as evidence where relevant. Then list up to 3 ranked alternative
actions with a confidence score (0-1) and short rationale for each.

Respond ONLY with valid JSON, no markdown fences, matching exactly this schema:
{{
  "recommended_action": string,
  "confidence": number between 0 and 1,
  "reasoning": string explaining why this is the top pick,
  "ranked_alternatives": [
    {{
      "action": string,
      "confidence": number between 0 and 1,
      "rationale": string,
      "based_on_incident_ids": [string]
    }}
  ]
}}"""


def _call_claude(prompt: str) -> dict:
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL_NAME,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    text = "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


def _rule_based_fallback(incident: Incident, history: List[HistoricalIncident]) -> dict:
    """
    Used when no ANTHROPIC_API_KEY is set (e.g. local dev/demo before all
    three members integrate). Picks the most similar past incident's most
    successful action, purely so the API contract is fully testable offline.
    """
    candidates = []
    for h in history:
        for s in h.solutions:
            if s.was_successful:
                candidates.append((h.similarity_score or 0.0, h.incident_id, s.action_taken, s.notes))

    if not candidates:
        return {
            "recommended_action": f"Escalate to on-call engineer for {incident.affected_service}",
            "confidence": 0.3,
            "reasoning": "No similar past incidents with a successful resolution were found, "
            "so escalation is the safest default action.",
            "ranked_alternatives": [],
        }

    candidates.sort(key=lambda c: c[0], reverse=True)
    top = candidates[0]
    alternatives = [
        {
            "action": c[2],
            "confidence": round(min(c[0], 0.95), 2),
            "rationale": c[3] or f"Successfully resolved a similar incident ({c[1]}).",
            "based_on_incident_ids": [c[1]],
        }
        for c in candidates[1:4]
    ]

    return {
        "recommended_action": top[2],
        "confidence": round(min(top[0], 0.95), 2) if top[0] else 0.5,
        "reasoning": f"This action resolved the most similar past incident ({top[1]}, "
        f"similarity={top[0]}), which shares incident type or service with the current one.",
        "ranked_alternatives": alternatives,
    }


def generate_recommendation(
    incident: Incident, history: List[HistoricalIncident]
) -> RecommendationResponse:
    if ANTHROPIC_API_KEY:
        try:
            result = _call_claude(_build_prompt(incident, history))
        except Exception:
            # LLM call failed (network, bad key, parse error, etc.) -> degrade gracefully
            result = _rule_based_fallback(incident, history)
    else:
        result = _rule_based_fallback(incident, history)

    alternatives = [RankedAction(**alt) for alt in result.get("ranked_alternatives", [])]

    return RecommendationResponse(
        incident_id=incident.incident_id,
        recommended_action=result["recommended_action"],
        confidence=result["confidence"],
        reasoning=result["reasoning"],
        ranked_alternatives=alternatives,
    )
