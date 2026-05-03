from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import require_api_key

router = APIRouter(
    prefix="/api/alerts",
    tags=["Alerts"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=list[schemas.AlertResponse])
def get_alerts(turbine_id: str = None, severity: str = None, db: Session = Depends(get_db)):
    """Return alerts, optionally filtered by turbine_id or severity."""
    query = db.query(models.Alert).order_by(models.Alert.timestamp.desc())
    if turbine_id:
        query = query.filter(models.Alert.turbine_id == turbine_id)
    if severity:
        query = query.filter(models.Alert.severity == severity.upper())
    return query.limit(100).all()


@router.get("/{alert_id}", response_model=schemas.AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Return a single alert by ID."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert