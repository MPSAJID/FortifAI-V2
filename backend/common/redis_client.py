"""
Redis Client for caching and pub/sub
"""
import redis
import json
from typing import Any, Optional
import os

class RedisClient:
    """Redis client wrapper for FortifAI"""
    
    def __init__(self, url: str = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            self._client = redis.from_url(self.url, decode_responses=True)
        return self._client
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return self.client.setex(key, expire, value)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        return bool(self.client.delete(key))
    
    def publish(self, channel: str, message: dict):
        """Publish message to channel"""
        self.client.publish(channel, json.dumps(message))
    
    def subscribe(self, channel: str):
        """Subscribe to channel"""
        pubsub = self.client.pubsub()
        pubsub.subscribe(channel)
        return pubsub
    
    def cache_threat(self, threat_id: str, threat_data: dict, expire: int = 86400):
        """Cache threat data"""
        self.set(f"threat:{threat_id}", threat_data, expire)
    
    def cache_alert(self, alert_id: str, alert_data: dict, expire: int = 86400):
        """Cache alert data"""
        self.set(f"alert:{alert_id}", alert_data, expire)
    
    def get_cached_threat(self, threat_id: str) -> Optional[dict]:
        """Get cached threat"""
        return self.get(f"threat:{threat_id}")
    
    def increment_counter(self, key: str) -> int:
        """Increment a counter"""
        return self.client.incr(key)
    
    def get_rate_limit(self, identifier: str, window: int = 60) -> int:
        """Get current rate limit count"""
        key = f"ratelimit:{identifier}"
        count = self.client.get(key)
        return int(count) if count else 0
    
    def check_rate_limit(self, identifier: str, limit: int = 100, window: int = 60) -> bool:
        """Check if rate limit exceeded"""
        key = f"ratelimit:{identifier}"
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, window)
        return current <= limit
