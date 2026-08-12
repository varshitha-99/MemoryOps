import os
from dotenv import load_dotenv
from hindsight_client import Hindsight

# Load variables from .env
load_dotenv()

# Connect to Hindsight
client = Hindsight(
    base_url=os.getenv("HINDSIGHT_BASE_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

# Our project's memory bank
BANK_ID = "memoryops-incidents"

# --------------------------------------------------
# 1. Create the memory bank
# --------------------------------------------------

try:
    client.create_bank(
        bank_id=BANK_ID,
        name="MemoryOps Incident Memory"
    )
    print("Memory bank created successfully!")

except Exception as e:
    print("Memory bank may already exist.")
    print("Details:", e)


# --------------------------------------------------
# 2. Store a test incident
# --------------------------------------------------

incident = """
Incident ID: INC-001

Service: Payment API

Incident Type: Database

Severity: High

Root Cause:
Database connection pool exhaustion

Solution:
Increased database connection pool from 50 to 100

Outcome:
Successful

Summary:
Payment API was unavailable because database connections
were exhausted, causing database connection timeouts and HTTP 503 errors.
"""

try:
    result = client.retain(
        bank_id=BANK_ID,
        content=incident
    )

    print("\nIncident stored successfully!")
    print(result)

except Exception as e:
    print("\nError storing incident:")
    print(e)


# --------------------------------------------------
# 3. Recall the incident from Hindsight
# --------------------------------------------------

query = """
Have we experienced a database connection timeout
in the Payment API before? What solution worked?
"""

try:
    result = client.recall(
        bank_id=BANK_ID,
        query=query
    )

    print("\n==============================")
    print("RECALLED MEMORIES")
    print("==============================")

    print(result)

except Exception as e:
    print("\nError recalling memory:")
    print(e)
