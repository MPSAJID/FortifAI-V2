"""
FortifAI Data Collector Service
Collects logs from various sources for analysis
"""
import asyncio
import json
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional
import httpx
import os
from dotenv import load_dotenv

# Add parent directory to path for common imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from collectors.file_collector import FileLogCollector
from collectors.process_collector import ProcessCollector
from collectors.network_collector import NetworkCollector
from collectors.event_collector import EventLogCollector

try:
    from common.logger import get_logger, SecurityLogger
    from common.redis_client import RedisClient
    from common.utils import generate_id, calculate_risk_score
    from common.constants import SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW, SEVERITY_INFO
except ImportError:
    # Fallback if common module not available
    import logging
    logging.basicConfig(level=logging.INFO)
    def get_logger(name):
        return logging.getLogger(name)
    SecurityLogger = None
    RedisClient = None
    generate_id = lambda prefix="": f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    calculate_risk_score = lambda factors: factors.get('confidence', 0.5)
    SEVERITY_CRITICAL, SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW, SEVERITY_INFO = "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"

load_dotenv()

# Initialize logger
logger = get_logger("data-collector")


class DataCollectorService:
    """
    Main data collector service that orchestrates multiple collectors
    and sends data to the ML engine for analysis
    """
    
    def __init__(self):
        self.api_url = os.getenv("API_URL", "http://localhost:8000")
        self.ml_engine_url = os.getenv("ML_ENGINE_URL", "http://localhost:5000")
        
        # Initialize collectors
        self.collectors = {
            'file': FileLogCollector(),
            'process': ProcessCollector(),
            'network': NetworkCollector(),
            'events': EventLogCollector()
        }
        
        self.running = False
        self.collection_interval = int(os.getenv("COLLECTION_INTERVAL", 30))
        self.batch_size = int(os.getenv("BATCH_SIZE", 50))
        
        # Initialize Redis client for caching (optional)
        self.redis_client = None
        if RedisClient:
            try:
                self.redis_client = RedisClient()
                logger.info("Redis client initialized")
            except Exception as e:
                logger.warning(f"Redis not available: {e}")
        
        # Initialize security logger
        self.security_logger = None
        if SecurityLogger:
            self.security_logger = SecurityLogger("data-collector")
        
        # Statistics tracking
        self.stats = {
            "total_collected": 0,
            "total_threats": 0,
            "total_alerts": 0,
            "collection_errors": 0,
            "start_time": None,
            "last_collection": None,
            "collector_stats": {name: {"collected": 0, "errors": 0} for name in self.collectors}
        }
    
    async def start(self):
        """Start the data collection service"""
        self.running = True
        self.stats["start_time"] = datetime.now().isoformat()
        
        logger.info(
            "data_collector_started",
            interval=self.collection_interval,
            batch_size=self.batch_size,
            collectors=list(self.collectors.keys())
        )
        print(f"🔍 Data Collector Started - Interval: {self.collection_interval}s")
        
        while self.running:
            try:
                await self.collect_and_process()
                self.stats["last_collection"] = datetime.now().isoformat()
            except Exception as e:
                self.stats["collection_errors"] += 1
                logger.error("collection_cycle_error", error=str(e))
                print(f"❌ Collection error: {e}")
            
            await asyncio.sleep(self.collection_interval)
    
    async def stop(self):
        """Stop the data collection service"""
        self.running = False
        
        # Stop file collector observer
        if 'file' in self.collectors:
            try:
                self.collectors['file'].stop()
            except Exception as e:
                logger.warning(f"Error stopping file collector: {e}")
        
        logger.info("data_collector_stopped", stats=self.stats)
        print("🛑 Data Collector Stopped")
    
    def get_health_status(self) -> Dict:
        """Get health status of the service"""
        return {
            "status": "healthy" if self.running else "stopped",
            "uptime": self._calculate_uptime(),
            "stats": self.stats,
            "collectors": {
                name: {
                    "active": True,
                    "stats": self.stats["collector_stats"].get(name, {})
                }
                for name in self.collectors
            }
        }
    
    def _calculate_uptime(self) -> str:
        """Calculate service uptime"""
        if not self.stats["start_time"]:
            return "0s"
        start = datetime.fromisoformat(self.stats["start_time"])
        delta = datetime.now() - start
        return str(delta)
    
    async def collect_and_process(self):
        """Collect data from all sources and process"""
        timestamp = datetime.now().isoformat()
        
        # Collect from all sources concurrently
        collection_tasks = [
            self._collect_from_source(name, collector)
            for name, collector in self.collectors.items()
        ]
        
        results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        
        # Process collected data
        all_logs = []
        for i, result in enumerate(results):
            collector_name = list(self.collectors.keys())[i]
            if isinstance(result, Exception):
                self.stats["collector_stats"][collector_name]["errors"] += 1
                logger.error("collector_error", collector=collector_name, error=str(result))
                continue
            
            self.stats["collector_stats"][collector_name]["collected"] += len(result)
            all_logs.extend(result)
        
        self.stats["total_collected"] += len(all_logs)
        
        if all_logs:
            # Cache collected data if Redis available
            if self.redis_client:
                await self._cache_logs(all_logs)
            
            # Send to ML engine in batches
            await self._send_to_ml_engine_batch(all_logs)
            
            # Publish real-time updates via Redis
            if self.redis_client:
                await self._publish_updates(all_logs)
    
    async def _collect_from_source(self, name: str, collector) -> List[Dict]:
        """Collect data from a single source"""
        try:
            logs = collector.collect()
            
            # Add metadata to each log
            for log in logs:
                log["collection_id"] = generate_id(f"col-{name}")
                log["collected_at"] = datetime.now().isoformat()
            
            logger.debug("collector_success", collector=name, count=len(logs))
            return logs
        except Exception as e:
            logger.error("collector_failed", collector=name, error=str(e))
            print(f"Error collecting from {name}: {e}")
            return []
    
    async def _cache_logs(self, logs: List[Dict]):
        """Cache collected logs in Redis"""
        try:
            for log in logs:
                log_id = log.get("collection_id", generate_id("log"))
                self.redis_client.set(f"log:{log_id}", log, expire=3600)  # 1 hour TTL
        except Exception as e:
            logger.warning("cache_error", error=str(e))
    
    async def _publish_updates(self, logs: List[Dict]):
        """Publish real-time updates via Redis pub/sub"""
        try:
            suspicious_logs = [l for l in logs if l.get("is_suspicious", False)]
            if suspicious_logs:
                self.redis_client.publish("security:events", {
                    "type": "suspicious_activity",
                    "count": len(suspicious_logs),
                    "timestamp": datetime.now().isoformat(),
                    "summary": [
                        {"type": l.get("event_type"), "source": l.get("source")}
                        for l in suspicious_logs[:10]  # Limit to 10
                    ]
                })
        except Exception as e:
            logger.warning("publish_error", error=str(e))
    
    async def _send_to_ml_engine_batch(self, logs: List[Dict]):
        """Send collected logs to ML engine in batches for analysis"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Process in batches
            for i in range(0, len(logs), self.batch_size):
                batch = logs[i:i + self.batch_size]
                
                try:
                    # Send batch to ML engine
                    response = await client.post(
                        f"{self.ml_engine_url}/analyze/batch",
                        json={"logs": batch},
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        results = response.json()
                        threats = results.get("threats", [])
                        
                        for threat in threats:
                            self.stats["total_threats"] += 1
                            log_index = threat.get("log_index", 0)
                            original_log = batch[log_index] if log_index < len(batch) else {}
                            await self._create_alert(original_log, threat)
                            
                            # Log threat detection
                            if self.security_logger:
                                self.security_logger.log_threat_detection(
                                    threat_type=threat.get("threat_type", "unknown"),
                                    confidence=threat.get("confidence", 0),
                                    details={"log": original_log, "analysis": threat}
                                )
                    else:
                        logger.warning("ml_engine_error", status=response.status_code)
                        # Fallback to individual processing
                        await self._send_to_ml_engine(batch)
                        
                except httpx.HTTPError as e:
                    logger.error("ml_engine_batch_error", error=str(e))
                    # Fallback to individual processing on error
                    await self._send_to_ml_engine(batch)
    
    async def _send_to_ml_engine(self, logs: List[Dict]):
        """Send collected logs to ML engine individually (fallback method)"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                for log in logs:
                    response = await client.post(
                        f"{self.ml_engine_url}/analyze",
                        json={"log_data": log},
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("is_threat", False):
                            self.stats["total_threats"] += 1
                            await self._create_alert(log, result)
                            
            except httpx.HTTPError as e:
                logger.error("ml_engine_communication_error", error=str(e))
                print(f"ML Engine communication error: {e}")
    
    async def _create_alert(self, log: Dict, analysis: Dict):
        """Create an alert for detected threats"""
        self.stats["total_alerts"] += 1
        
        async with httpx.AsyncClient() as client:
            try:
                alert_id = generate_id("alert")
                risk_score = analysis.get('risk_score', analysis.get('confidence', 0.5))
                
                alert_data = {
                    "id": alert_id,
                    "title": f"Threat Detected: {analysis.get('threat_type', 'Unknown')}",
                    "message": f"Confidence: {analysis.get('confidence', 0):.2%}",
                    "severity": self._get_severity(risk_score),
                    "source": log.get("source", "data-collector"),
                    "threat_type": analysis.get("threat_type", "unknown"),
                    "confidence": analysis.get("confidence", 0),
                    "risk_score": risk_score,
                    "metadata": {
                        "log": log,
                        "analysis": analysis
                    },
                    "created_at": datetime.now().isoformat()
                }
                
                # Cache alert in Redis
                if self.redis_client:
                    self.redis_client.cache_alert(alert_id, alert_data)
                    # Publish real-time alert
                    self.redis_client.publish("alerts:new", alert_data)
                
                response = await client.post(
                    f"{self.api_url}/api/v1/alerts",
                    json=alert_data,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info("alert_created", alert_id=alert_id, severity=alert_data["severity"])
                else:
                    logger.warning("alert_creation_failed", status=response.status_code)
                    
            except httpx.HTTPError as e:
                logger.error("alert_creation_error", error=str(e))
                print(f"Alert creation error: {e}")
    
    def _get_severity(self, risk_score: float) -> str:
        """Convert risk score to severity level"""
        if risk_score >= 0.9:
            return SEVERITY_CRITICAL
        elif risk_score >= 0.7:
            return SEVERITY_HIGH
        elif risk_score >= 0.5:
            return SEVERITY_MEDIUM
        elif risk_score >= 0.3:
            return SEVERITY_LOW
        return SEVERITY_INFO


# HTTP Health Check Server (optional, runs alongside main service)
class HealthCheckServer:
    """Simple HTTP server for health checks"""
    
    def __init__(self, service: DataCollectorService, port: int = 8081):
        self.service = service
        self.port = port
        self.server = None
    
    async def start(self):
        """Start health check server"""
        from aiohttp import web
        
        app = web.Application()
        app.router.add_get('/health', self.health_handler)
        app.router.add_get('/stats', self.stats_handler)
        app.router.add_get('/ready', self.ready_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        self.server = web.TCPSite(runner, '0.0.0.0', self.port)
        await self.server.start()
        logger.info(f"Health check server started on port {self.port}")
    
    async def health_handler(self, request):
        """Health check endpoint"""
        from aiohttp import web
        status = self.service.get_health_status()
        return web.json_response(status)
    
    async def stats_handler(self, request):
        """Stats endpoint"""
        from aiohttp import web
        return web.json_response(self.service.stats)
    
    async def ready_handler(self, request):
        """Readiness probe endpoint"""
        from aiohttp import web
        if self.service.running:
            return web.json_response({"ready": True})
        return web.json_response({"ready": False}, status=503)


async def main():
    """Main entry point with signal handling"""
    service = DataCollectorService()
    health_server = None
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("shutdown_signal_received", signal=sig)
        print("\n🛑 Shutdown signal received, stopping...")
        asyncio.create_task(service.stop())
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start health check server if aiohttp is available
        try:
            import aiohttp
            health_port = int(os.getenv("HEALTH_PORT", 8081))
            health_server = HealthCheckServer(service, health_port)
            await health_server.start()
        except ImportError:
            logger.warning("aiohttp not installed, health check server disabled")
        
        # Start the main data collection service
        await service.start()
        
    except Exception as e:
        logger.error("service_error", error=str(e))
        raise
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
