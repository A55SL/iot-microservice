from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class TurbineReading(Base):
    __tablename__ = "turbine_readings"

    id = Column(Integer, primary_key=True, index=True)
    turbine_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    wind_speed_m_s = Column(Float)
    rotor_rpm = Column(Float)
    power_output_kw = Column(Float)
    blade_pitch_deg = Column(Float)
    nacelle_yaw_deg = Column(Float)
    generator_temp_c = Column(Float)
    gearbox_temp_c = Column(Float)
    main_bearing_temp_c = Column(Float)
    nacelle_temp_c = Column(Float)
    ambient_temp_c = Column(Float)
    main_bearing_vibration_mm_s = Column(Float)
    tower_vibration_mm_s = Column(Float)
    oil_pressure_bar = Column(Float)
    grid_frequency_hz = Column(Float)
    fault_injected = Column(String(100), nullable=True)
    received_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    alerts = relationship("Alert", back_populates="reading")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    reading_id = Column(Integer, ForeignKey("turbine_readings.id"), nullable=False)
    turbine_id = Column(String(100), nullable=False)
    parameter = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(50), nullable=False)
    message = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    reading = relationship("TurbineReading", back_populates="alerts")


class ModelThreshold(Base):
    __tablename__ = "model_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    turbine_model = Column(String(100), nullable=False, unique=True)
    generator_temp_max = Column(Float, default=80.0)
    gearbox_temp_max = Column(Float, default=70.0)
    main_bearing_temp_max = Column(Float, default=60.0)
    vibration_max_mm_s = Column(Float, default=4.5)
    oil_pressure_min = Column(Float, default=3.0)
