"""
models.py
Data contracts for the AI Recommendation Agent (Member 3).

These shapes are the "integration contract" with the other two modules:
- Member 1 (Incident Analyzer) produces something that fits `Incident`
- Member 2 (Hindsight Memory Engine) produces something that fits `HistoricalIncident`
- Member 3 (this module) consumes both and produces `RecommendationResponse`
  and, after feedback, an `OutcomeRecord` that Member 2 can store back into Hindsight.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# ---------------------------------------------------------------------------
# Input: what Member 1 (Incident Analyzer) hands over
# ---------------------------------------------------------------------------

class Incident(BaseModel):
    incident_id: str = Field(..., description="Unique ID for this incident")
    incident_type: str = Field(..., description="e.g. 'database_timeout', 'memory_leak'")
    severity: Severity
    affected_service: str
    root_cause: Optional[str] = Field(None, description="Best-guess root cause from Member 1")
    summary: str = Field(..., description="Human-readable structured incident summary")
    raw_logs: Optional[str] = Field(None, description="Optional raw log/stack trace snippet")
    timestamp: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Input: what Member 2 (Hindsight Memory Engine) hands over
# ---------------------------------------------------------------------------

class PastSolution(BaseModel):
    action_taken: str
    was_successful: bool
    notes: Optional[str] = None


class HistoricalIncident(BaseModel):
    incident_id: str
    incident_type: str
    affected_service: str
    similarity_score: Optional[float] = Field(
        None, description="0-1 similarity score returned by Hindsight search"
    )
    solutions: List[PastSolution] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Request into Member 3's core endpoint
# ---------------------------------------------------------------------------

class RecommendationRequest(BaseModel):
    incident: Incident
    historical_incidents: List[HistoricalIncident] = Field(
        default_factory=list,
        description="Similar past incidents + their solutions, from Member 2's Hindsight search",
    )


# ---------------------------------------------------------------------------
# Output: the recommendation itself
# ---------------------------------------------------------------------------

class RankedAction(BaseModel):
    action: str
    confidence: float = Field(..., ge=0, le=1)
    rationale: str
    based_on_incident_ids: List[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    incident_id: str
    recommended_action: str
    confidence: float
    reasoning: str
    ranked_alternatives: List[RankedAction] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Feedback loop: human/ops confirms what actually happened
# ---------------------------------------------------------------------------

class FeedbackRequest(BaseModel):
    incident_id: str
    action_taken: str
    was_successful: bool
    resolution_notes: Optional[str] = None


class OutcomeRecord(BaseModel):
    """
    This is the record Member 3 hands back — Member 2 stores this into
    Hindsight so future recommendations can learn from it.
    """
    incident_id: str
    action_taken: str
    was_successful: bool
    resolution_notes: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
