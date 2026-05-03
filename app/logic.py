from sqlalchemy.orm import Session
from app import models

DEFAULT_WARNING_THRESHOLD = 75.0
DEFAULT_CRITICAL_THRESHOLD = 90.0


def get_thresholds(db: Session, device_id: str) -> tuple[float, float]:
    """Look up device-specific thresholds, or use defaults."""
    config = (
        db.query(models.ThresholdConfig)
        .filter(models.ThresholdConfig.device_id == device_id)
        .first()
    )
    if config:
        return config.warning_threshold, config.critical_threshold
    return DEFAULT_WARNING_THRESHOLD, DEFAULT_CRITICAL_THRESHOLD


def evaluate_reading(db: Session, reading: models.SensorReading) -> models.Alert | None:
    """
    Core domain logic:
    Sensor Value Received → Threshold Check → Alert (if breached)
    """
    warning_threshold, critical_threshold = get_thresholds(db, reading.device_id)

    if reading.value >= critical_threshold:
        severity = "CRITICAL"
        message = (
            f"CRITICAL: Device '{reading.device_id}' reported {reading.value} {reading.unit}, "
            f"exceeding critical threshold of {critical_threshold} {reading.unit}."
        )
    elif reading.value >= warning_threshold:
        severity = "WARNING"
        message = (
            f"WARNING: Device '{reading.device_id}' reported {reading.value} {reading.unit}, "
            f"exceeding warning threshold of {warning_threshold} {reading.unit}."
        )
    else:
        return None

    alert = models.Alert(
        reading_id=reading.id,
        message=message,
        severity=severity,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert