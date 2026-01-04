"""
Common Utility Functions
"""
import uuid
from datetime import datetime
from typing import Optional
import hashlib
import re

def generate_id(prefix: str = "") -> str:
    """Generate unique ID with optional prefix"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique = uuid.uuid4().hex[:8]
    if prefix:
        return f"{prefix}-{timestamp}-{unique}"
    return f"{timestamp}-{unique}"

def parse_timestamp(timestamp: str) -> Optional[datetime]:
    """Parse timestamp string to datetime"""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp, fmt)
        except ValueError:
            continue
    return None

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash a string using specified algorithm"""
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text)
    return sanitized.strip()

def extract_ip_addresses(text: str) -> list:
    """Extract IP addresses from text"""
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    return re.findall(ip_pattern, text)

def is_valid_ip(ip: str) -> bool:
    """Validate IP address format"""
    pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(pattern, ip))

def calculate_risk_score(factors: dict) -> float:
    """Calculate risk score based on various factors"""
    weights = {
        'severity': 0.3,
        'confidence': 0.25,
        'frequency': 0.2,
        'impact': 0.15,
        'exposure': 0.1
    }
    
    score = 0.0
    for factor, weight in weights.items():
        if factor in factors:
            score += factors[factor] * weight
    
    return min(max(score, 0.0), 1.0)

def format_bytes(size: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"
