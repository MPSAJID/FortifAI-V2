"""
Structured Logger for FortifAI
"""
import structlog
import logging
import sys
from datetime import datetime

def setup_logging(log_level: str = "INFO"):
    """Setup structured logging"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )

def get_logger(name: str):
    """Get a structured logger instance"""
    setup_logging()
    return structlog.get_logger(name)

class SecurityLogger:
    """Security-focused logger for audit trails"""
    
    def __init__(self, service_name: str):
        self.logger = get_logger(service_name)
        self.service = service_name
    
    def log_security_event(self, event_type: str, details: dict, severity: str = "INFO"):
        """Log security-related events"""
        self.logger.info(
            "security_event",
            event_type=event_type,
            service=self.service,
            severity=severity,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def log_authentication(self, user: str, success: bool, ip_address: str = None):
        """Log authentication attempts"""
        self.logger.info(
            "authentication",
            user=user,
            success=success,
            ip_address=ip_address,
            timestamp=datetime.now().isoformat()
        )
    
    def log_threat_detection(self, threat_type: str, confidence: float, details: dict):
        """Log threat detection events"""
        self.logger.warning(
            "threat_detected",
            threat_type=threat_type,
            confidence=confidence,
            details=details,
            timestamp=datetime.now().isoformat()
        )
