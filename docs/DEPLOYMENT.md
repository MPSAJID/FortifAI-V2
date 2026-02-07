# FortifAI Deployment Guide

## Docker Deployment

### Prerequisites

- Docker 24.0+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB disk space

### Quick Start

1. **Configure Environment**

```bash
cd infrastructure/docker
cp .env.example .env
# Edit .env with your settings
```

**Required Environment Variables:**

```bash
# Database
DATABASE_URL=postgresql://fortifai:fortifai_secure_password@postgres:5432/fortifai_db

# Redis
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-super-secret-key-change-in-production
INTERNAL_API_KEY=fortifai-internal-service-key

# Email Notifications (SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
ALERT_EMAIL_TO=recipient@example.com

# Slack Notifications (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Microsoft Teams Notifications (Optional)
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/YOUR/WEBHOOK/URL
```

**Setting up Gmail for SMTP:**

1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account > Security > App passwords
3. Generate a new app password for "Mail"
4. Use the 16-character password (without spaces) as `SMTP_PASSWORD`
5. Set `SMTP_USERNAME` to your Gmail address

2. **Start Services**

```bash
docker-compose up -d
```

3. **Verify Deployment**

```bash
docker-compose ps
docker-compose logs -f api
```

4. **Access Services**

- Dashboard: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.28+
- kubectl configured
- Helm 3.0+ (optional)

### Deploy

1. **Create Namespace**

```bash
kubectl create namespace fortifai
```

2. **Apply Configurations**

```bash
cd infrastructure/kubernetes

# Create secrets
kubectl apply -f configmap.yaml -n fortifai

# Deploy services
kubectl apply -f api-deployment.yaml -n fortifai
kubectl apply -f ml-engine-deployment.yaml -n fortifai

# Configure ingress
kubectl apply -f ingress.yaml -n fortifai
```

3. **Verify Deployment**

```bash
kubectl get pods -n fortifai
kubectl get services -n fortifai
```

## AWS Deployment with Terraform

### Prerequisites

- AWS CLI configured
- Terraform 1.0+
- S3 bucket for state (optional)

### Deploy

1. **Initialize Terraform**

```bash
cd infrastructure/terraform
terraform init
```

2. **Review Plan**

```bash
terraform plan -var="environment=production"
```

3. **Apply Infrastructure**

```bash
terraform apply -var="environment=production"
```

## Production Checklist

### Security

- [ ] Change default admin password
- [ ] Generate new SECRET_KEY
- [ ] Configure HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Enable audit logging

### Performance

- [ ] Configure resource limits
- [ ] Set up horizontal pod autoscaling
- [ ] Configure database connection pooling
- [ ] Enable Redis caching

### Monitoring

- [ ] Set up Prometheus metrics
- [ ] Configure Grafana dashboards
- [ ] Enable log aggregation
- [ ] Configure alert notifications

### Backup

- [ ] Configure database backups
- [ ] Set up disaster recovery
- [ ] Test restore procedures

## Troubleshooting

### Email Notifications Not Working

**Check SMTP configuration:**
```bash
docker exec fortifai-alerts env | grep SMTP
```

**Test SMTP connection:**
```bash
curl -X POST http://localhost:5001/api/test-smtp
```

**Common issues:**
- Gmail blocking: Use App Password, not regular password
- Firewall: Ensure port 587 (SMTP) is allowed
- Missing `ALERT_EMAIL_TO`: Must be set in docker-compose.yml
- Check spam folder for test emails

### Database Connection Errors

**Issue**: `database "fortifai_db" does not exist`

**Solution:**
```bash
cd infrastructure/docker
docker-compose down
docker volume rm docker_postgres_data
docker-compose up -d
```

### ML Engine Feature Extraction Errors

**Issue**: KeyError on feature names

**Solution**: Ensure feature names in `threat_classifier.py` match trained model:
- Use `process_name_length` not `name_length`
- Use `cmdline_length` not `cmd_length`
- Include all 22 required features

### Docker Networking Issues

**Issue**: Services can't communicate

**Solution**: Use service names in URLs, not `localhost`:
- ✓ `postgresql://fortifai:password@postgres:5432/fortifai_db`
- ✗ `postgresql://fortifai:password@localhost:5432/fortifai_db`

### Container Logs

```bash
# View all service logs
docker-compose logs -f

# View specific service
docker logs fortifai-api -f
docker logs fortifai-ml -f
docker logs fortifai-alerts -f
```
