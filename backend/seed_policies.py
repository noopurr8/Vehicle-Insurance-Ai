from backend.database import SessionLocal
from backend.models.models import Policy


policies = [
    Policy(
        name="Comprehensive Plus",
        coverage_type="Full",
        description="Comprehensive vehicle insurance with own-damage and third-party coverage.",
        premium=18500,
        features="Own damage, third-party liability, theft, fire, natural calamity, roadside assistance",
    ),
    Policy(
        name="Comprehensive Standard",
        coverage_type="Full",
        description="Standard comprehensive protection for everyday vehicle use.",
        premium=12500,
        features="Own damage, third-party liability, theft, fire, natural calamity",
    ),
    Policy(
        name="Third Party Basic",
        coverage_type="Third Party",
        description="Mandatory third-party liability coverage for the vehicle.",
        premium=4500,
        features="Third-party property damage and liability coverage",
    ),
]


db = SessionLocal()

try:
    existing = db.query(Policy).count()

    if existing == 0:
        db.add_all(policies)
        db.commit()
        print("Policies inserted successfully!")
    else:
        print(f"Policies already exist: {existing}")

finally:
    db.close()