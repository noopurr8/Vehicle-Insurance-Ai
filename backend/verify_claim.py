from backend.database import SessionLocal
from backend.models.models import Claim

db = SessionLocal()

claims = db.query(Claim).all()

print(f"Total claims in database: {len(claims)}")

for claim in claims:
    print("\nClaim ID:", claim.id)
    print("Policy Number:", claim.policy_number)
    print("Vehicle Number:", claim.extracted_vehicle_number)
    print("Damage:", claim.damage_type)
    print("Damage Count:", claim.damage_count)
    print("Fraud Probability:", claim.fraud_probability)
    print("Fraud Prediction:", claim.fraud_prediction)
    print("Priority:", claim.priority)
    print("Status:", claim.status)

db.close()