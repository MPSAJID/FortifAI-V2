"""Threat Schemas"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ThreatLogBase(BaseModel):
    threat_type: str
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    process_name: Optional[str] = None
    file_path: Optional[str] = None
    user: Optional[str] = None

class ThreatLogCreate(ThreatLogBase):
    raw_log: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}

class ThreatLogResponse(ThreatLogBase):
    id: int
    threat_id: str
    confidence: float
    classification: Optional[str] = None
    risk_score: float
    detected_at: datetime
    
    class Config:
        from_attributes = True

class ThreatAnalysisRequest(BaseModel):
    log_data: Dict[str, Any]
    
class ThreatAnalysisResponse(BaseModel):
    threat_type: str
    confidence: float
    risk_score: float
    classification: str
    recommendations: list
