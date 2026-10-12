
import json
import os

from dotenv import load_dotenv
from groq import Groq

from planning import build_contingency_plan

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-20b"


def explain_plan(
    hospital_state: dict,
    research_findings: list[dict],
    plan: dict,
) -> str:
    """Ask the AI to explain a validated simulated plan."""

    prompt_data = {
        "hospital_state": hospital_state,
        "research_findings": research_findings,
        "validated_plan": plan,
    }

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are HospitalShield, an AI assistant for a fictional "
                    "hospital simulation.\n\n"

                    "Rules:\n"
                    "1. The Python-generated plan is authoritative for simulated "
                    "staffing and supply thresholds.\n"
                    "2. 'No shortages detected' is a normal status, NOT a risk. "
                    "Do not invent risks when all thresholds are met.\n"
                    "3. Distinguish confirmed external events from their possible "
                    "impact on the simulated hospital.\n"
                    "4. A finding marked verified=False is not independently "
                    "verified. If official corroboration is supplied, explain "
                    "exactly what it confirms and what remains unknown.\n"
                    "5. Never infer a hospital shortage, delivery delay, or "
                    "patient-care impact without supporting evidence.\n"
                    "6. Never invent facts, dates, source details, monitoring "
                    "systems, or verification results.\n"
                    "7. Actions are proposals for human review. Never claim "
                    "that an action has been carried out.\n"
                    "8. Include source URLs as plain URLs in parentheses. "
                    "Do not generate Markdown links, nested brackets, or citation markup.\n"
                    "9. Avoid repetition and generic explanations.\n\n"

                    "Use these exact headings:\n"
                    "## Current Status\n"
                    "## External Findings\n"
                    "## Recommendation\n"
                    "## Human Review\n\n"

                    "Under Current Status, state whether simulated thresholds "
                    "are met.\n"
                    "Under External Findings, describe relevant evidence and "
                    "separate confirmed event details from unknown hospital impacts.\n"
                    "Under Recommendation, report the proposed action or state "
                    "that no additional contingency action is indicated by the "
                    "available evidence when all monitored thresholds are met "
                    "and no hospital impact is established.\n"
                    "Under Recommendation, if all monitored thresholds are met and "
                    "no hospital impact is established, use this exact sentence: "
                    "'No additional contingency action is indicated by the available "
                    "evidence. The impact of the external event on hospital operations "
                    "has not been established.' Do not substitute a shorter version.\n"
                    "Do not claim that no action is required or that an external "
                    "event cannot affect the hospital.\n"
                    "Do not claim that a proposed action will solve or resolve a risk "
                    "unless the provided evidence establishes that outcome. Describe "
                    "intended benefits as possibilities, and preserve any validation "
                    "conditions from the plan.\n"

                    "Under Human Review, list only specific checks relevant "
                    "to approving the proposal.\n\n"

                    "Keep the report under 250 words. If there are no relevant "
                    "external findings, say so explicitly."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Explain this hospital scenario and plan. "
                    "Describe the key risk, why it matters, what "
                    "the proposed action accomplishes, and what "
                    "a human should verify before approving it.\n\n"
                    + json.dumps(prompt_data, indent=2)
                ),
            },
        ],
        temperature=0.2,
    )

    report = response.choices[0].message.content or "No explanation generated."

# Enforce the recommendation using the validated Python plan.
    if not plan["risks"] and not plan["proposed_actions"]:
        recommendation = (
            "## Recommendation\n\n"
            "No additional contingency action is indicated by the available "
            "evidence. The impact of the external event on hospital operations "
            "has not been established."
        )

    else:
        actions = "\n".join(
            f"- {action['risk']}: {action['action']} "
            f"Validation: {action['validation']}"
            for action in plan["proposed_actions"]
        )

        recommendation = (
            "## Recommendation\n\n"
            "The validated plan identifies the following risk(s) and proposed "
            "action(s). These actions are proposals, not completed actions. "
            "Their effectiveness has not been established.\n\n"
            f"{actions}\n\n"
            "Human approval is required before any proposed action. "
            "Confirm the stated validation conditions before approval."
        )

# Replace the model-generated recommendation with the controlled version.
    if "## Recommendation" in report:
        before, remainder = report.split("## Recommendation", 1)

        if "## Human Review" in remainder:
            _, human_review = remainder.split("## Human Review", 1)
            report = (
                before.rstrip()
                + "\n\n"
                + recommendation
                + "\n\n## Human Review"
                + human_review
            )
        else:
            report = before.rstrip() + "\n\n" + recommendation
    else:
        report = report.rstrip() + "\n\n" + recommendation

    return report



if __name__ == "__main__":
    from simulation import hospital, simulate_driver_shortage
    from research import research_disruptions

    # Test with a simulated driver shortage.
    scenario = simulate_driver_shortage(hospital)
    plan = build_contingency_plan(scenario)

    print("Researching current potential disruptions...")
    findings = research_disruptions(
        "official Long Island New York weather and transit alerts today"
    )

    # Limit the evidence sent to the model.
    findings = findings[:3]
    for finding in findings:
        finding["content"] = finding["content"][:400]

    print("\n=== HOSPITALSHIELD DECISION REPORT ===\n")
    print(explain_plan(scenario, findings, plan))
