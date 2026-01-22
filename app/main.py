"""FastAPI application for BigchainDB Agri Backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import auth, farms, fields, sensors, measurements, analytics

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.app_name}...")
    yield
    # Shutdown
    print(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    description="RESTful API for agricultural sensor data management using BigchainDB",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(farms.router, prefix="/api/v1/farms", tags=["Farms"])
app.include_router(fields.router, prefix="/api/v1/fields", tags=["Fields"])
app.include_router(sensors.router, prefix="/api/v1/sensors", tags=["Sensors"])
app.include_router(measurements.router, prefix="/api/v1/measurements", tags=["Measurements"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "documentation": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
