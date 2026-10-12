
import json
import os

from dotenv import load_dotenv
from groq import Groq

from research import research_disruptions

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "openai/gpt-oss-20b"


def run_agent(task: str) -> str:
    print("\n[HospitalShield] Researching the web...")

    findings = research_disruptions(task)

    # Limit the amount of evidence sent to the AI.
    findings = findings[:3]

    for finding in findings:
        finding["content"] = finding["content"][:500]

    print(f"[HospitalShield] Collected {len(findings)} results.")

    evidence = json.dumps(findings, indent=2)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are HospitalShield, an assistant for a "
                    "simulated hospital. Analyze the supplied web "
                    "research and explain possible operational "
                    "impacts. Distinguish verified facts from "
                    "possibilities. Search snippets alone do not "
                    "prove an incident is active. Flag dates that "
                    "are missing, outdated, or inconsistent with "
                    "the requested date. Never invent incidents "
                    "or claim to change real-world systems. "
                    "Recommend actions for human review and cite "
                    "the supplied source URLs. If evidence is "
                    "insufficient, say so."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Task: {task}\n\n"
                    f"Research evidence:\n{evidence}\n\n"
                    "Write a concise report with findings, "
                    "potential hospital impacts, suggested "
                    "precautions, and source URLs."
                ),
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or "No report generated."


if __name__ == "__main__":
    task = input(
        "What should HospitalShield investigate? "
    ).strip()

    if task:
        try:
            print("\n--- HOSPITALSHIELD REPORT ---\n")
            print(run_agent(task))
        except Exception as error:
            print(f"\nHospitalShield encountered an error: {error}")
    else:
        print("Please enter a task.")
