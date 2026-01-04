# FortifAI Security Platform
## AI-Powered Cybersecurity Threat Detection and Reconnaissance System

**Project Report**

---

## 1. Executive Summary

FortifAI is a comprehensive, AI-powered cybersecurity platform designed to detect, analyze, and respond to security threats in real-time. The platform integrates advanced machine learning algorithms with robust reconnaissance capabilities to provide organizations with a complete security monitoring and threat intelligence solution.

The system combines two powerful components:
- **FortifAI Core**: Real-time threat detection using machine learning, user behavior analytics, and automated alerting
- **SubVeil Scanner**: External reconnaissance and security assessment module for URL analysis, SSL verification, and vulnerability scanning

This unified platform enables security teams to both monitor internal threats and assess external attack surfaces from a single dashboard.

---

## 2. System Architecture

### 2.1 High-Level Architecture

The platform follows a microservices architecture, ensuring scalability, maintainability, and fault isolation:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                                │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │              Next.js Dashboard (Port 3000)                   │   │
│   │    • Security Overview    • Scanner Interface                │   │
│   │    • Threat Management    • Alert Center                     │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │              FastAPI REST API (Port 8000)                    │   │
│   │    /api/v1/scanner  │  /api/v1/threats  │  /api/v1/alerts   │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   ML Engine   │          │ Alert Service │          │ Auth Service  │
│  (Port 5000)  │          │  (Port 5001)  │          │  (Port 5002)  │
│               │          │               │          │               │
│ • Anomaly Det │          │ • Email/Slack │          │ • JWT Auth    │
│ • Threat Class│          │ • Teams Notif │          │ • RBAC        │
│ • Behavior AI │          │ • Escalation  │          │ • Sessions    │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    ▼
              ┌─────────────────────────────────────────┐
              │         Data Layer                       │
              │   PostgreSQL (5432)  │  Redis (6379)    │
              └─────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14, React, TypeScript, Tailwind CSS | User interface and visualization |
| API Gateway | FastAPI, Python 3.11, Pydantic | RESTful API and request handling |
| ML Engine | scikit-learn, TensorFlow, NumPy | Threat classification and anomaly detection |
| Database | PostgreSQL 15 | Persistent data storage |
| Cache | Redis 7 | Session management and real-time data |
| Container | Docker, Docker Compose | Deployment and orchestration |

---

## 3. Core Features

### 3.1 Threat Detection Module

The ML-powered threat detection system provides:

- **Real-time Threat Classification**: Identifies malware, ransomware, DDoS attacks, phishing attempts, and insider threats with confidence scoring
- **Anomaly Detection**: Uses isolation forests and autoencoders to detect unusual patterns in network traffic and user behavior
- **User Behavior Analytics (UEBA)**: Establishes behavioral baselines and detects deviations indicating compromised accounts

### 3.2 Scanner Module (SubVeil Integration)

The integrated reconnaissance scanner provides external security assessment:

| Feature | Description |
|---------|-------------|
| **URL Extraction** | Parses URLs to extract protocol, domain, subdomain, TLD, path, and query parameters |
| **WHOIS Intelligence** | Retrieves domain registration data, age, and calculates trust scores |
| **SSL/TLS Analysis** | Validates certificates, checks expiration, and verifies certificate chains |
| **Security Headers** | Audits HTTP security headers (HSTS, CSP, X-Frame-Options, etc.) |
| **Port Scanning** | Identifies open ports and running services on target hosts |
| **Technology Detection** | Fingerprints web servers, CMS platforms, frameworks, and JavaScript libraries |
| **DNS Analysis** | Retrieves A, AAAA, MX, NS, and TXT records |

### 3.3 Alert Management

- Multi-channel notifications (Email, Slack, Microsoft Teams)
- Severity-based prioritization (Critical, High, Medium, Low)
- Alert acknowledgment and resolution tracking
- Automated escalation workflows

### 3.4 Security Dashboard

The React-based dashboard provides:
- Real-time security metrics and KPIs
- Interactive threat visualization
- Scanner interface for on-demand security assessments
- User and role management
- Historical analytics and reporting

---

## 4. API Endpoints

### 4.1 Scanner API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scanner/extract` | POST | Extract URL components and WHOIS data |
| `/api/v1/scanner/deep-scan` | POST | Comprehensive security scan with scoring |
| `/api/v1/scanner/quick-scan` | POST | Fast SSL and headers check |
| `/api/v1/scanner/analyze-pcap` | POST | Network traffic analysis from PCAP files |
| `/api/v1/scanner/capabilities` | GET | List available scanner features |

### 4.2 Core Security API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/threats` | GET/POST | Threat management |
| `/api/v1/alerts` | GET/POST/PATCH | Alert handling |
| `/api/v1/analytics/dashboard` | GET | Security metrics |
| `/api/v1/auth/token` | POST | Authentication |

---

## 5. Deployment

### 5.1 Docker Deployment

The platform is fully containerized with 8 microservices:

```bash
# Start all services
cd infrastructure/docker
docker-compose up -d

# Services started:
# - fortifai-api (8000)
# - fortifai-dashboard (3000)
# - fortifai-ml (5000)
# - fortifai-alerts (5001)
# - fortifai-auth (5002)
# - fortifai-collector
# - fortifai-postgres (5432)
# - fortifai-redis (6379)
```

### 5.2 System Requirements

- Docker 20.10+ and Docker Compose 2.0+
- Minimum 4GB RAM, 2 CPU cores
- 10GB disk space for containers and data

---

## 6. Security Scoring Methodology

The scanner calculates security grades (A+ to F) based on:

| Category | Weight | Criteria |
|----------|--------|----------|
| SSL/TLS | 35% | Valid certificate, expiration, protocol version |
| Security Headers | 25% | Presence of HSTS, CSP, X-Frame-Options, etc. |
| Port Security | 15% | Absence of risky open ports (FTP, Telnet, RDP) |
| HTTPS Enforcement | 15% | HTTP to HTTPS redirect implementation |
| Technology | 10% | CDN usage, server disclosure |

---

## 7. Conclusion

FortifAI represents a unified approach to cybersecurity, combining internal threat monitoring with external reconnaissance capabilities. The integration of SubVeil's scanning technology with FortifAI's ML-powered threat detection creates a comprehensive security platform suitable for:

- **Security Operations Centers (SOCs)**: Real-time monitoring and incident response
- **Penetration Testers**: Reconnaissance and vulnerability assessment
- **IT Administrators**: Infrastructure security auditing
- **Compliance Teams**: Security posture verification

The microservices architecture ensures the platform can scale to meet enterprise demands while maintaining reliability and performance. With Docker-based deployment, organizations can quickly implement a complete security monitoring solution.

---

**Project Repository Structure**
```
FortifAI-V2/
├── backend/
│   ├── api/              # FastAPI + Scanner Module
│   ├── ml-engine/        # Machine Learning Models
│   ├── alert-service/    # Notification Service
│   ├── auth-service/     # Authentication
│   └── data-collector/   # Log Collection
├── frontend/
│   └── dashboard/        # Next.js Dashboard
├── infrastructure/
│   ├── docker/           # Docker Compose
│   └── kubernetes/       # K8s Deployments
├── ml-models/            # Trained ML Models
├── docs/                 # Documentation
└── tests/                # Test Suites
```

---

*Report Generated: January 4, 2026*
*Platform Version: 1.0.0*
