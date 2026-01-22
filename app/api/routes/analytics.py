"""Analytics routes for data aggregation and reporting."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.routes.auth import User, get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter()


def get_analytics_service() -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService()


@router.get("/dashboard")
async def get_dashboard(
    farm_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get dashboard summary statistics."""
    return analytics_service.get_dashboard_summary(farm_id=farm_id)


@router.get("/timeseries/{sensor_id}")
async def get_timeseries(
    sensor_id: str,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    interval: str = Query("hour", regex="^(hour|day|week)$"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get time series data for a sensor."""
    return analytics_service.get_timeseries_data(
        sensor_id=sensor_id,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
    )


@router.get("/aggregations")
async def get_aggregations(
    farm_id: Optional[str] = None,
    field_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Get aggregated statistics by sensor type."""
    return analytics_service.get_aggregations(
        farm_id=farm_id,
        field_id=field_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/export")
async def export_data(
    farm_id: Optional[str] = None,
    field_id: Optional[str] = None,
    sensor_id: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
):
    """Export measurement data in JSON or CSV format."""
    from app.api.routes.measurements import measurements_db
    from app.api.routes.sensors import sensors_db
    from app.api.routes.farms import farms_db

    filtered = []
    for m in measurements_db:
        sensor = sensors_db.get(m.get("internal_sensor_id"))
        if not sensor:
            continue

        farm = farms_db.get(sensor.get("farm_id"))
        if not farm or farm.get("owner_email") != current_user.email:
            continue

        if sensor_id and m.get("sensor_id") != sensor_id:
            continue
        if field_id and sensor.get("field_id") != field_id:
            continue
        if farm_id and sensor.get("farm_id") != farm_id:
            continue

        m_time = datetime.fromisoformat(m.get("timestamp", m.get("created_at")))
        if from_date and m_time < from_date:
            continue
        if to_date and m_time > to_date:
            continue

        filtered.append(m)

    if format == "csv":
        import csv
        import io

        output = io.StringIO()
        if filtered:
            writer = csv.DictWriter(output, fieldnames=filtered[0].keys())
            writer.writeheader()
            writer.writerows(filtered)

        from fastapi.responses import StreamingResponse

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=measurements.csv"},
        )

    return {
        "data": filtered,
        "count": len(filtered),
        "exported_at": datetime.utcnow().isoformat(),
    }
