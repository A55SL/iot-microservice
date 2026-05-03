from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas, logic
from app.database import get_db

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.post("/readings", response_model=schemas.SensorReadingWithAlert, status_code=201)
def create_reading(payload: schemas.SensorReadingCreate, db: Session = Depends(get_db)):
    """Receive a sensor reading, check thresholds, save and return result."""
    reading = models.SensorReading(**payload.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)

    alert = logic.evaluate_reading(db, reading)

    return schemas.SensorReadingWithAlert(
        **schemas.SensorReadingResponse.model_validate(reading).model_dump(),
        alert=schemas.AlertResponse.model_validate(alert) if alert else None,
    )


@router.get("/readings", response_model=list[schemas.SensorReadingResponse])
def get_readings(db: Session = Depends(get_db)):
    """Return all sensor readings."""
    return db.query(models.SensorReading).order_by(models.SensorReading.timestamp.desc()).all()


@router.post("/threshold", response_model=schemas.ThresholdConfigResponse, status_code=201)
def set_threshold(payload: schemas.ThresholdConfigCreate, db: Session = Depends(get_db)):
    """Create or update threshold config for a device."""
    config = (
        db.query(models.ThresholdConfig)
        .filter(models.ThresholdConfig.device_id == payload.device_id)
        .first()
    )
    if config:
        config.warning_threshold = payload.warning_threshold
        config.critical_threshold = payload.critical_threshold
    else:
        config = models.ThresholdConfig(**payload.model_dump())
        db.add(config)

    db.commit()
    db.refresh(config)
    return config