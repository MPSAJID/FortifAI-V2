"""Analytics Router"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timedelta

from backend.api.core.database import get_db
from backend.api.core.security import get_current_user
from backend.api.models.alert import Alert
from backend.api.models.threat import ThreatLog

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard statistics"""
    # Get counts
    alerts_result = await db.execute(select(func.count(Alert.id)))
    threats_result = await db.execute(select(func.count(ThreatLog.id)))
    
    # Get recent activity
    recent_alerts = await db.execute(
        select(Alert).order_by(Alert.created_at.desc()).limit(5)
    )
    recent_threats = await db.execute(
        select(ThreatLog).order_by(ThreatLog.detected_at.desc()).limit(5)
    )
    
    return {
        "summary": {
            "total_alerts": alerts_result.scalar() or 0,
            "total_threats": threats_result.scalar() or 0,
            "system_health": "operational"
        },
        "recent_alerts": [
            {"id": a.alert_id, "title": a.title, "severity": a.severity}
            for a in recent_alerts.scalars()
        ],
        "recent_threats": [
            {"id": t.threat_id, "type": t.threat_type, "risk": t.risk_score}
            for t in recent_threats.scalars()
        ]
    }

@router.get("/timeline")
async def get_timeline(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get activity timeline for the specified days"""
    start_date = datetime.now() - timedelta(days=days)
    
    alerts_result = await db.execute(
        select(Alert).where(Alert.created_at >= start_date)
    )
    threats_result = await db.execute(
        select(ThreatLog).where(ThreatLog.detected_at >= start_date)
    )
    
    # Group by date
    timeline = {}
    for alert in alerts_result.scalars():
        date_key = alert.created_at.strftime("%Y-%m-%d")
        if date_key not in timeline:
            timeline[date_key] = {"alerts": 0, "threats": 0}
        timeline[date_key]["alerts"] += 1
    
    for threat in threats_result.scalars():
        date_key = threat.detected_at.strftime("%Y-%m-%d")
        if date_key not in timeline:
            timeline[date_key] = {"alerts": 0, "threats": 0}
        timeline[date_key]["threats"] += 1
    
    return {"days": days, "timeline": timeline}

@router.get("/risk-assessment")
async def get_risk_assessment(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get overall risk assessment"""
    # Get unresolved critical alerts
    critical_alerts = await db.execute(
        select(Alert).where(
            Alert.resolved == False,
            Alert.severity.in_(["CRITICAL", "HIGH"])
        )
    )
    critical_count = len(list(critical_alerts.scalars()))
    
    # Get high-risk threats
    high_risk_threats = await db.execute(
        select(ThreatLog).where(ThreatLog.risk_score >= 0.7)
    )
    high_risk_count = len(list(high_risk_threats.scalars()))
    
    # Calculate overall risk level
    if critical_count >= 5 or high_risk_count >= 10:
        risk_level = "CRITICAL"
        overall_risk_score = 0.95
    elif critical_count >= 2 or high_risk_count >= 5:
        risk_level = "HIGH"
        overall_risk_score = 0.75
    elif critical_count >= 1 or high_risk_count >= 2:
        risk_level = "MEDIUM"
        overall_risk_score = 0.50
    else:
        risk_level = "LOW"
        overall_risk_score = 0.25
    
    # Get counts by severity
    severity_counts = await db.execute(
        select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)
    )
    severity_data = {row[0]: row[1] for row in severity_counts}
    
    return {
        "risk_level": risk_level,
        "overall_risk_score": overall_risk_score,
        "critical_count": severity_data.get("CRITICAL", 0),
        "high_count": severity_data.get("HIGH", 0),
        "medium_count": severity_data.get("MEDIUM", 0),
        "low_count": severity_data.get("LOW", 0),
        "critical_alerts": critical_count,
        "high_risk_threats": high_risk_count,
        "recommendations": [
            "Review unresolved critical alerts immediately",
            "Investigate high-risk threat detections",
            "Update security policies based on recent threats",
            "Consider implementing additional monitoring"
        ] if risk_level in ["CRITICAL", "HIGH"] else [
            "Continue regular monitoring",
            "Review security logs periodically"
        ]
    }


@router.get("/severity-distribution")
async def get_severity_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get alert distribution by severity"""
    result = await db.execute(
        select(Alert.severity, func.count(Alert.id))
        .group_by(Alert.severity)
    )
    
    distribution = {}
    for row in result:
        distribution[row[0]] = row[1]
    
    return {
        "distribution": distribution,
        "total": sum(distribution.values())
    }


@router.get("/threat-types")
async def get_threat_type_distribution(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get threat distribution by type"""
    result = await db.execute(
        select(ThreatLog.threat_type, func.count(ThreatLog.id))
        .group_by(ThreatLog.threat_type)
    )
    
    distribution = {}
    for row in result:
        distribution[row[0]] = row[1]
    
    return {
        "distribution": distribution,
        "total": sum(distribution.values())
    }
