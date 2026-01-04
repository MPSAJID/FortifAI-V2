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
