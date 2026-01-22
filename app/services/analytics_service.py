"""Analytics service for data aggregation and reporting."""

from datetime import datetime, timedelta
from typing import Any, Optional

from pymongo import MongoClient

from app.config import get_settings

settings = get_settings()


class AnalyticsService:
    """Service for analytics and data aggregation using MongoDB."""

    def __init__(self):
        """Initialize MongoDB connection."""
        self.client = MongoClient(settings.mongodb_url)
        self.db = self.client[settings.mongodb_database]

    def get_dashboard_summary(self, farm_id: Optional[str] = None) -> dict[str, Any]:
        """Get summary statistics for the dashboard.

        Args:
            farm_id: Optional farm ID to filter by

        Returns:
            Dashboard summary statistics
        """
        match_stage = {}
        if farm_id:
            match_stage["asset.data.farm_id"] = farm_id

        # Count active sensors
        sensor_count = self.db.assets.count_documents({
            **match_stage,
            "asset.data.type": "sensor",
        })

        # Count measurements in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        measurement_count = self.db.transactions.count_documents({
            **match_stage,
            "metadata.reading.timestamp": {"$gte": yesterday.isoformat()},
        })

        # Count alerts (measurements outside normal range)
        alert_count = self.db.transactions.count_documents({
            **match_stage,
            "metadata.reading.quality": {"$ne": "good"},
            "metadata.reading.timestamp": {"$gte": yesterday.isoformat()},
        })

        return {
            "active_sensors": sensor_count,
            "measurements_24h": measurement_count,
            "alerts_24h": alert_count,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_timeseries_data(
        self,
        sensor_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        interval: str = "hour",
    ) -> list[dict[str, Any]]:
        """Get time series data for a sensor.

        Args:
            sensor_id: Sensor ID
            from_date: Start date
            to_date: End date
            interval: Aggregation interval (hour, day, week)

        Returns:
            Time series data points
        """
        if from_date is None:
            from_date = datetime.utcnow() - timedelta(days=7)
        if to_date is None:
            to_date = datetime.utcnow()

        # Define date format based on interval
        date_formats = {
            "hour": "%Y-%m-%dT%H:00:00Z",
            "day": "%Y-%m-%d",
            "week": "%Y-W%V",
        }
        date_format = date_formats.get(interval, date_formats["hour"])

        pipeline = [
            {
                "$match": {
                    "asset.data.sensor_id": sensor_id,
                    "metadata.reading.timestamp": {
                        "$gte": from_date.isoformat(),
                        "$lte": to_date.isoformat(),
                    },
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": date_format,
                            "date": {"$toDate": "$metadata.reading.timestamp"},
                        }
                    },
                    "avg_value": {"$avg": "$metadata.reading.value"},
                    "min_value": {"$min": "$metadata.reading.value"},
                    "max_value": {"$max": "$metadata.reading.value"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = list(self.db.transactions.aggregate(pipeline))
        return [
            {
                "timestamp": r["_id"],
                "avg": r["avg_value"],
                "min": r["min_value"],
                "max": r["max_value"],
                "count": r["count"],
            }
            for r in results
        ]

    def get_aggregations(
        self,
        farm_id: Optional[str] = None,
        field_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get aggregated statistics.

        Args:
            farm_id: Optional farm ID filter
            field_id: Optional field ID filter
            from_date: Start date
            to_date: End date

        Returns:
            Aggregated statistics
        """
        match_conditions = {}
        if farm_id:
            match_conditions["asset.data.farm_id"] = farm_id
        if field_id:
            match_conditions["asset.data.field_id"] = field_id
        if from_date:
            match_conditions["metadata.reading.timestamp"] = {"$gte": from_date.isoformat()}
        if to_date:
            if "metadata.reading.timestamp" in match_conditions:
                match_conditions["metadata.reading.timestamp"]["$lte"] = to_date.isoformat()
            else:
                match_conditions["metadata.reading.timestamp"] = {"$lte": to_date.isoformat()}

        pipeline = [
            {"$match": match_conditions},
            {
                "$group": {
                    "_id": "$asset.data.sensor_type",
                    "avg_value": {"$avg": "$metadata.reading.value"},
                    "min_value": {"$min": "$metadata.reading.value"},
                    "max_value": {"$max": "$metadata.reading.value"},
                    "count": {"$sum": 1},
                }
            },
        ]

        results = list(self.db.transactions.aggregate(pipeline))
        return {
            "aggregations": [
                {
                    "sensor_type": r["_id"],
                    "avg": r["avg_value"],
                    "min": r["min_value"],
                    "max": r["max_value"],
                    "count": r["count"],
                }
                for r in results
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def close(self) -> None:
        """Close the MongoDB connection."""
        self.client.close()
