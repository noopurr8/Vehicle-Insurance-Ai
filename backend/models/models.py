from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(150))
    phone = Column(String(20))


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    vehicle_number = Column(String(30))
    vehicle_type = Column(String(50))
    policy_number = Column(String(100))


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)

    # Customer details
    name = Column(String(100))
    email = Column(String(150))
    phone_number = Column(String(20))
    address = Column(Text)

    # Vehicle details
    make = Column(String(100))
    model = Column(String(100))
    year = Column(Integer)
    mileage = Column(Integer)
    vin = Column(String(100))

    # Requested coverage
    coverage_type = Column(String(50))
    rent_a_car = Column(Integer, default=0)

    # Selected/issued policy
    selected_policy_id = Column(Integer, nullable=True)
    policy_number = Column(String(100), nullable=True)

    status = Column(String(50), default="Draft")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150))
    coverage_type = Column(String(50))
    description = Column(Text)
    premium = Column(Float)
    features = Column(Text)

    active = Column(Integer, default=1)


class ApplicationPolicy(Base):
    __tablename__ = "application_policies"

    id = Column(Integer, primary_key=True, index=True)

    application_id = Column(
        Integer,
        ForeignKey("applications.id")
    )

    policy_id = Column(
        Integer,
        ForeignKey("policies.id")
    )

    selected = Column(Integer, default=0)


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))

    claim_description = Column(Text)

    # OCR
    ocr_text = Column(Text)
    policy_number = Column(String(100))
    extracted_vehicle_number = Column(String(30))

    # YOLO
    damage_type = Column(String(100))
    damage_count = Column(Integer, default=0)

    # Fraud model
    fraud_probability = Column(Float)
    fraud_prediction = Column(Integer)

    # Claim decision
    priority = Column(String(30))
    status = Column(String(50), default="Pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())