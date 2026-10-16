def calculate_priority(damage_count, fraud_probability, damage_types):
    """
    Calculate claim priority using damage severity and fraud risk.
    """

    severe_damage = {
        "glass shatter",
        "lamp broken",
        "tire flat"
    }

    has_severe_damage = any(
        damage.lower() in severe_damage
        for damage in damage_types
    )

    if fraud_probability >= 0.70:
        priority = "High"
    elif has_severe_damage or damage_count >= 3:
        priority = "High"
    elif fraud_probability >= 0.40 or damage_count >= 2:
        priority = "Medium"
    else:
        priority = "Low"

    return priority


if __name__ == "__main__":
    print("Claim priority service ready.")