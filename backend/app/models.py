from datetime import datetime

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    name = Column(String(100))
    phone = Column(String(20))
    region = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    fields = relationship("FieldMaster", back_populates="user")


class SourceMaster(Base):
    __tablename__ = "source_master"
    source_id = Column(Integer, primary_key=True)
    source_name = Column(String(200))
    license_type = Column(String(50))
    commercial_allowed = Column(Boolean, default=True)
    rate_limit_per_day = Column(Integer, default=10000)
    last_called_at = Column(DateTime(timezone=True))
    last_status = Column(String(20))


class FieldMaster(Base):
    __tablename__ = "field_master"
    field_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    fmap_innb = Column(String(50), nullable=False)
    pnu_code = Column(String(30))
    crop_code = Column(String(20), default="pepper")
    crop_name = Column(String(50), default="고추")
    land_type = Column(String(20))
    lat = Column(Float)
    lng = Column(Float)
    position_x = Column(Float)
    position_y = Column(Float)
    kma_nx = Column(Integer)
    kma_ny = Column(Integer)
    address = Column(Text)
    planting_date = Column(Date)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    user = relationship("User", back_populates="fields")


class RawApiLog(Base):
    __tablename__ = "raw_api_log"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("source_master.source_id"))
    field_id = Column(Integer, ForeignKey("field_master.field_id"))
    endpoint = Column(Text)
    request_params = Column(JSON)
    response_body = Column(JSON)
    status_code = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class WeatherHourly(Base):
    __tablename__ = "weather_hourly"
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("field_master.field_id", ondelete="CASCADE"))
    obs_time = Column(DateTime(timezone=True), nullable=False)
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall = Column(Float)
    wind_speed = Column(Float)
    soil_moisture = Column(Float)
    dew_time = Column(Float)
    source = Column(String(50), default="farmmap")


class SoilSnapshot(Base):
    __tablename__ = "soil_snapshot"
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("field_master.field_id", ondelete="CASCADE"))
    sample_year = Column(Integer)
    acidity = Column(Float)
    organic_matter = Column(Float)
    available_phosphate = Column(Float)
    ec = Column(Float)
    potassium = Column(Float)
    magnesium = Column(Float)
    lime_requirement = Column(Float)
    source = Column(String(50), default="farmmap")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class PestOccurrence(Base):
    __tablename__ = "pest_occurrence"
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("field_master.field_id", ondelete="CASCADE"))
    pest_name = Column(String(100))
    crop_name = Column(String(50))
    occurrence_value = Column(Float)
    occurrence_distance = Column(Float)
    report_date = Column(Date)
    source = Column(String(50), default="farmmap")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class FeatureDaily(Base):
    __tablename__ = "feature_daily"
    __table_args__ = (UniqueConstraint("field_id", "date"),)
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("field_master.field_id", ondelete="CASCADE"))
    date = Column(Date, nullable=False)
    rain_6h = Column(Float)
    humidity_24h = Column(Float)
    dew_time_24h = Column(Float)
    temp_min = Column(Float)
    temp_max = Column(Float)
    soil_moisture_avg = Column(Float)
    soil_risk_index = Column(Float)
    pest_prior_score = Column(Float)


class RiskScoreDaily(Base):
    __tablename__ = "risk_score_daily"
    __table_args__ = (UniqueConstraint("field_id", "date", "pest_name"),)
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("field_master.field_id", ondelete="CASCADE"))
    date = Column(Date, nullable=False)
    pest_name = Column(String(100), nullable=False)
    weather_risk = Column(Float)
    pest_risk = Column(Float)
    soil_risk = Column(Float)
    crop_stage_risk = Column(Float, default=0)
    final_risk = Column(Float)
    risk_level = Column(String(20))
    model_version = Column(String(20), default="v1.0")


class RecommendationCard(Base):
    __tablename__ = "recommendation_card"
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("field_master.field_id", ondelete="CASCADE"))
    pest_name = Column(String(100))
    risk_score = Column(Float)
    title = Column(Text)
    reason = Column(Text)
    action_list = Column(JSON)
    source_refs = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AlertEvent(Base):
    __tablename__ = "alert_event"
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey("field_master.field_id", ondelete="CASCADE"))
    alert_type = Column(String(50))
    title = Column(Text)
    message = Column(Text)
    status = Column(String(20), default="pending")
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AlertSettings(Base):
    __tablename__ = "alert_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    risk_rise = Column(Boolean, default=True)
    rain_before_spray = Column(Boolean, default=True)
    high_humidity = Column(Boolean, default=True)
    nearby_pest = Column(Boolean, default=True)
    weekly_report = Column(Boolean, default=True)
