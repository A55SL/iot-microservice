import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app import models

logger = logging.getLogger("predictive_maintenance")

DEFAULTS = {
    "generator_temp_max": 80.0,
    "gearbox_temp_max": 70.0,
    "main_bearing_temp_max": 60.0,
    "vibration_max_mm_s": 4.5,
    "oil_pressure_min": 3.0,
    "service_interval_hours": 4000.0,
}


def get_model_from_id(turbine_id: str) -> str:
    """Extract model name from turbine ID. E.g. 'VES-V90-001' -> 'VES-V90'"""
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
            "service_interval_hours": config.service_interval_hours,
        }
    return DEFAULTS.copy()


def update_operating_hours(db: Session, reading: models.TurbineReading) -> models.TurbineStatus:
    """Track cumulative operating hours like an odometer."""
    status = (
        db.query(models.TurbineStatus)
        .filter(models.TurbineStatus.turbine_id == reading.turbine_id)
        .first()
    )

    if not status:
        status = models.TurbineStatus(
            turbine_id=reading.turbine_id,
            operating_hours=0.0,
            last_service_hours=0.0,
            last_reading_time=reading.timestamp,
        )
        db.add(status)
        db.commit()
        db.refresh(status)
        return status

    if status.last_reading_time and reading.power_output_kw > 0:
        time_diff = (reading.timestamp - status.last_reading_time).total_seconds()
        if 0 < time_diff < 3600:  # ignore gaps longer than 1 hour
            hours = time_diff / 3600.0
            status.operating_hours += hours

    status.last_reading_time = reading.timestamp
    status.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(status)
    return status


def check_maintenance_due(
    db: Session,
    reading: models.TurbineReading,
    status: models.TurbineStatus,
    thresholds: dict,
) -> models.Alert | None:
    """Check if the turbine is due for scheduled maintenance based on operating hours."""
    hours_since_service = status.operating_hours - status.last_service_hours
    interval = thresholds["service_interval_hours"]

    if hours_since_service >= interval:
        severity = "CRITICAL" if hours_since_service >= interval * 1.2 else "WARNING"
        message = (
            f"{severity}: Turbine '{reading.turbine_id}' — "
            f"{hours_since_service:.0f} operating hours since last service, "
            f"service interval is {interval:.0f} hours"
        )
        alert = models.Alert(
            reading_id=reading.id,
            turbine_id=reading.turbine_id,
            parameter="operating_hours",
            value=round(hours_since_service, 1),
            threshold=interval,
            severity=severity,
            message=message,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        logger.warning(f"🔧 MAINTENANCE DUE — {message}")
        return alert

    return None


def evaluate_reading(db: Session, reading: models.TurbineReading) -> list[models.Alert]:
    """
    Core domain logic: check all sensor values against model-specific thresholds
    and track operating hours for scheduled maintenance.
    """
    thresholds = get_thresholds(db, reading.turbine_id)
    alerts = []

    # --- Anomaly checks ---
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

            logger.warning(f"🚨 TECHNICIAN NOTIFIED — {message}")

    if alerts:
        db.commit()
        for a in alerts:
            db.refresh(a)

    # --- Operating hours & maintenance check ---
    status = update_operating_hours(db, reading)
    maintenance_alert = check_maintenance_due(db, reading, status, thresholds)
    if maintenance_alert:
        alerts.append(maintenance_alert)

    return alerts
