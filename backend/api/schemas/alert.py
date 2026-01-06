"""Alert Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AlertBase(BaseModel):
    title: str
    message: Optional[str] = None
    severity: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default={}, alias="alert_metadata")

class AlertCreate(BaseModel):
    title: str
    message: Optional[str] = None
    severity: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    acknowledged: Optional[bool] = None
    resolved: Optional[bool] = None

class AlertResponse(BaseModel):
    id: int
    alert_id: str
    title: str
    message: Optional[str] = None
    severity: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default={}, validation_alias="alert_metadata")
    status: str
    acknowledged: bool
    resolved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True
