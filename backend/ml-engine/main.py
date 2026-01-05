"""
FortifAI ML Engine Service
Provides threat detection and analysis endpoints
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
from datetime import datetime

from threat_classifier import ThreatClassifier
from behaviour_analytics import UserBehaviorAnalytics
from anomaly_detector import AnomalyDetector

app = FastAPI(title="FortifAI ML Engine", version="1.0.0")

# Initialize ML models
threat_classifier = ThreatClassifier()
behavior_analytics = UserBehaviorAnalytics()
anomaly_detector = AnomalyDetector()

class AnalyzeRequest(BaseModel):
    log_data: Dict[str, Any]
    
    class Config:
        extra = "allow"  # Allow extra fields
    
class AnalyzeResponse(BaseModel):
    is_threat: bool
    threat_type: str
    confidence: float
    risk_score: float
    classification: str
    recommendations: List[str]

class BehaviorRequest(BaseModel):
    user: str
    activity: Dict[str, Any]

class TrainRequest(BaseModel):
    training_data: List[Dict[str, Any]]
    labels: Optional[List[str]] = None

class BatchAnalyzeRequest(BaseModel):
    logs: List[Dict[str, Any]]

class BatchAnalyzeResponse(BaseModel):
    threats: List[Dict[str, Any]]
    total_analyzed: int
    threat_count: int

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ml-engine",
        "models": {
            "threat_classifier": threat_classifier.is_trained,
            "anomaly_detector": anomaly_detector.is_trained
        }
    }

@app.post("/analyze/debug")
async def analyze_debug(request: dict):
    """Debug endpoint to see raw request"""
    print(f"Received raw request: {request}")
    return {"received": request, "type": str(type(request))}

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_log(request: dict):
    """Analyze a log entry for potential threats
    
    Accepts either:
    - {"log_data": {...}} format
    - Raw log data directly
    """
    try:
        # Handle both wrapped and unwrapped log data
        if "log_data" in request:
            log_data = request["log_data"]
        else:
            log_data = request
        
        print(f"Analyzing log data: {log_data}")
        result = threat_classifier.predict(log_data)
        
        is_threat = result['classification'] != 'normal'
        
        recommendations = []
        if is_threat:
            recommendations = _get_recommendations(result['classification'])
        
        return AnalyzeResponse(
            is_threat=is_threat,
            threat_type=result.get('threat_type', 'unknown'),
            confidence=result.get('confidence', 0.0),
            risk_score=result.get('risk_score', 0.0),
            classification=result['classification'],
            recommendations=recommendations
        )
    except Exception as e:
        print(f"Error analyzing log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/behavior/record")
async def record_behavior(request: BehaviorRequest):
    """Record user behavior for analysis"""
    try:
        behavior_analytics.record_activity(request.user, request.activity)
        return {"status": "recorded", "user": request.user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/behavior/analyze")
async def analyze_behavior(request: BehaviorRequest):
    """Analyze user behavior for anomalies"""
    try:
        result = behavior_analytics.analyze_behavior(request.user, request.activity)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/anomaly/detect")
async def detect_anomaly(request: AnalyzeRequest):
    """Detect anomalies in system data"""
    try:
        result = anomaly_detector.detect(request.log_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/batch", response_model=BatchAnalyzeResponse)
async def analyze_batch(request: BatchAnalyzeRequest):
    """Analyze multiple log entries in batch for efficiency"""
    try:
        threats = []
        
        for idx, log in enumerate(request.logs):
            # Run threat classification
            result = threat_classifier.predict(log)
            
            # Run anomaly detection
            anomaly_result = anomaly_detector.detect(log)
            
            is_threat = result['classification'] != 'normal'
            is_anomaly = anomaly_result.get('is_anomaly', False)
            
            # Combine results - flag if either classifier or anomaly detector triggers
            if is_threat or is_anomaly:
                # Boost confidence if both detectors agree
                confidence = result.get('confidence', 0.0)
                if is_threat and is_anomaly:
                    confidence = min(confidence * 1.2, 1.0)
                
                threat_info = {
                    "log_index": idx,
                    "is_threat": True,
                    "threat_type": result.get('threat_type', result['classification']),
                    "confidence": confidence,
                    "risk_score": result.get('risk_score', 0.0),
                    "classification": result['classification'],
                    "anomaly_score": anomaly_result.get('anomaly_score', 0.0),
                    "anomaly_indicators": anomaly_result.get('statistical_anomalies', []),
                    "recommendations": _get_recommendations(result['classification'])
                }
                threats.append(threat_info)
        
        return BatchAnalyzeResponse(
            threats=threats,
            total_analyzed=len(request.logs),
            threat_count=len(threats)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def train_models(request: TrainRequest):
    """Train ML models with new data"""
    try:
        # Train threat classifier
        if request.labels:
            threat_classifier.train(request.training_data, request.labels)
        
        # Train anomaly detector
        anomaly_detector.fit(request.training_data)
        
        return {
            "status": "training_complete",
            "samples": len(request.training_data),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/status")
async def get_model_status():
    """Get status of all ML models"""
    return {
        "threat_classifier": {
            "trained": threat_classifier.is_trained,
            "categories": threat_classifier.threat_categories
        },
        "behavior_analytics": {
            "users_tracked": len(behavior_analytics.user_profiles)
        },
        "anomaly_detector": {
            "trained": anomaly_detector.is_trained
        }
    }

def _get_recommendations(classification: str) -> List[str]:
    """Get recommendations based on threat classification"""
    recommendations_map = {
        'malware': [
            "Isolate the affected system immediately",
            "Run full antivirus scan",
            "Check for lateral movement",
            "Review recent file downloads"
        ],
        'ransomware': [
            "Disconnect from network immediately",
            "Do not pay the ransom",
            "Check backup availability",
            "Contact incident response team"
        ],
        'ddos': [
            "Enable DDoS protection",
            "Rate limit incoming requests",
            "Contact ISP for upstream filtering",
            "Review firewall rules"
        ],
        'brute_force': [
            "Enable account lockout policy",
            "Implement MFA",
            "Review failed login attempts",
            "Block source IP addresses"
        ],
        'data_exfiltration': [
            "Block outbound connections",
            "Review data access logs",
            "Identify affected data",
            "Check for compromised credentials"
        ],
        'privilege_escalation': [
            "Review privilege changes",
            "Check for unauthorized admin accounts",
            "Audit group memberships",
            "Review security policies"
        ]
    }
    
    return recommendations_map.get(classification, [
        "Review the detected activity",
        "Consult security team",
        "Document the incident"
    ])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
