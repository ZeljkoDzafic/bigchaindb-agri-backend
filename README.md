# BigchainDB Agri Backend

RESTful API middleware for precision agriculture using BigchainDB blockchain.

## Overview

This FastAPI backend provides a RESTful interface for managing agricultural sensor data with immutable storage on BigchainDB. It supports farm management, field tracking, sensor registration, and measurement recording with full audit trails.

## Features

- **Farm Management**: Create and manage farms with location tracking
- **Field Management**: Define fields within farms with boundaries
- **Sensor Registration**: Register IoT sensors with Ed25519 cryptographic identity
- **Measurement Recording**: Store sensor readings on BigchainDB blockchain
- **Analytics**: Time-series aggregation and data export
- **Authentication**: JWT-based authentication with secure password hashing
- **Message Queue**: RabbitMQ integration for high-throughput data ingestion

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   IoT Sensors   │────▶│   FastAPI API   │────▶│   BigchainDB    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │    RabbitMQ     │     │    MongoDB      │
                        └─────────────────┘     └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for running dependencies)

### Installation

```bash
# Clone the repository
git clone https://github.com/ZeljkoDzafic/bigchaindb-agri-backend.git
cd bigchaindb-agri-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### Running with Docker

```bash
# Start all services (BigchainDB, MongoDB, RabbitMQ, API)
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Running Locally (Development)

```bash
# Start dependencies
docker-compose up -d mongodb rabbitmq bigchaindb tendermint

# Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Authenticate user |
| `/api/v1/farms` | GET/POST | List/Create farms |
| `/api/v1/fields` | GET/POST | List/Create fields |
| `/api/v1/sensors` | GET/POST | List/Register sensors |
| `/api/v1/measurements` | GET/POST | List/Record measurements |
| `/api/v1/analytics/dashboard` | GET | Dashboard statistics |
| `/api/v1/analytics/timeseries/{sensor_id}` | GET | Time series data |

## Testing

```bash
# Install test dependencies
pip install pytest pytest-mock httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Configuration

Environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `BIGCHAINDB_ROOT_URL` | BigchainDB API URL | `http://localhost:9984` |
| `MONGODB_URL` | MongoDB connection URL | `mongodb://localhost:27017` |
| `RABBITMQ_URL` | RabbitMQ connection URL | `amqp://guest:guest@localhost:5672` |
| `JWT_SECRET_KEY` | Secret for JWT tokens | (required) |

## Project Structure

```
bigchaindb-agri-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── api/
│   │   └── routes/          # API route handlers
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic services
│   └── utils/               # Utility functions
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

MIT License
