
import os
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient

load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

if not groq_key or not tavily_key:
    raise ValueError("Check that both API keys are in your .env file.")

# Test Tavily: research a current public disruption
tavily = TavilyClient(api_key=tavily_key)

results = tavily.search(
    query="official severe weather alerts United States",
    max_results=3
)

print("\n--- TAVILY SEARCH RESULTS ---")

for result in results.get("results", []):
    print("\nTitle:", result.get("title"))
    print("URL:", result.get("url"))
    print("Summary:", result.get("content", "")[:250])

# Test Groq: generate a response
groq = Groq(api_key=groq_key)

response = groq.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "user",
            "content": (
                "You are HospitalShield. In one sentence, "
                "explain how researching a weather alert could "
                "help a simulated hospital prepare."
            )
        }
    ],
)

print("\n--- GROQ RESPONSE ---")
print(response.choices[0].message.content)
