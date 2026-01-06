"""
Local Data Collector Test Script
Monitors real Windows system activity and sends to FortifAI API
"""
import asyncio
import httpx
import psutil
import os
import sys
from datetime import datetime
from typing import Dict, List

# Configuration
API_URL = "http://localhost:8000"
INTERNAL_API_KEY = "fortifai-internal-service-key"
ML_ENGINE_URL = "http://localhost:5000"

# Suspicious process patterns
SUSPICIOUS_PATTERNS = [
    'mimikatz', 'psexec', 'procdump', 'netcat', 'nc.exe',
    'certutil', 'bitsadmin', 'powershell -enc', 'powershell -e ',
    'base64', 'nmap', 'masscan', 'keylogger', 'reverse', 'shell'
]

class LocalCollector:
    def __init__(self):
        self.known_processes = set()
        self.stats = {"collected": 0, "threats": 0, "alerts": 0}
    
    def collect_processes(self) -> List[Dict]:
        """Collect real process data from Windows"""
        processes = []
        current_pids = set()
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'cmdline', 'create_time']):
            try:
                info = proc.info
                current_pids.add(info['pid'])
                
                is_new = info['pid'] not in self.known_processes
                is_suspicious = self._is_suspicious(info)
                
                # Only collect new or suspicious
                if is_new or is_suspicious:
                    processes.append({
                        "event_type": "process_info",
                        "timestamp": datetime.now().isoformat(),
                        "pid": info['pid'],
                        "process_name": info['name'],
                        "user": info['username'],
                        "cpu_usage": info['cpu_percent'] or 0,
                        "memory_usage": info['memory_percent'] or 0,
                        "cmdline": ' '.join(info['cmdline']) if info['cmdline'] else '',
                        "is_new": is_new,
                        "is_suspicious": is_suspicious,
                        "source": "local_process_collector"
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        self.known_processes = current_pids
        return processes
    
    def _is_suspicious(self, info: Dict) -> bool:
        """Check if process is suspicious"""
        name = (info.get('name') or '').lower()
        cmdline = ' '.join(info.get('cmdline') or []).lower()
        
        for pattern in SUSPICIOUS_PATTERNS:
            if pattern in name or pattern in cmdline:
                return True
        
        # High resource usage
        cpu = info.get('cpu_percent', 0) or 0
        memory = info.get('memory_percent', 0) or 0
        if cpu > 80 or memory > 50:
            return True
        
        return False
    
    async def analyze_with_ml(self, logs: List[Dict]) -> List[Dict]:
        """Send logs to ML engine for analysis"""
        threats = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{ML_ENGINE_URL}/analyze/batch",
                    json={"logs": logs},
                    timeout=30.0
                )
                if response.status_code == 200:
                    result = response.json()
                    threats = result.get("threats", [])
                    print(f"  ML Engine: Analyzed {len(logs)} logs, found {len(threats)} threats")
            except Exception as e:
                print(f"  ML Engine error: {e}")
        return threats
    
    async def create_alert(self, log: Dict, threat: Dict):
        """Create alert in API"""
        async with httpx.AsyncClient() as client:
            try:
                alert_data = {
                    "title": f"Threat Detected: {threat.get('threat_type', 'Unknown')}",
                    "message": f"Process: {log.get('process_name')} | Confidence: {threat.get('confidence', 0):.0%}",
                    "severity": self._get_severity(threat.get('risk_score', 0.5)),
                    "source": log.get('source', 'local_collector'),
                    "metadata": {"log": log, "threat": threat}
                }
                
                response = await client.post(
                    f"{API_URL}/api/v1/alerts/internal",
                    json=alert_data,
                    headers={"X-Internal-Key": INTERNAL_API_KEY},
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    self.stats["alerts"] += 1
                    print(f"  ✓ Alert created: {alert_data['severity']} - {alert_data['title']}")
                else:
                    print(f"  ✗ Alert failed: {response.status_code}")
            except Exception as e:
                print(f"  ✗ Alert error: {e}")
    
    def _get_severity(self, risk_score: float) -> str:
        if risk_score >= 0.9: return "CRITICAL"
        if risk_score >= 0.7: return "HIGH"
        if risk_score >= 0.5: return "MEDIUM"
        if risk_score >= 0.3: return "LOW"
        return "INFO"
    
    async def run_once(self):
        """Run single collection cycle"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Collecting real system data...")
        
        # Collect processes
        processes = self.collect_processes()
        self.stats["collected"] += len(processes)
        print(f"  Collected {len(processes)} process events")
        
        if processes:
            # Show sample
            for p in processes[:3]:
                status = "⚠️ SUSPICIOUS" if p['is_suspicious'] else "🆕 New"
                print(f"    {status}: {p['process_name']} (PID: {p['pid']})")
            
            # Analyze with ML
            threats = await self.analyze_with_ml(processes)
            self.stats["threats"] += len(threats)
            
            # Create alerts for threats
            for i, threat in enumerate(threats):
                if threat.get("is_threat"):
                    await self.create_alert(processes[i % len(processes)], threat)
        
        print(f"  Stats: {self.stats}")
    
    async def run_continuous(self, interval: int = 15):
        """Run continuously"""
        print("="*60)
        print("FortifAI Local Data Collector - REAL SYSTEM MONITORING")
        print("="*60)
        print(f"API: {API_URL}")
        print(f"ML Engine: {ML_ENGINE_URL}")
        print(f"Interval: {interval}s")
        print("Press Ctrl+C to stop\n")
        
        while True:
            await self.run_once()
            await asyncio.sleep(interval)


async def main():
    collector = LocalCollector()
    
    # Run 3 cycles for testing
    print("\nRunning 3 collection cycles (15s interval)...")
    for i in range(3):
        await collector.run_once()
        if i < 2:
            print("\nWaiting 15 seconds...")
            await asyncio.sleep(15)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print(f"Total collected: {collector.stats['collected']}")
    print(f"Threats detected: {collector.stats['threats']}")
    print(f"Alerts created: {collector.stats['alerts']}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
