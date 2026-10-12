
hospital = {
    "name": "Northstar General (Simulated)",
    "staff": {
        "nurses_available": 12,
        "nurses_required": 10,
        "drivers_available": 3,
        "drivers_required": 2,
    },
    "supplies": {
        "emergency_kits": 24,
        "minimum_emergency_kits": 10,
        "backup_generator_fuel_hours": 36,
        "minimum_fuel_hours": 12,
    },
}



def assess_hospital_state(state: dict) -> list[str]:
    """Identify staffing and supply constraints."""

    risks = []

    staff = state["staff"]
    supplies = state["supplies"]

    if staff["nurses_available"] < staff["nurses_required"]:
        risks.append("Insufficient available nurses")

    if staff["drivers_available"] < staff["drivers_required"]:
        risks.append("Insufficient available drivers")

    if supplies["emergency_kits"] < supplies["minimum_emergency_kits"]:
        risks.append("Emergency kit stock below minimum")

    if (
        supplies["backup_generator_fuel_hours"]
        < supplies["minimum_fuel_hours"]
    ):
        risks.append("Backup generator fuel below minimum")

    return risks


def simulate_driver_shortage(state: dict) -> dict:
    """Simulate two drivers becoming unavailable without
    changing the original hospital state."""

    import copy

    simulated_state = copy.deepcopy(state)
    simulated_state["staff"]["drivers_available"] = max(
        0,
        simulated_state["staff"]["drivers_available"] - 2,
    )

    return simulated_state

if __name__ == "__main__":
    print(f"Hospital: {hospital['name']}")
    print("\nHospital assessment:")

    for risk in assess_hospital_state(hospital):
        print("-", risk)
