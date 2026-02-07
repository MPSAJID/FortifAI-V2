# FortifAI Development Guide

## Setting Up Development Environment

### Python Backend

1. **Create Virtual Environment**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Run Services**

```bash
# API
cd backend/api
uvicorn main:app --reload --port 8000

# ML Engine
cd backend/ml-engine
python main.py

# Alert Service
cd backend/alert-service
uvicorn main:app --reload --port 5001
```

### Docker Development with Live Reload

For development with Docker and live code reloading:

**docker-compose.yml configuration:**
```yaml
services:
  api:
    volumes:
      - ../../backend/api:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
  
  ml-engine:
    volumes:
      - ../../backend/ml-engine:/app
  
  alert-service:
    volumes:
      - ../../backend/alert-service:/app
    command: uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

This allows editing code on your host machine while services run in Docker with automatic reloading.

### Frontend

1. **Install Dependencies**

```bash
cd frontend/dashboard
npm install
```

2. **Run Development Server**

```bash
npm run dev
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Format with Black
- Lint with Flake8

```bash
black backend/
flake8 backend/
```

### TypeScript/React

- Follow ESLint rules
- Use Prettier for formatting

```bash
npm run lint
npm run format
```

## Testing

### Run Tests

```bash
# Python tests
pytest tests/ -v --cov=backend

# Frontend tests
cd frontend/dashboard
npm test
```

### Writing Tests

See `tests/` directory for examples.

## Debugging

### Print Debugging in Docker

Add print statements or logging:
```python
print(f"[DEBUG] Variable value: {my_var}")
import traceback
traceback.print_exc()
```

View output:
```bash
docker logs fortifai-api -f
```

### Testing Email Notifications

```bash
# Test SMTP connection
curl -X POST http://localhost:5001/api/test-smtp

# Create test critical alert
curl -X POST http://localhost:5001/api/notify \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Alert",
    "message": "Testing email delivery",
    "severity": "CRITICAL",
    "source": "test",
    "metadata": {}
  }'
```

### Common Development Issues

**Module not found errors:**
```bash
# Rebuild Docker images
docker-compose build --no-cache
docker-compose up -d
```

**Database schema changes:**
```bash
# Drop and recreate database
docker-compose down
docker volume rm docker_postgres_data
docker-compose up -d
```

**Port conflicts:**
```bash
# Check what's using the port
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request
