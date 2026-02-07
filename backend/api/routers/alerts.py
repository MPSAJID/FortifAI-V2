"""Alerts Router"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
import uuid
import os
import httpx

from backend.api.core.database import get_db
from backend.api.core.security import get_current_user
from backend.api.models.alert import Alert
from backend.api.schemas.alert import AlertCreate, AlertResponse, AlertUpdate

router = APIRouter()

# Internal service API key for service-to-service communication
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "fortifai-internal-service-key")


async def verify_internal_service(x_internal_key: Optional[str] = Header(None, alias="X-Internal-Key")):
    """Verify internal service API key"""
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid internal service key")
    return True


async def notify_critical_alert(alert_title: str, alert_message: str, severity: str, source: str):
    """Send email notification for critical alerts"""
    if severity.upper() != "CRITICAL":
        return  # Only notify for critical alerts
    
    alert_service_url = os.getenv("ALERT_SERVICE_URL", "http://alert-service:5001")
    
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "title": alert_title,
                "message": alert_message,
                "severity": severity,
                "source": source,
                "metadata": {}
            }
            await client.post(
                f"{alert_service_url}/api/notify",
                json=payload,
                timeout=10.0
            )
    except Exception as e:
        # Log but don't fail the alert creation if notification fails
        print(f"Failed to send alert notification: {e}")

@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all alerts with optional filtering"""
    query = select(Alert).order_by(desc(Alert.created_at))
    
    if severity:
        query = query.where(Alert.severity == severity.upper())
    if status:
        query = query.where(Alert.status == status)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    
    return result.scalars().all()

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new alert"""
    alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    db_alert = Alert(
        alert_id=alert_id,
        title=alert_data.title,
        message=alert_data.message,
        severity=alert_data.severity.upper(),
        source=alert_data.source,
        alert_metadata=alert_data.metadata or {}
    )
    
    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)
    
    # Send email notification if critical
    await notify_critical_alert(alert_data.title, alert_data.message, alert_data.severity, alert_data.source)
    
    return db_alert


@router.post("/internal", response_model=AlertResponse)
async def create_alert_internal(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_internal_service)
):
    """Create a new alert from internal services (no user auth required)"""
    alert_id = f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    db_alert = Alert(
        alert_id=alert_id,
        title=alert_data.title,
        message=alert_data.message,
        severity=alert_data.severity.upper(),
        source=alert_data.source,
        alert_metadata=alert_data.metadata or {}
    )
    
    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)
    
    # Send email notification if critical
    await notify_critical_alert(alert_data.title, alert_data.message, alert_data.severity, alert_data.source)
    
    return db_alert


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific alert by ID"""
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return alert

@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_update: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an alert status"""
    result = await db.execute(
        select(Alert).where(Alert.alert_id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if alert_update.status:
        alert.status = alert_update.status
    if alert_update.acknowledged is not None:
        alert.acknowledged = alert_update.acknowledged
    if alert_update.resolved is not None:
        alert.resolved = alert_update.resolved
        if alert_update.resolved:
            alert.resolved_at = datetime.now()
            alert.status = "resolved"
    
    await db.commit()
    await db.refresh(alert)
    
    return alert

@router.get("/stats/summary")
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alert statistics summary"""
    result = await db.execute(select(Alert))
    alerts = result.scalars().all()
    
    stats = {
        "total": len(alerts),
        "by_severity": {},
        "by_status": {},
        "unresolved": 0
    }
    
    for alert in alerts:
        stats["by_severity"][alert.severity] = stats["by_severity"].get(alert.severity, 0) + 1
        stats["by_status"][alert.status] = stats["by_status"].get(alert.status, 0) + 1
        if not alert.resolved:
            stats["unresolved"] += 1
    
    return stats
