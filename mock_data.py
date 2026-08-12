"""
mock_data.py
Stand-ins for Member 1's Incident Analyzer output and Member 2's Hindsight
search results. Lets Member 3 be built, tested, and demoed without waiting
on the other two modules.
"""

from models import Incident, HistoricalIncident, PastSolution, Severity

MOCK_INCIDENT = Incident(
    incident_id="INC-1042",
    incident_type="database_timeout",
    severity=Severity.high,
    affected_service="payments-api",
    root_cause="Connection pool exhaustion under high load",
    summary="payments-api started returning 504s at 14:02 UTC. Logs show DB "
    "connection pool hitting max size (50) with queued requests timing out.",
    raw_logs="ERROR: could not obtain connection from pool within 30000ms",
)

MOCK_HISTORY = [
    HistoricalIncident(
        incident_id="INC-0871",
        incident_type="database_timeout",
        affected_service="payments-api",
        similarity_score=0.93,
        solutions=[
            PastSolution(
                action_taken="Increase DB connection pool size from 50 to 100 and "
                "add exponential backoff on retries",
                was_successful=True,
                notes="Resolved the incident within 10 minutes, no recurrence in 30 days.",
            ),
            PastSolution(
                action_taken="Restart payments-api pods",
                was_successful=False,
                notes="Provided temporary relief but timeouts returned within 20 minutes.",
            ),
        ],
    ),
    HistoricalIncident(
        incident_id="INC-0654",
        incident_type="database_timeout",
        affected_service="orders-api",
        similarity_score=0.61,
        solutions=[
            PastSolution(
                action_taken="Add read replica and route read-heavy queries to it",
                was_successful=True,
                notes="Different root cause (read load), but same symptom pattern.",
            )
        ],
    ),
]
