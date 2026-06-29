from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class FieldCreate(BaseModel):
    lat: float = Field(..., description="위도 WGS84")
    lng: float = Field(..., description="경도 WGS84")
    crop_name: str = "고추"
    crop_code: str = "pepper"
    planting_date: Optional[date] = None
    user_id: int = 1


class FieldResponse(BaseModel):
    field_id: int
    fmap_innb: str
    pnu_code: Optional[str]
    crop_name: str
    land_type: Optional[str]
    address: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    planting_date: Optional[date]

    class Config:
        from_attributes = True


class RiskSummary(BaseModel):
    pest_name: str
    final_risk: float
    risk_level: str
    weather_risk: float
    pest_risk: float
    soil_risk: float


class DashboardResponse(BaseModel):
    field: FieldResponse
    today_risks: list[RiskSummary]
    top_pests: list[RiskSummary]
    trend_7d: list[dict]
    alerts: list[dict]
    recommendation: Optional[dict]


class AlertSettingsUpdate(BaseModel):
    risk_rise: bool = True
    rain_before_spray: bool = True
    high_humidity: bool = True
    nearby_pest: bool = True
    weekly_report: bool = True


class ApiStatusItem(BaseModel):
    source_name: str
    last_called_at: Optional[str]
    last_status: str
    license_type: Optional[str]
