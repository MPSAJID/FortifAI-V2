"""
FortifAI Alert Service
Enhanced version with API endpoints
"""
import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from enum import Enum
import threading
import queue
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn

load_dotenv()

class AlertSeverity(Enum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    INFO = 0

class AlertCreate(BaseModel):
    title: str
    message: str
    severity: str
    source: str
    metadata: Optional[Dict[str, Any]] = {}

class AlertManager:
    """
    Centralized alert management with multiple notification channels
    """
    
    def __init__(self):
        self.alert_queue = queue.Queue()
        self.alert_history = []
        self.alert_rules = []
        
        # Email configuration
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL')
        }
        
        # Notification webhooks
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.teams_webhook = os.getenv('TEAMS_WEBHOOK_URL')
        
        print("[INIT] AlertManager initialized")
        print(f"[INIT] Email config: smtp_server={self.email_config['smtp_server']}, username={bool(self.email_config['username'])}")
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.processing_thread.start()
        print("[INIT] Background processing thread started")
    
    def create_alert(self, title: str, message: str, severity: str, source: str, metadata: dict = None):
        """Create a new alert"""
        alert = {
            'id': f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.alert_history)}",
            'title': title,
            'message': message,
            'severity': severity.upper(),
            'source': source,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'status': 'new',
            'acknowledged': False,
            'resolved': False
        }
        
        print(f"[CREATE] Adding alert to queue: {alert['id']} (severity={alert['severity']})")
        self.alert_queue.put(alert)
        print(f"[CREATE] Alert added to queue. Queue size: {self.alert_queue.qsize()}")
        self.alert_history.append(alert)
        
        return alert
    
    def _process_alerts(self):
        """Background thread to process alerts"""
        print("[BACKGROUND] Alert processing thread started")
        while True:
            try:
                alert = self.alert_queue.get(timeout=1)
                print(f"[BACKGROUND] Processing alert: {alert['id']} - {alert['title']}")
                self._dispatch_alert(alert)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[BACKGROUND] Error processing alert: {e}")
                import traceback
                traceback.print_exc()
    
    def _dispatch_alert(self, alert: dict):
        """Dispatch alert to configured channels"""
        severity = alert['severity']
        
        # Critical and High alerts go to all channels
        if severity in ['CRITICAL', 'HIGH']:
            self._send_email_alert(alert)
            self._send_slack_alert(alert)
            self._send_teams_alert(alert)
        elif severity == 'MEDIUM':
            self._send_slack_alert(alert)
            self._send_teams_alert(alert)
        else:
            self._send_slack_alert(alert)
    
    def _send_email_alert(self, alert: dict):
        """Send alert via email"""
        print(f"[EMAIL] Checking email config: username={bool(self.email_config['username'])}")
        if not self.email_config['username']:
            print("[EMAIL] No SMTP username configured, skipping email send")
            return
        
        try:
            recipient = os.getenv('ALERT_EMAIL_TO', '')
            print(f"[EMAIL] Preparing email from {self.email_config['from_email']} to {recipient}")
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = recipient
            msg['Subject'] = f"[{alert['severity']}] {alert['title']}"
            
            body = f"""
            Alert: {alert['title']}
            Severity: {alert['severity']}
            Source: {alert['source']}
            Time: {alert['timestamp']}
            
            {alert['message']}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            print(f"[EMAIL] Connecting to {self.email_config['smtp_server']}:{self.email_config['smtp_port']}")
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                print("[EMAIL] SMTP connection established, starting TLS...")
                server.starttls()
                print(f"[EMAIL] TLS started, logging in as {self.email_config['username']}")
                server.login(self.email_config['username'], self.email_config['password'])
                print(f"[EMAIL] Login successful, sending message...")
                server.send_message(msg)
                print("[EMAIL] Email sent successfully!")
                
        except Exception as e:
            print(f"[EMAIL] ERROR - Email alert failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def _send_slack_alert(self, alert: dict):
        """Send alert to Slack"""
        if not self.slack_webhook:
            return
        
        try:
            color = {
                'CRITICAL': '#FF0000',
                'HIGH': '#FF6600',
                'MEDIUM': '#FFCC00',
                'LOW': '#00FF00',
                'INFO': '#0066FF'
            }.get(alert['severity'], '#808080')
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"[{alert['severity']}] {alert['title']}",
                    "text": alert['message'],
                    "fields": [
                        {"title": "Source", "value": alert['source'], "short": True},
                        {"title": "Time", "value": alert['timestamp'], "short": True}
                    ]
                }]
            }
            
            requests.post(self.slack_webhook, json=payload, timeout=10)
            
        except Exception as e:
            print(f"Slack alert failed: {e}")
    
    def _send_teams_alert(self, alert: dict):
        """Send alert to Microsoft Teams"""
        if not self.teams_webhook:
            return
        
        try:
            color = {
                'CRITICAL': 'FF0000',
                'HIGH': 'FF6600',
                'MEDIUM': 'FFCC00',
                'LOW': '00FF00',
                'INFO': '0066FF'
            }.get(alert['severity'], '808080')
            
            payload = {
                "@type": "MessageCard",
                "themeColor": color,
                "title": f"[{alert['severity']}] {alert['title']}",
                "text": alert['message'],
                "sections": [{
                    "facts": [
                        {"name": "Source", "value": alert['source']},
                        {"name": "Time", "value": alert['timestamp']}
                    ]
                }]
            }
            
            requests.post(self.teams_webhook, json=payload, timeout=10)
            
        except Exception as e:
            print(f"Teams alert failed: {e}")
    
    def get_alerts(self, limit: int = 100, severity: str = None) -> List[dict]:
        """Get alert history"""
        alerts = self.alert_history[-limit:]
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity.upper()]
        return alerts
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alert_history:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['status'] = 'acknowledged'
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alert_history:
            if alert['id'] == alert_id:
                alert['resolved'] = True
                alert['status'] = 'resolved'
                alert['resolved_at'] = datetime.now().isoformat()
                return True
        return False


# FastAPI Application
app = FastAPI(title="FortifAI Alert Service", version="1.0.0")
alert_manager = AlertManager()

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "alert-service"}

@app.post("/api/test-smtp")
async def test_smtp():
    """Test SMTP connection and send test email"""
    print("[TEST] Testing SMTP connection...")
    config = alert_manager.email_config
    
    if not config['username']:
        return {"status": "error", "message": "No SMTP credentials configured"}
    
    try:
        print(f"[TEST] Connecting to {config['smtp_server']}:{config['smtp_port']}")
        with smtplib.SMTP(config['smtp_server'], config['smtp_port'], timeout=10) as server:
            print("[TEST] SMTP connection established")
            server.starttls()
            print("[TEST] TLS started")
            server.login(config['username'], config['password'])
            print("[TEST] Login successful")
            
            # Create test email
            msg = MIMEMultipart()
            msg['From'] = config['from_email']
            msg['To'] = os.getenv('ALERT_EMAIL_TO', 'ajack6590@gmail.com')
            msg['Subject'] = "[TEST] FortifAI SMTP Connection Test"
            msg.attach(MIMEText("This is a test email from FortifAI Alert Service.\n\nIf you received this, SMTP is working correctly!", 'plain'))
            
            print(f"[TEST] Sending test email...")
            server.send_message(msg)
            print("[TEST] Test email sent successfully!")
            
            return {"status": "success", "message": "SMTP test email sent successfully"}
            
    except Exception as e:
        print(f"[TEST] ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": f"{type(e).__name__}: {str(e)}"}

@app.post("/alerts")
async def create_alert(alert_data: AlertCreate):
    alert = alert_manager.create_alert(
        title=alert_data.title,
        message=alert_data.message,
        severity=alert_data.severity,
        source=alert_data.source,
        metadata=alert_data.metadata
    )
    return alert

@app.post("/api/notify")
async def notify_alert(alert_data: AlertCreate):
    """Endpoint for API service to send email notifications for critical alerts"""
    alert = alert_manager.create_alert(
        title=alert_data.title,
        message=alert_data.message,
        severity=alert_data.severity,
        source=alert_data.source,
        metadata=alert_data.metadata
    )
    return alert

@app.get("/alerts")
async def get_alerts(limit: int = 100, severity: str = None):
    return alert_manager.get_alerts(limit=limit, severity=severity)

@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    if alert_manager.acknowledge_alert(alert_id):
        return {"status": "acknowledged"}
    raise HTTPException(status_code=404, detail="Alert not found")

@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    if alert_manager.resolve_alert(alert_id):
        return {"status": "resolved"}
    raise HTTPException(status_code=404, detail="Alert not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)
