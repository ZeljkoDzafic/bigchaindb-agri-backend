"""API routes for the BigchainDB Agri Backend."""

from app.api.routes import auth, farms, fields, sensors, measurements, analytics

__all__ = ["auth", "farms", "fields", "sensors", "measurements", "analytics"]
