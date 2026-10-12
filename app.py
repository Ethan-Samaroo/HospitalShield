
import streamlit as st

from simulation import (
    hospital,
    assess_hospital_state,
    simulate_driver_shortage,
)
from planning import build_contingency_plan
from research import research_disruptions
from decision import explain_plan


st.set_page_config(
    page_title="HospitalShield",
    page_icon="🏥",
    layout="wide",
)

st.title("🏥 HospitalShield")
st.caption(
    "AI-assisted disruption research and contingency planning "
    "for a simulated hospital."
)

st.warning(
    "Demonstration only. All hospital resources are fictional. "
    "Recommendations require human review."
)

scenario_name = st.selectbox(
    "Choose a simulation scenario",
    [
        "Normal operations",
        "Driver shortage",
    ],
)

if scenario_name == "Driver shortage":
    scenario = simulate_driver_shortage(hospital)
else:
    scenario = hospital

st.subheader("Hospital resource status")

staff_col, supply_col = st.columns(2)

with staff_col:
    st.markdown("**Staff availability**")

    for role, amount in scenario["staff"].items():
        st.write(f"{role.replace('_', ' ').title()}: {amount}")

with supply_col:
    st.markdown("**Supply and backup power**")

    for item, amount in scenario["supplies"].items():
        st.write(f"{item.replace('_', ' ').title()}: {amount}")

st.subheader("Current simulated risks")

risks = assess_hospital_state(scenario)

for risk in risks:
    if risk.startswith("No simulated"):
        st.success(risk)
    else:
        st.error(risk)

st.divider()

if st.button("Research and generate contingency plan", type="primary"):
    with st.spinner("Researching public information..."):
        try:
            findings = research_disruptions(
                "official active weather alerts and public transit disruptions "
                "Long Island New York"
            )

            

            for finding in findings:
                finding["content"] = finding["content"][:400]

        except Exception as error:
            st.error(f"Research failed: {error}")
            st.stop()
    
    st.subheader("Research findings")

    if not findings:
        st.warning(
            "No relevant disruption candidates were returned. "
            "This does not prove that no disruptions exist."
        )
    else:
        for finding in findings:
            st.markdown(f"### {finding.get('title', 'Untitled')}")
            st.write(finding.get("content", "No summary available."))

            st.write(
                f"Source status: "
                f"{finding.get('source_status', 'Unknown')}"
            )
            st.write(
                f"Date status: {finding.get('date_status', 'Unknown')}"
            )
            st.write(f"Article verified: {finding.get('verified', False)}")

            corroboration = finding.get("event_corroboration")

            if corroboration:
                st.markdown("**Official event corroboration**")
                st.write(corroboration["status"])
                st.write(corroboration["notes"])
                st.markdown(
                    f"[Open official source]({corroboration['source_url']})"
                )
                st.caption(
                    "The planned transit event is corroborated; "
                    "its impact on the simulated hospital is unknown."
                )
            else:
                st.caption(
                    "No matching official corroboration is recorded."
                )

            sources = finding.get("supporting_sources", [])

            if sources:
                with st.expander(
                    f"Supporting reports ({len(sources)})"
                ):
                    for source in sources:
                        title = source.get("title", "Untitled")
                        url = source.get("url", "")

                        if url:
                            st.markdown(f"[{title}]({url})")
                        else:
                            st.write(title)

            else:
                url = finding.get("url", "")
                if url:
                    st.markdown(f"[Open source]({url})")

            st.divider()


    plan = build_contingency_plan(scenario)

    st.subheader("Validated contingency plan")

    if plan["status"] == "All monitored thresholds are met":
        st.success("All monitored staffing and supply thresholds are met.")
        st.write("No additional contingency action is indicated by the current simulation data.")
    else:
        st.warning("Potential resource constraints detected.")
        for risk in plan["risks"]:
            st.write(f"- {risk}")

        for action in plan["proposed_actions"]:
            st.markdown(f"**Risk:** {action['risk']}")
            st.write(f"**Proposed action:** {action['action']}")
            st.write(f"**Validation:** {action['validation']}")

    st.info("Human approval is required before any proposed action.")


    with st.spinner("Generating AI explanation..."):
        try:
            report = explain_plan(scenario, findings, plan)
            st.subheader("AI decision report")
            st.markdown(report)
        except Exception as error:
            st.error(f"AI explanation failed: {error}")
