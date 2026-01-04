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

load_dotenv()

class AlertSeverity(Enum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    INFO = 0

class AlertManager:
    """
    Centralized alert management with multiple notification channels:
    - Email
    - Slack
    - Microsoft Teams
    - SMS (Twilio)
    - Webhook
    """
    
    def __init__(self):
        self.alert_queue = queue.Queue()
        self.alert_history = []
        self.alert_rules = []
        self.notification_channels = []
        
        # Email configuration
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL')
        }
        
        # Slack configuration
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        
        # Teams configuration
        self.teams_webhook = os.getenv('TEAMS_WEBHOOK_URL')
        
        # Start alert processing thread
        self.processing_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self.processing_thread.start()
    
    def create_alert(self, title, message, severity, source, metadata=None):
        """Create a new alert"""
        alert = {
            'id': f"ALERT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.alert_history)}",
            'title': title,
            'message': message,
            'severity': severity.name if isinstance(severity, AlertSeverity) else severity,
            'source': source,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'status': 'new',
            'acknowledged': False,
            'resolved': False
        }
        
        self.alert_queue.put(alert)
        self.alert_history.append(alert)
        
        return alert
    
    def _process_alerts(self):
        """Background thread to process alerts"""
        while True:
            try:
                alert = self.alert_queue.get(timeout=1)
                self._dispatch_alert(alert)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing alert: {e}")
    
    def _dispatch_alert(self, alert):
        """Dispatch alert to all configured channels"""
        severity = AlertSeverity[alert['severity']] if isinstance(alert['severity'], str) else alert['severity']
        
        # Critical and High alerts go to all channels
        if severity.value >= AlertSeverity.HIGH.value:
            self._send_email_alert(alert)
            self._send_slack_alert(alert)
            self._send_teams_alert(alert)
        
        # Medium alerts go to Slack and Teams
        elif severity.value >= AlertSeverity.MEDIUM.value:
            self._send_slack_alert(alert)
            self._send_teams_alert(alert)
        
        # Low and Info alerts logged only
        print(f"[{alert['severity']}] {alert['title']}: {alert['message']}")
    
    def _send_email_alert(self, alert):
        """Send alert via email"""
        if not self.email_config['username']:
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert['severity']}] {alert['title']}"
            msg['From'] = self.email_config['from_email']
            msg['To'] = os.getenv('ALERT_EMAIL_TO', 'admin@example.com')
            
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: {self._get_severity_color(alert['severity'])}; padding: 20px; color: white;">
                    <h1>{alert['title']}</h1>
                </div>
                <div style="padding: 20px;">
                    <p><strong>Severity:</strong> {alert['severity']}</p>
                    <p><strong>Source:</strong> {alert['source']}</p>
                    <p><strong>Time:</strong> {alert['timestamp']}</p>
                    <hr>
                    <p>{alert['message']}</p>
                    <hr>
                    <h3>Metadata</h3>
                    <pre>{json.dumps(alert['metadata'], indent=2)}</pre>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            print(f"Email alert sent: {alert['title']}")
            
        except Exception as e:
            print(f"Failed to send email alert: {e}")
    
    def _send_slack_alert(self, alert):
        """Send alert to Slack"""
        if not self.slack_webhook:
            return
        
        try:
            color = self._get_severity_color(alert['severity'])
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"íº¨ {alert['title']}",
                    "text": alert['message'],
                    "fields": [
                        {"title": "Severity", "value": alert['severity'], "short": True},
                        {"title": "Source", "value": alert['source'], "short": True},
                        {"title": "Time", "value": alert['timestamp'], "short": True},
                        {"title": "Alert ID", "value": alert['id'], "short": True}
                    ],
                    "footer": "FortifAI Security System"
                }]
            }
            
            response = requests.post(self.slack_webhook, json=payload)
            
            if response.status_code == 200:
                print(f"Slack alert sent: {alert['title']}")
            
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
    
    def _send_teams_alert(self, alert):
        """Send alert to Microsoft Teams"""
        if not self.teams_webhook:
            return
        
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_severity_color(alert['severity']).replace('#', ''),
                "summary": alert['title'],
                "sections": [{
                    "activityTitle": f"íº¨ {alert['title']}",
                    "facts": [
                        {"name": "Severity", "value": alert['severity']},
                        {"name": "Source", "value": alert['source']},
                        {"name": "Time", "value": alert['timestamp']},
                        {"name": "Alert ID", "value": alert['id']}
                    ],
                    "text": alert['message']
                }]
            }
            
            response = requests.post(self.teams_webhook, json=payload)
            
            if response.status_code == 200:
                print(f"Teams alert sent: {alert['title']}")
            
        except Exception as e:
            print(f"Failed to send Teams alert: {e}")
    
    def _get_severity_color(self, severity):
        """Get color for severity level"""
        colors = {
            'CRITICAL': '#e63946',
            'HIGH': '#f4a261',
            'MEDIUM': '#f9c74f',
            'LOW': '#90be6d',
            'INFO': '#43aa8b'
        }
        return colors.get(severity, '#4f5d75')
    
    def acknowledge_alert(self, alert_id):
        """Acknowledge an alert"""
        for alert in self.alert_history:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                return alert
        return None
    
    def resolve_alert(self, alert_id, resolution_notes=""):
        """Resolve an alert"""
        for alert in self.alert_history:
            if alert['id'] == alert_id:
                alert['resolved'] = True
                alert['resolved_at'] = datetime.now().isoformat()
                alert['resolution_notes'] = resolution_notes
                return alert
        return None
    
    def get_active_alerts(self):
        """Get all unresolved alerts"""
        return [a for a in self.alert_history if not a['resolved']]
    
    def get_alerts_by_severity(self, severity):
        """Get alerts by severity"""
        return [a for a in self.alert_history if a['severity'] == severity]
    
    def get_alert_statistics(self):
        """Get alert statistics"""
        total = len(self.alert_history)
        
        by_severity = {}
        for sev in AlertSeverity:
            by_severity[sev.name] = len([a for a in self.alert_history if a['severity'] == sev.name])
        
        return {
            'total': total,
            'active': len(self.get_active_alerts()),
            'resolved': len([a for a in self.alert_history if a['resolved']]),
            'by_severity': by_severity,
            'last_24h': len([a for a in self.alert_history 
                           if datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=24)])
        }
