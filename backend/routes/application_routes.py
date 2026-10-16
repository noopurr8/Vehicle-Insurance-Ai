from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import Application

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("")
def create_application(payload: dict, db: Session = Depends(get_db)):
    customer = payload["customer_details"]
    vehicle = payload["vehicle_details"]

    application = Application(
        name=customer["name"],
        email=customer["email"],
        phone_number=customer["phone_number"],
        address=customer["address"],
        make=vehicle["make"],
        model=vehicle["model"],
        year=vehicle["year"],
        mileage=vehicle["mileage"],
        vin=vehicle["vin"],
        coverage_type=payload["coverage_type"],
        rent_a_car=1 if payload.get("rent_a_car", False) else 0,
        status="Draft",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "application_id": str(application.id),
        "status": application.status,
        "message": "Application created successfully.",
    }

@router.get("/{application_id}/policies")
def list_policies(application_id: str, db: Session = Depends(get_db)):
    application = db.query(Application).filter(
        Application.id == int(application_id)
    ).first()

    if not application:
        return {"error": "Application not found"}

    from backend.models.models import Policy

    policies = db.query(Policy).filter(
        Policy.active == 1,
        Policy.coverage_type == application.coverage_type
    ).all()

    return [
        {
            "policy_id": str(policy.id),
            "name": policy.name,
            "coverage_type": policy.coverage_type,
            "description": policy.description,
            "premium": policy.premium,
            "features": policy.features.split(", "),
        }
        for policy in policies
    ]

@router.post("/{application_id}/select-policy")
def select_policy(
    application_id: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(
        Application.id == int(application_id)
    ).first()

    if not application:
        return {"error": "Application not found"}

    from backend.models.models import Policy

    policy = db.query(Policy).filter(
        Policy.id == int(payload["policy_id"]),
        Policy.active == 1
    ).first()

    if not policy:
        return {"error": "Policy not found"}

    if policy.coverage_type != application.coverage_type:
        return {"error": "Selected policy is not eligible for this application"}

    application.selected_policy_id = policy.id

    db.commit()
    db.refresh(application)

    return {
        "application_id": str(application.id),
        "policy_id": str(policy.id),
        "policy_name": policy.name,
        "premium": policy.premium,
        "status": application.status,
        "message": "Policy selected successfully."
    }

@router.post("/{application_id}/confirm")
def confirm_application(
    application_id: str,
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(
        Application.id == int(application_id)
    ).first()

    if not application:
        return {"error": "Application not found"}

    if not application.selected_policy_id:
        return {"error": "No policy has been selected"}

    if application.status == "Confirmed":
        return {
            "application_id": str(application.id),
            "policy_number": application.policy_number,
            "status": application.status,
            "message": "Application is already confirmed."
        }

    application.policy_number = f"POL-2026-{application.id:05d}"
    application.status = "Confirmed"

    db.commit()
    db.refresh(application)

    return {
        "application_id": str(application.id),
        "policy_number": application.policy_number,
        "status": application.status,
        "message": "Application confirmed successfully."
    }