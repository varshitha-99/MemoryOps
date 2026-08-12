"""
main.py
FastAPI service for Member 3 — the AI Recommendation Agent.

Run:
    uvicorn main:app --reload --port 8003

Then open http://127.0.0.1:8003/docs for interactive Swagger UI.

Endpoints
---------
POST /recommend        -> core function: incident + history -> recommendation
POST /feedback          -> record whether the recommendation actually worked
GET  /demo/recommend    -> runs /recommend against built-in mock data (no
                            need to wait for Member 1 / Member 2 to be ready)
GET  /health            -> liveness check
"""

from fastapi import FastAPI, HTTPException
from typing import Dict

from models import (
    RecommendationRequest,
    RecommendationResponse,
    FeedbackRequest,
    OutcomeRecord,
)
from agent import generate_recommendation
from mock_data import MOCK_INCIDENT, MOCK_HISTORY

app = FastAPI(
    title="MemoryOps - AI Recommendation Agent",
    description="Member 3 module: ranks and recommends incident resolutions, "
    "explains its reasoning, and turns feedback into a record Hindsight can store.",
    version="1.0.0",
)

# In-memory store standing in for "send this to Member 2 / Hindsight".
# Swap this for a real call to Member 2's API once integration starts.
_outcome_log: Dict[str, OutcomeRecord] = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(payload: RecommendationRequest):
    """
    Core endpoint. Accepts:
      - `incident`: Member 1's structured incident output
      - `historical_incidents`: Member 2's Hindsight search results

    Returns a ranked recommendation with reasoning.
    """
    try:
        return generate_recommendation(payload.incident, payload.historical_incidents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {e}")


@app.post("/feedback", response_model=OutcomeRecord)
def feedback(payload: FeedbackRequest):
    """
    Accepts resolution feedback after an action was tried in the real world.
    Produces an OutcomeRecord that Member 2 pulls (or that gets pushed to
    Member 2's API) to store back into Hindsight for future recommendations.
    """
    record = OutcomeRecord(
        incident_id=payload.incident_id,
        action_taken=payload.action_taken,
        was_successful=payload.was_successful,
        resolution_notes=payload.resolution_notes,
    )
    _outcome_log[payload.incident_id] = record
    return record


@app.get("/outcomes/{incident_id}", response_model=OutcomeRecord)
def get_outcome(incident_id: str):
    """Lets Member 2 (or a test script) pull back a stored outcome record."""
    record = _outcome_log.get(incident_id)
    if not record:
        raise HTTPException(status_code=404, detail="No outcome recorded for this incident_id")
    return record


@app.get("/demo/recommend", response_model=RecommendationResponse)
def demo_recommend():
    """
    Self-contained demo: Incident + Past Solutions -> AI Agent -> Recommended Action.
    Uses built-in mock data standing in for Member 1 and Member 2's output,
    so this module is demoable before integration.
    """
    return generate_recommendation(MOCK_INCIDENT, MOCK_HISTORY)
