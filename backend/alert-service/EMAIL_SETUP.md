# Email Alerting Configuration

## Overview
The FortifAI alert service automatically sends email notifications for **CRITICAL** alerts. This includes alerts triggered by threat detection, security incidents, and other critical events.

## Setup Instructions

### 1. Environment Variables
Configure the following in your `.env` or `infrastructure/docker/.env` file:

```env
# Email Configuration (SMTP)
SMTP_SERVER=smtp.gmail.com          # Your SMTP server
SMTP_PORT=587                        # SMTP port (usually 587 for TLS)
SMTP_USERNAME=your-email@gmail.com  # Email account for sending alerts
SMTP_PASSWORD=your-app-password     # App-specific password (see below)
FROM_EMAIL=your-email@gmail.com     # From address for alert emails
ALERT_EMAIL_TO=recipient@domain.com # Email address to receive alerts

# Optional: Slack & Teams webhooks (for multi-channel alerting)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/...
```

### 2. Gmail Setup (Recommended)
If using Gmail as your SMTP provider:

1. **Enable 2FA** on your Google Account (required for app passwords)
2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer"
   - Google will generate a 16-character password
   - Use this as `SMTP_PASSWORD`

3. **Set environment variables**:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password
   FROM_EMAIL=your-email@gmail.com
   ALERT_EMAIL_TO=admin@yourcompany.com
   ```

### 3. Other Email Providers
| Provider | SMTP Server | Port |
|----------|-------------|------|
| Gmail | smtp.gmail.com | 587 (TLS) |
| Office 365 | smtp.office365.com | 587 (TLS) |
| SendGrid | smtp.sendgrid.net | 587 |
| AWS SES | email-smtp.region.amazonaws.com | 587 |
| Custom | your-smtp.server.com | 587 |

## Alert Flow

```
Threat Detected
    ↓
ML Engine (analyze/batch)
    ↓
simulate_threats.py creates alert via /api/v1/alerts/internal
    ↓
API Router (alerts.py) saves alert to DB
    ↓
notify_critical_alert() checks severity
    ↓
IF severity == CRITICAL:
    ├─ Email notification (via alert-service)
    ├─ Slack notification (if configured)
    └─ Teams notification (if configured)
```

## Alert Severity Mapping

Emails are sent for **CRITICAL** alerts. The following threat classifications trigger CRITICAL severity:

- **Ransomware Detection** → CRITICAL
- **Malware Detection** → CRITICAL
- **Data Exfiltration** → CRITICAL
- **Credential Dumping** → CRITICAL
- **DDoS Attack** → HIGH (email not sent)
- **Brute Force Attack** → HIGH (email not sent)

## Email Template

Critical alerts will be formatted as:

```
Subject: [CRITICAL] Ransomware Detected: cryptolocker.exe

Alert: Ransomware Detected: cryptolocker.exe
Severity: CRITICAL
Source: threat_simulation
Time: 2026-01-15T21:38:14.123456

Suspicious process 'cryptolocker.exe' detected with 98.5% confidence.
Classification: ransomware. Risk Score: 0.95
```

## Testing Email Configuration

### 1. Test Alert via curl:
```bash
curl -X POST http://localhost:8000/api/v1/alerts/internal \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: fortifai-internal-service-key" \
  -d '{
    "title": "Test Critical Alert",
    "message": "This is a test email alert",
    "severity": "CRITICAL",
    "source": "test_email",
    "metadata": {"test": true}
  }'
```

### 2. Trigger via Threat Simulation:
```bash
cd scripts
python simulate_threats.py --attack ransomware --duration 5 --skip-check
```

This will create a CRITICAL alert and send an email.

### 3. Check Docker logs:
```bash
docker logs fortifai-alerts | grep -i "email"
```

## Troubleshooting

### Email not sending?

1. **Check Alert Severity**:
   ```bash
   curl http://localhost:8000/api/v1/alerts?limit=5 \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
   Look for alerts with `"severity": "CRITICAL"`

2. **Check Alert Service Logs**:
   ```bash
   docker logs fortifai-alerts
   ```
   Look for `Email alert failed:` messages

3. **Test SMTP Configuration**:
   ```python
   import smtplib
   
   smtp_server = "smtp.gmail.com"
   smtp_port = 587
   username = "your-email@gmail.com"
   password = "your-app-password"
   
   try:
       server = smtplib.SMTP(smtp_server, smtp_port)
       server.starttls()
       server.login(username, password)
       print("✓ SMTP connection successful")
       server.quit()
   except Exception as e:
       print(f"✗ SMTP connection failed: {e}")
   ```

4. **Check Environment Variables**:
   ```bash
   docker exec fortifai-alerts env | grep SMTP
   docker exec fortifai-alerts env | grep EMAIL
   ```

5. **Verify Recipient Email**:
   Ensure `ALERT_EMAIL_TO` is set and valid

## Multi-Channel Alerting

In addition to email, configure webhooks for other channels:

### Slack
1. Create Slack App: https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Create webhook URL and add to `.env`:
   ```env
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

### Microsoft Teams
1. Get Teams webhook URL from connectors
2. Add to `.env`:
   ```env
   TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/...
   ```

## API Endpoints

### Check Alert Status
```bash
curl -X GET http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Alert Statistics
```bash
curl -X GET http://localhost:8000/api/v1/alerts/stats/summary \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Disabling Email Alerts

To disable email alerts, simply don't set the `SMTP_USERNAME` or `SMTP_PASSWORD` environment variables. The system will skip email notification gracefully.
