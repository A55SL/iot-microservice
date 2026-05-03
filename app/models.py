from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(50), default="celsius")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    alerts = relationship("Alert", back_populates="reading")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    reading_id = Column(Integer, ForeignKey("sensor_readings.id"), nullable=False)
    message = Column(String(500), nullable=False)
    severity = Column(String(50), default="WARNING")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    reading = relationship("SensorReading", back_populates="alerts")


class ThresholdConfig(Base):
    __tablename__ = "threshold_configs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=False, unique=True)
    warning_threshold = Column(Float, default=75.0)
    critical_threshold = Column(Float, default=90.0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))