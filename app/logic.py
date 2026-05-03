import logging
from sqlalchemy.orm import Session
from app import models

logger = logging.getLogger("predictive_maintenance")

# Default thresholds for Vestas V90-2MW
DEFAULTS = {
    "generator_temp_max": 80.0,
    "gearbox_temp_max": 70.0,
    "main_bearing_temp_max": 60.0,
    "vibration_max_mm_s": 4.5,
    "oil_pressure_min": 3.0,
}


def get_model_from_id(turbine_id: str) -> str:
    """Extract model name from turbine ID. E.g. 'VES-V90-001' → 'VES-V90'"""
    parts = turbine_id.rsplit("-", 1)
    return parts[0] if len(parts) > 1 else turbine_id


def get_thresholds(db: Session, turbine_id: str) -> dict:
    """Look up model-specific thresholds, or fall back to defaults."""
    model = get_model_from_id(turbine_id)
    config = (
        db.query(models.ModelThreshold)
        .filter(models.ModelThreshold.turbine_model == model)
        .first()
    )
    if config:
        return {
            "generator_temp_max": config.generator_temp_max,
            "gearbox_temp_max": config.gearbox_temp_max,
            "main_bearing_temp_max": config.main_bearing_temp_max,
            "vibration_max_mm_s": config.vibration_max_mm_s,
            "oil_pressure_min": config.oil_pressure_min,
        }
    return DEFAULTS.copy()


def evaluate_reading(db: Session, reading: models.TurbineReading) -> list[models.Alert]:
    """
    Core domain logic: check all sensor values against model-specific thresholds.
    Returns a list of alerts (could be multiple per reading).
    """
    thresholds = get_thresholds(db, reading.turbine_id)
    alerts = []

    checks = [
        ("generator_temp_c", reading.generator_temp_c, thresholds["generator_temp_max"], "above"),
        ("gearbox_temp_c", reading.gearbox_temp_c, thresholds["gearbox_temp_max"], "above"),
        ("main_bearing_temp_c", reading.main_bearing_temp_c, thresholds["main_bearing_temp_max"], "above"),
        ("main_bearing_vibration_mm_s", reading.main_bearing_vibration_mm_s, thresholds["vibration_max_mm_s"], "above"),
        ("oil_pressure_bar", reading.oil_pressure_bar, thresholds["oil_pressure_min"], "below"),
    ]

    for param, value, limit, direction in checks:
        breached = value > limit if direction == "above" else value < limit
        if breached:
            severity = "CRITICAL" if direction == "above" and value > limit * 1.15 else "WARNING"
            if direction == "below" and value < limit * 0.7:
                severity = "CRITICAL"

            message = (
                f"{severity}: Turbine '{reading.turbine_id}' — "
                f"{param} = {value:.1f} {'exceeds' if direction == 'above' else 'below'} "
                f"limit {limit:.1f}"
            )

            alert = models.Alert(
                reading_id=reading.id,
                turbine_id=reading.turbine_id,
                parameter=param,
                value=value,
                threshold=limit,
                severity=severity,
                message=message,
            )
            db.add(alert)
            alerts.append(alert)

            # Simulate technician notification
            logger.warning(f"🚨 TECHNICIAN NOTIFIED — {message}")

    if alerts:
        db.commit()
        for a in alerts:
            db.refresh(a)

    return alerts