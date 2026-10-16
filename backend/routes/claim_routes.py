from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
import os
import shutil

from backend.database import get_db
from backend.models.models import Claim

from ai.ocr.ocr_service import process_document
from ai.damage_detection.damage_service import detect_damage
from ai.fraud_detection.fraud_service import predict_fraud
from ai.claim_priority.priority_service import calculate_priority


router = APIRouter(prefix="/claims", tags=["Claims"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/process")
async def process_claim(
    document: UploadFile = File(...),
    vehicle_image: UploadFile = File(...),
    claim_description: str = Form(""),
    db: Session = Depends(get_db)
):

    document_path = os.path.join(UPLOAD_DIR, document.filename)
    vehicle_image_path = os.path.join(UPLOAD_DIR, vehicle_image.filename)

    with open(document_path, "wb") as buffer:
        shutil.copyfileobj(document.file, buffer)

    with open(vehicle_image_path, "wb") as buffer:
        shutil.copyfileobj(vehicle_image.file, buffer)

    # 1. OCR
    ocr_result = process_document(document_path)

    # 2. Damage detection
    damage_result = detect_damage(vehicle_image_path)

    # 3. Fraud detection
    fraud_data = {
        "Month": "Dec",
        "WeekOfMonth": 1,
        "DayOfWeek": "Monday",
        "Make": "Honda",
        "AccidentArea": "Urban",
        "DayOfWeekClaimed": "Monday",
        "MonthClaimed": "Dec",
        "WeekOfMonthClaimed": 1,
        "Sex": "Male",
        "MaritalStatus": "Single",
        "Age": 30,
        "Fault": "Policy Holder",
        "PolicyType": "Sedan - Collision",
        "VehicleCategory": "Sport",
        "VehiclePrice": "20000 to 29000",
        "RepNumber": 10,
        "Deductible": 400,
        "DriverRating": 1,
        "Days_Policy_Accident": "more than 30",
        "Days_Policy_Claim": "more than 30",
        "PastNumberOfClaims": "none",
        "AgeOfVehicle": "3 years",
        "AgeOfPolicyHolder": "31 to 35",
        "PoliceReportFiled": "Yes",
        "WitnessPresent": "No",
        "AgentType": "External",
        "NumberOfSuppliments": "none",
        "AddressChange_Claim": "1 year",
        "NumberOfCars": "1 vehicle",
        "Year": 1994,
        "BasePolicy": "Collision"
    }

    fraud_result = predict_fraud(fraud_data)

    # 4. Priority
    damage_types = [
        item["damage_type"]
        for item in damage_result["damages"]
    ]

    priority = calculate_priority(
        damage_result["damage_count"],
        fraud_result["fraud_probability"],
        damage_types
    )

    # 5. Save claim to PostgreSQL
    claim = Claim(
        claim_description=claim_description,
        ocr_text=ocr_result["raw_text"],
        policy_number=ocr_result["extracted_fields"]["policy_number"],
        extracted_vehicle_number=ocr_result["extracted_fields"]["vehicle_number"],
        damage_type=", ".join(damage_types) if damage_types else None,
        damage_count=damage_result["damage_count"],
        fraud_probability=fraud_result["fraud_probability"],
        fraud_prediction=fraud_result["fraud_prediction"],
        priority=priority,
        status="Pending"
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    return {
        "claim_id": claim.id,
        "claim_description": claim_description,
        "ocr": ocr_result,
        "damage_detection": damage_result,
        "fraud_detection": fraud_result,
        "priority": priority,
        "status": claim.status,
        "database_saved": True
    }

@router.post("")
def create_chat_claim(payload: dict, db: Session = Depends(get_db)):
    policy_number = payload.get("policy_number")
    accident_details = payload.get("accident_details", {})

    if not policy_number:
        return {"error": "Policy number is required"}

    # Verify that the policy exists in a confirmed application
    from backend.models.models import Application

    application = db.query(Application).filter(
        Application.policy_number == policy_number,
        Application.status == "Confirmed"
    ).first()

    if not application:
        return {"error": "Valid confirmed policy not found"}

    claim = Claim(
        policy_number=policy_number,
        claim_description=accident_details.get("description", ""),
        status="Draft"
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    return {
        "claim_id": str(claim.id),
        "policy_number": policy_number,
        "accident_time": accident_details.get("accident_time"),
        "accident_location": accident_details.get("accident_location"),
        "description": accident_details.get("description", ""),
        "status": claim.status,
        "message": "Claim draft created successfully."
    }

@router.post("/{claim_id}/confirm")
def confirm_chat_claim(
    claim_id: str,
    db: Session = Depends(get_db)
):
    claim = db.query(Claim).filter(
        Claim.id == int(claim_id)
    ).first()

    if not claim:
        return {"error": "Claim not found"}

    if claim.status != "Draft":
        return {
            "claim_id": str(claim.id),
            "claim_number": f"CLM-2026-{claim.id:05d}",
            "status": claim.status,
            "message": "Claim has already been submitted."
        }

    claim.status = "Pending"

    db.commit()
    db.refresh(claim)

    claim_number = f"CLM-2026-{claim.id:05d}"

    return {
        "claim_id": str(claim.id),
        "claim_number": claim_number,
        "policy_number": claim.policy_number,
        "status": claim.status,
        "message": "Claim submitted successfully."
    }

@router.get("/{claim_number}/status")
def get_claim_status(
    claim_number: str,
    db: Session = Depends(get_db)
):
    if not claim_number.startswith("CLM-2026-"):
        return {"error": "Invalid claim number"}

    try:
        claim_id = int(claim_number.replace("CLM-2026-", ""))
    except ValueError:
        return {"error": "Invalid claim number"}

    claim = db.query(Claim).filter(
        Claim.id == claim_id
    ).first()

    if not claim:
        return {"error": "Claim not found"}

    return {
        "claim_number": claim_number,
        "policy_number": claim.policy_number,
        "status": claim.status,
        "priority": claim.priority,
        "damage_type": claim.damage_type,
        "damage_count": claim.damage_count,
        "fraud_probability": claim.fraud_probability,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
    }

@router.post("/{claim_id}/process-ai")
async def process_existing_claim_ai(
    claim_id: str,
    document: UploadFile = File(...),
    vehicle_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    claim = db.query(Claim).filter(
        Claim.id == int(claim_id)
    ).first()

    if not claim:
        return {"error": "Claim not found"}

    document_path = os.path.join(
        UPLOAD_DIR,
        document.filename
    )

    vehicle_image_path = os.path.join(
        UPLOAD_DIR,
        vehicle_image.filename
    )

    with open(document_path, "wb") as buffer:
        shutil.copyfileobj(
            document.file,
            buffer
        )

    with open(vehicle_image_path, "wb") as buffer:
        shutil.copyfileobj(
            vehicle_image.file,
            buffer
        )

    # OCR
    ocr_result = process_document(document_path)

    # Damage detection
    damage_result = detect_damage(vehicle_image_path)

    # Fraud detection
    fraud_data = {
        "Month": "Dec",
        "WeekOfMonth": 1,
        "DayOfWeek": "Monday",
        "Make": "Honda",
        "AccidentArea": "Urban",
        "DayOfWeekClaimed": "Monday",
        "MonthClaimed": "Dec",
        "WeekOfMonthClaimed": 1,
        "Sex": "Male",
        "MaritalStatus": "Single",
        "Age": 30,
        "Fault": "Policy Holder",
        "PolicyType": "Sedan - Collision",
        "VehicleCategory": "Sport",
        "VehiclePrice": "20000 to 29000",
        "RepNumber": 10,
        "Deductible": 400,
        "DriverRating": 1,
        "Days_Policy_Accident": "more than 30",
        "Days_Policy_Claim": "more than 30",
        "PastNumberOfClaims": "none",
        "AgeOfVehicle": "3 years",
        "AgeOfPolicyHolder": "31 to 35",
        "PoliceReportFiled": "Yes",
        "WitnessPresent": "No",
        "AgentType": "External",
        "NumberOfSuppliments": "none",
        "AddressChange_Claim": "1 year",
        "NumberOfCars": "1 vehicle",
        "Year": 1994,
        "BasePolicy": "Collision"
    }

    fraud_result = predict_fraud(fraud_data)

    # Priority
    damage_types = [
        item["damage_type"]
        for item in damage_result["damages"]
    ]

    priority = calculate_priority(
        damage_result["damage_count"],
        fraud_result["fraud_probability"],
        damage_types
    )

    # Update existing claim
    claim.ocr_text = ocr_result["raw_text"]

    # Validate that the uploaded document belongs
    # to the same policy as the existing claim.
    ocr_policy_number = (
        ocr_result["extracted_fields"]["policy_number"]
    )

    if (
        ocr_policy_number
        and ocr_policy_number != claim.policy_number
    ):
        return {
            "error": (
                f"Policy number mismatch. "
                f"Claim belongs to {claim.policy_number}, "
                f"but the uploaded document contains "
                f"{ocr_policy_number}."
            )
        }

    claim.extracted_vehicle_number = (
        ocr_result["extracted_fields"]["vehicle_number"]
    )

    claim.damage_type = (
        ", ".join(damage_types)
        if damage_types
        else None
    )

    claim.damage_count = (
        damage_result["damage_count"]
    )

    claim.fraud_probability = (
        fraud_result["fraud_probability"]
    )

    claim.fraud_prediction = (
        fraud_result["fraud_prediction"]
    )

    claim.priority = priority
    claim.status = "Pending"

    db.commit()
    db.refresh(claim)

    return {
        "claim_id": claim.id,
        "claim_number": f"CLM-2026-{claim.id:05d}",
        "ocr": ocr_result,
        "damage_detection": damage_result,
        "fraud_detection": fraud_result,
        "priority": priority,
        "status": claim.status,
        "database_updated": True
    }