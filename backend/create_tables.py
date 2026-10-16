from backend.database import Base, engine
from backend.models.models import (
    Customer,
    Vehicle,
    Application,
    Policy,
    ApplicationPolicy,
    Claim,
)

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!") 