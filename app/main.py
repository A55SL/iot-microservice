from fastapi import FastAPI
from app.database import engine, Base
from app.routers import sensors, alerts

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Predictive Maintenance API",
    description="IoT sensor monitoring and anomaly detection — Intelligent IoT Solutions A/S",
    version="1.0.0",
)

app.include_router(sensors.router)
app.include_router(alerts.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Predictive Maintenance API"}