# Member 3 — AI Recommendation Agent

Standalone module for MemoryOps. Takes an incident + retrieved historical
incidents, ranks possible fixes, explains its reasoning, and turns operator
feedback into a record that Member 2 (Hindsight) can store for next time.

Built to run and demo **completely independently** of Members 1 and 2, using
built-in mock data that mimics their eventual output shapes.

## Files

| File | Purpose |
|---|---|
| `models.py` | Pydantic schemas — the integration contract with Members 1 & 2 |
| `agent.py` | Core logic: builds the LLM prompt, calls Claude, ranks actions, falls back to a rule-based ranker if no API key is set |
| `mock_data.py` | Fake incident + fake Hindsight search results, standing in for Members 1 & 2 |
| `main.py` | FastAPI app exposing the endpoints below |
| `requirements.txt` | Dependencies |

## Setup

```bash
pip install -r requirements.txt

# Optional but recommended: enables real LLM reasoning instead of the
# rule-based fallback. Without it, the module still runs and returns
# sensible recommendations based on similarity score + past success.
export ANTHROPIC_API_KEY=your_key_here

uvicorn main:app --reload --port 8003
```

Open `http://127.0.0.1:8003/docs` for interactive Swagger UI (good for the
Postman/Swagger testing step in the project plan).

## Endpoints

### `GET /demo/recommend`
Runs the full pipeline against built-in mock data. Use this to demo the
module before Members 1 and 2 are ready — no request body needed.

### `POST /recommend`
The real endpoint. Body:
```json
{
  "incident": {
    "incident_id": "INC-1042",
    "incident_type": "database_timeout",
    "severity": "high",
    "affected_service": "payments-api",
    "root_cause": "Connection pool exhaustion under high load",
    "summary": "payments-api returning 504s, DB pool maxed out."
  },
  "historical_incidents": [
    {
      "incident_id": "INC-0871",
      "incident_type": "database_timeout",
      "affected_service": "payments-api",
      "similarity_score": 0.93,
      "solutions": [
        {
          "action_taken": "Increase DB connection pool size to 100",
          "was_successful": true,
          "notes": "Resolved within 10 minutes."
        }
      ]
    }
  ]
}
```
Returns a `RecommendationResponse` with `recommended_action`, `confidence`,
`reasoning`, and up to 3 `ranked_alternatives`.

### `POST /feedback`
Body:
```json
{
  "incident_id": "INC-1042",
  "action_taken": "Increase DB connection pool size to 100",
  "was_successful": true,
  "resolution_notes": "Confirmed no more 504s after 15 minutes."
}
```
Stores an `OutcomeRecord` and returns it.

### `GET /outcomes/{incident_id}`
Lets Member 2 (or a script) pull back a stored outcome to write into Hindsight.

### `GET /health`
Liveness check.

## Testing standalone

```bash
curl http://127.0.0.1:8003/demo/recommend
```

This alone is enough for your demo: `Incident + Past Solutions → AI Agent →
Recommended Action → Feedback`, using `mock_data.py` for the first half and
`/feedback` for the second half.

## Integration notes (for later)

- Member 1 should produce JSON matching the `Incident` schema in `models.py`
  and POST it (plus historical incidents from Member 2) to `/recommend`.
- Member 2 should implement a search endpoint returning a list matching
  `HistoricalIncident`, and can either poll `GET /outcomes/{incident_id}`
  after feedback is submitted, or you can add a direct HTTP call from
  `main.py`'s `/feedback` handler to push the `OutcomeRecord` straight into
  Member 2's Hindsight store.
- Swap `_outcome_log` (in-memory dict in `main.py`) for that real call once
  Member 2's API is ready — everything else stays the same.
