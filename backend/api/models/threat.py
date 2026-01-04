"""Threat Log Model"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text
from sqlalchemy.sql import func
from core.database import Base

class ThreatLog(Base):
    __tablename__ = "threat_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    threat_id = Column(String(50), unique=True, index=True)
    threat_type = Column(String(50), nullable=False)
    confidence = Column(Float, default=0.0)
    source_ip = Column(String(45))
    destination_ip = Column(String(45))
    process_name = Column(String(255))
    file_path = Column(Text)
    user = Column(String(100))
    raw_log = Column(JSON)
    classification = Column(String(50))  # malware, ransomware, ddos, etc.
    risk_score = Column(Float, default=0.0)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    threat_metadata = Column("metadata", JSON, default={})
