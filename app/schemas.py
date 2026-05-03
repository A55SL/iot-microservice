from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SensorReadingCreate(BaseModel):
    device_id: str
    value: float
    unit: str = "celsius"


class SensorReadingResponse(BaseModel):
    id: int
    device_id: str
    value: float
    unit: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    id: int
    reading_id: int
    message: str
    severity: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class SensorReadingWithAlert(SensorReadingResponse):
    alert: Optional[AlertResponse] = None


class ThresholdConfigCreate(BaseModel):
    device_id: str
    warning_threshold: float = Field(default=75.0, ge=0)
    critical_threshold: float = Field(default=90.0, ge=0)


class ThresholdConfigResponse(ThresholdConfigCreate):
    id: int
    updated_at: datetime

    model_config = {"from_attributes": True}