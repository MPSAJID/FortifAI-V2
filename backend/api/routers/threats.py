"""Threats Router"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
import uuid
import httpx

from backend.api.core.database import get_db
from backend.api.core.security import get_current_user
from backend.api.core.config import settings
from backend.api.models.threat import ThreatLog
from backend.api.schemas.threat import ThreatLogCreate, ThreatLogResponse, ThreatAnalysisRequest, ThreatAnalysisResponse

router = APIRouter()

@router.get("/", response_model=List[ThreatLogResponse])
async def get_threats(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    threat_type: Optional[str] = None,
    classification: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all detected threats"""
    query = select(ThreatLog).order_by(desc(ThreatLog.detected_at))
    
    if threat_type:
        query = query.where(ThreatLog.threat_type == threat_type)
    if classification:
        query = query.where(ThreatLog.classification == classification)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.scalars().all()

@router.post("/", response_model=ThreatLogResponse)
async def log_threat(
    threat_data: ThreatLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Log a new threat detection"""
    threat_id = f"THREAT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    db_threat = ThreatLog(
        threat_id=threat_id,
        threat_type=threat_data.threat_type,
        source_ip=threat_data.source_ip,
        destination_ip=threat_data.destination_ip,
        process_name=threat_data.process_name,
        file_path=threat_data.file_path,
        user=threat_data.user,
        raw_log=threat_data.raw_log,
        metadata=threat_data.metadata
    )
    
    db.add(db_threat)
    await db.commit()
    await db.refresh(db_threat)
    
    return db_threat

@router.post("/analyze", response_model=ThreatAnalysisResponse)
async def analyze_threat(
    request: ThreatAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze log data for threats using ML Engine"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ML_ENGINE_URL}/analyze",
                json=request.log_data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        # Fallback response if ML engine is unavailable
        return ThreatAnalysisResponse(
            threat_type="unknown",
            confidence=0.0,
            risk_score=0.0,
            classification="pending",
            recommendations=["ML Engine unavailable - manual review required"]
        )

@router.get("/stats/summary")
async def get_threat_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get threat statistics summary"""
    result = await db.execute(select(ThreatLog))
    threats = result.scalars().all()
    
    stats = {
        "total": len(threats),
        "by_type": {},
        "by_classification": {},
        "avg_risk_score": 0.0,
        "high_risk_count": 0
    }
    
    total_risk = 0
    for threat in threats:
        stats["by_type"][threat.threat_type] = stats["by_type"].get(threat.threat_type, 0) + 1
        if threat.classification:
            stats["by_classification"][threat.classification] = stats["by_classification"].get(threat.classification, 0) + 1
        total_risk += threat.risk_score
        if threat.risk_score >= 0.7:
            stats["high_risk_count"] += 1
    
    if threats:
        stats["avg_risk_score"] = round(total_risk / len(threats), 2)
    
    return stats
