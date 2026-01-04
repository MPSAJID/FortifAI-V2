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
python main.py
```

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

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request
