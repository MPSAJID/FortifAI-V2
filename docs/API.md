# FortifAI API Documentation

## Authentication

All API endpoints (except `/health` and `/docs`) require authentication.

### Obtain Token

```bash
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Use Token

Include the token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Endpoints

### Health Check

```
GET /health
GET /ready
GET /live
```

### Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/alerts` | List all alerts |
| POST | `/api/v1/alerts` | Create new alert |
| GET | `/api/v1/alerts/{id}` | Get alert by ID |
| PATCH | `/api/v1/alerts/{id}` | Update alert |
| GET | `/api/v1/alerts/stats/summary` | Get alert statistics |

### Threats

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/threats` | List detected threats |
| POST | `/api/v1/threats` | Log new threat |
| POST | `/api/v1/threats/analyze` | Analyze log for threats |
| GET | `/api/v1/threats/stats/summary` | Get threat statistics |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard` | Dashboard statistics |
| GET | `/api/v1/analytics/timeline` | Activity timeline |
| GET | `/api/v1/analytics/risk-assessment` | Risk assessment |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users` | List all users (admin/analyst only) |
| GET | `/api/v1/users/me` | Get current user info |
| GET | `/api/v1/users/stats` | Get user statistics |
| GET | `/api/v1/users/count` | Get user count |
| GET | `/api/v1/users/{id}` | Get user by ID |
| POST | `/api/v1/users` | Create new user (admin only) |
| PUT | `/api/v1/users/{id}` | Update user |
| DELETE | `/api/v1/users/{id}` | Delete user (admin only) |
| POST | `/api/v1/users/{id}/activate` | Activate user (admin only) |
| POST | `/api/v1/users/{id}/deactivate` | Deactivate user (admin only) |
| POST | `/api/v1/users/{id}/reset-password` | Reset user password |

## Request/Response Examples

### Create Alert

```bash
POST /api/v1/alerts
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Suspicious Login Detected",
  "message": "Multiple failed login attempts from IP 192.168.1.100",
  "severity": "HIGH",
  "source": "auth-service",
  "metadata": {
    "ip_address": "192.168.1.100",
    "attempts": 5
  }
}
```

### Analyze Threat

```bash
POST /api/v1/threats/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
  "log_data": {
    "process_name": "suspicious.exe",
    "cpu_usage": 95,
    "memory_usage": 2048,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

Response:
```json
{
  "is_threat": true,
  "threat_type": "malware",
  "confidence": 0.87,
  "risk_score": 0.82,
  "classification": "malware",
  "recommendations": [
    "Isolate the affected system immediately",
    "Run full antivirus scan",
    "Check for lateral movement"
  ]
}
```

### Create User (Admin Only)

```bash
POST /api/v1/users
Content-Type: application/json
Authorization: Bearer <token>

{
  "username": "analyst1",
  "email": "analyst1@fortifai.io",
  "password": "SecurePass123!",
  "full_name": "John Analyst",
  "role": "analyst"
}
```

Response:
```json
{
  "id": 2,
  "username": "analyst1",
  "email": "analyst1@fortifai.io",
  "full_name": "John Analyst",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Get User Statistics

```bash
GET /api/v1/users/stats
Authorization: Bearer <token>
```

Response:
```json
{
  "total": 10,
  "active": 8,
  "inactive": 2,
  "by_role": {
    "admin": 2,
    "analyst": 5,
    "viewer": 3
  }
}
```

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message here"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

## Rate Limiting

API requests are rate limited to prevent abuse:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated endpoints

## Pagination

List endpoints support pagination:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 50, max: 100)

Example: `GET /api/v1/alerts?skip=20&limit=10`
