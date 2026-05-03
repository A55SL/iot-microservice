from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TurbineDataIn(BaseModel):
    turbine_id: str
    timestamp: datetime
    wind_speed_m_s: float
    rotor_rpm: float
    power_output_kw: float
    blade_pitch_deg: float
    nacelle_yaw_deg: float
    generator_temp_c: float
    gearbox_temp_c: float
    main_bearing_temp_c: float
    nacelle_temp_c: float
    ambient_temp_c: float
    main_bearing_vibration_mm_s: float
    tower_vibration_mm_s: float
    oil_pressure_bar: float
    grid_frequency_hz: float
    fault_injected: Optional[str] = None


class TurbineDataOut(BaseModel):
    id: int
    turbine_id: str
    timestamp: datetime
    wind_speed_m_s: float
    power_output_kw: float
    generator_temp_c: float
    gearbox_temp_c: float
    main_bearing_vibration_mm_s: float
    oil_pressure_bar: float
    received_at: datetime

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    id: int
    reading_id: int
    turbine_id: str
    parameter: str
    value: float
    threshold: float
    severity: str
    message: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ModelThresholdIn(BaseModel):
    turbine_model: str
    generator_temp_max: float = 80.0
    gearbox_temp_max: float = 70.0
    main_bearing_temp_max: float = 60.0
    vibration_max_mm_s: float = 4.5
    oil_pressure_min: float = 3.0
    service_interval_hours: float = 4000.0


class ModelThresholdOut(ModelThresholdIn):
    id: int

    model_config = {"from_attributes": True}


class TurbineStatusOut(BaseModel):
    turbine_id: str
    operating_hours: float
    last_service_hours: float
    hours_since_service: float
    service_interval_hours: float
    service_due: bool

    model_config = {"from_attributes": True}
