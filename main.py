from fastapi import FastAPI
from backend.routes.claim_routes import router as claim_router
from backend.routes.application_routes import router as application_router

app = FastAPI(
    title="AI Vehicle Insurance Platform",
    description="AI-powered vehicle insurance application and claims platform",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "AI Vehicle Insurance Platform API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


app.include_router(claim_router)
app.include_router(application_router)