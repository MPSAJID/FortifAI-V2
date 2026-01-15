#!/usr/bin/env python3
"""
Quick script to check alerts in the database
"""
import os
import asyncio
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, desc
from backend.api.core.database import AsyncSessionLocal
from backend.api.models.alert import Alert

async def check_alerts():
    """Check recent alerts in the database"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Alert).order_by(desc(Alert.created_at)).limit(10)
        )
        alerts = result.scalars().all()
        
        if not alerts:
            print("No alerts found in database")
            return
        
        print(f"\n{'='*80}")
        print(f"Found {len(alerts)} recent alerts:")
        print(f"{'='*80}\n")
        
        for alert in alerts:
            print(f"🚨 [{alert.severity}] {alert.title}")
            print(f"   ID: {alert.alert_id}")
            print(f"   Source: {alert.source}")
            print(f"   Status: {alert.status}")
            print(f"   Created: {alert.created_at}")
            if alert.message:
                print(f"   Message: {alert.message[:100]}...")
            print()

if __name__ == "__main__":
    asyncio.run(check_alerts())
