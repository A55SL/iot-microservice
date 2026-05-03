from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth import require_api_key

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=list[schemas.AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    """Return all triggered alerts."""
    return db.query(models.Alert).order_by(models.Alert.timestamp.desc()).all()


@router.get("/{alert_id}", response_model=schemas.AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Return a single alert by ID."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert