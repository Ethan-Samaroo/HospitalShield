
from simulation import hospital, assess_hospital_state, simulate_driver_shortage


def build_contingency_plan(state: dict) -> dict:
    """Create and validate a basic simulated contingency plan."""

    risks = assess_hospital_state(state)
    actions = []

    staff = state["staff"]
    supplies = state["supplies"]

    if staff["drivers_available"] < staff["drivers_required"]:
        actions.append({
            "risk": "Driver shortage",
            "action": (
                "Review nonurgent deliveries and arrange "
                "approved backup transport for essential supplies."
            ),
            "validation": (
                "Requires human approval and confirmation "
                "that backup transport is available."
            ),
        })

    if staff["nurses_available"] < staff["nurses_required"]:
        actions.append({
            "risk": "Nurse shortage",
            "action": (
                "Ask the staffing coordinator to review "
                "available qualified coverage."
            ),
            "validation": (
                "Do not assign staff beyond verified availability "
                "or qualifications."
            ),
        })

    if supplies["emergency_kits"] < supplies["minimum_emergency_kits"]:
        actions.append({
            "risk": "Emergency kit shortage",
            "action": (
                "Check stock records and request replenishment "
                "through the normal supply process."
            ),
            "validation": (
                "Confirm actual inventory and delivery timing "
                "before relying on replenishment."
            ),
        })

    if (
        supplies["backup_generator_fuel_hours"]
        < supplies["minimum_fuel_hours"]
    ):
        actions.append({
            "risk": "Low backup generator fuel",
            "action": (
                "Request an authorized review of backup-power "
                "readiness and fuel resupply options."
            ),
            "validation": (
                "A qualified facilities team must verify "
                "readiness and approve any action."
            ),
        })



    return {
        "hospital": state["name"],
        "status": (
            "Risks detected" if risks
            else "All monitored thresholds are met"
        ),
        "risks": risks,
        "proposed_actions": actions,
        "requires_human_approval": True,
    }



if __name__ == "__main__":
    print("=== BASELINE PLAN ===")
    baseline = build_contingency_plan(hospital)
    print(baseline)

    print("\n=== DRIVER SHORTAGE SCENARIO ===")
    disrupted_hospital = simulate_driver_shortage(hospital)
    disrupted_plan = build_contingency_plan(disrupted_hospital)
    print(disrupted_plan)
