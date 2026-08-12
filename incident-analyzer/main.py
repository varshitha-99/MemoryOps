import os
from dotenv import load_dotenv
from groq import Groq
from prompt import INCIDENT_ANALYZER_PROMPT

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

error_message = """
ERROR: Payment API failed.
Database connection timeout.
Connection pool exhausted.
HTTP 503 returned.
"""

prompt = INCIDENT_ANALYZER_PROMPT.format(
    error_message=error_message
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    temperature=0
)

print(response.choices[0].message.content)
