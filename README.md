# FortifAI Security Platform

AI-Powered Cybersecurity Threat Detection and Response System with Integrated Reconnaissance

## Overview

FortifAI is a comprehensive security platform that uses machine learning to detect and respond to cybersecurity threats in real-time. The platform now includes **SubVeil** reconnaissance capabilities for external target scanning and security assessment.

## Features

### Core Security Features
- **Threat Detection**: ML-powered threat classification with support for malware, ransomware, DDoS, and more
- **User Behavior Analytics (UEBA)**: Detect insider threats and compromised accounts
- **Anomaly Detection**: Identify unusual patterns in system and network activity
- **Real-time Alerts**: Multi-channel notifications (Email, Slack, Teams)
- **Security Dashboard**: React-based visualization of security metrics
- **RESTful API**: Full API access for integration with existing tools

### Scanner Module (Integrated from SubVeil)
- **URL Information Extraction**: Parse and analyze URLs with WHOIS lookup and domain intelligence
- **Deep Security Scanning**: Comprehensive security analysis including:
  - SSL/TLS certificate analysis
  - Security headers check (HSTS, CSP, X-Frame-Options, etc.)
  - DNS records lookup
  - Technology detection (CMS, frameworks, libraries)
  - Port scanning
  - Redirect chain analysis
  - Security scoring and grading
- **Network Analysis**: PCAP file parsing and traffic analysis
- **Trust Score Calculation**: Domain reputation and risk assessment

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │   Dashboard (React) │  │   Admin Panel       │              │
│  └─────────────────────┘  └─────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ /api/v1/scanner  - URL Scanning & Reconnaissance         │  │
│  │ /api/v1/threats  - Threat Management                     │  │
│  │ /api/v1/alerts   - Alert Management                      │  │
│  │ /api/v1/analytics - Security Analytics                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   ML Engine     │  │  Alert Service  │  │  Auth Service   │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
        ┌─────────────────────────────────────────┐
        │         PostgreSQL + Redis              │
        └─────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+

### Running with Docker

```bash
# Clone and navigate to project
cd FortifAI-V2

# Copy environment file
cp infrastructure/docker/.env.example infrastructure/docker/.env

# Start all services
cd infrastructure/docker
docker-compose up -d

# Access the dashboard
open http://localhost:3000
```

### Development Setup

```bash
# Backend API
cd backend/api
pip install -r requirements.txt
uvicorn main:app --reload

# ML Engine
cd backend/ml-engine
pip install -r requirements.txt
python main.py

# Frontend
cd frontend/dashboard
npm install
npm run dev
```

## API Documentation

Once running, access the API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Default Credentials

- Username: `admin`
- Password: `admin123`

⚠️ **Change these in production!**

## Project Structure

```
FortifAI-V2/
├── backend/
│   ├── api/                    # FastAPI REST API
│   │   ├── scanner/            # SubVeil Scanner Module
│   │   │   ├── url_extractor.py
│   │   │   ├── deep_scanner.py
│   │   │   └── network_analyzer.py
│   │   ├── routers/            # API Route Handlers
│   │   ├── models/             # Database Models
│   │   ├── schemas/            # Pydantic Schemas
│   │   └── core/               # Core Configuration
│   ├── ml-engine/              # Machine Learning Models
│   ├── data-collector/         # Log & Process Collectors
│   ├── alert-service/          # Alert Management
│   ├── auth-service/           # Authentication
│   └── common/                 # Shared utilities
├── frontend/
│   ├── dashboard/              # Next.js Dashboard
│   │   └── src/app/scanner/    # Scanner Page (SubVeil UI)
│   └── admin-panel/            # Admin Panel
├── ml-models/
│   ├── anomaly-detection/      # Anomaly Detection Models
│   ├── threat-classification/  # Threat Classification
│   └── behavior-analysis/      # User Behavior Analytics
├── infrastructure/
│   ├── docker/                 # Docker configurations
│   ├── kubernetes/             # K8s deployments
│   └── terraform/              # Infrastructure as Code
├── docs/                       # Documentation
├── tests/                      # Test suites
└── scripts/                    # Utility scripts
```

## Scanner API Endpoints

The integrated SubVeil scanner provides these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/scanner/extract` | POST | Extract URL information and WHOIS data |
| `/api/v1/scanner/extract-batch` | POST | Batch URL extraction |
| `/api/v1/scanner/deep-scan` | POST | Comprehensive security scan |
| `/api/v1/scanner/quick-scan` | POST | Quick SSL and headers check |
| `/api/v1/scanner/analyze-pcap` | POST | Analyze PCAP network captures |
| `/api/v1/scanner/capabilities` | GET | List scanner capabilities |

## License

MIT License - See LICENSE file for details.
