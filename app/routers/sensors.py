from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas, logic
from app.database import get_db
from app.auth import require_api_key

router = APIRouter(
    prefix="/api/turbines",
    tags=["Turbines"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/data", status_code=201)
def receive_turbine_data(payload: schemas.TurbineDataIn, db: Session = Depends(get_db)):
    """Receive telemetry from a wind turbine, store it, and evaluate thresholds."""
    reading = models.TurbineReading(**payload.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)

    alerts = logic.evaluate_reading(db, reading)

    return {
        "status": "received",
        "reading_id": reading.id,
        "alerts_triggered": len(alerts),
    }


@router.get("/readings", response_model=list[schemas.TurbineDataOut])
def get_readings(turbine_id: str = None, db: Session = Depends(get_db)):
    """Return stored readings, optionally filtered by turbine_id."""
    query = db.query(models.TurbineReading).order_by(models.TurbineReading.timestamp.desc())
    if turbine_id:
        query = query.filter(models.TurbineReading.turbine_id == turbine_id)
    return query.limit(100).all()


@router.post("/thresholds", response_model=schemas.ModelThresholdOut, status_code=201)
def set_model_threshold(payload: schemas.ModelThresholdIn, db: Session = Depends(get_db)):
    """Set thresholds for a specific turbine model."""
    config = (
        db.query(models.ModelThreshold)
        .filter(models.ModelThreshold.turbine_model == payload.turbine_model)
        .first()
    )
    if config:
        for key, val in payload.model_dump().items():
            setattr(config, key, val)
    else:
        config = models.ModelThreshold(**payload.model_dump())
        db.add(config)

    db.commit()
    db.refresh(config)
    return config