"""Data validation utilities."""

from typing import Any, Optional

# Valid ranges for different sensor types
SENSOR_RANGES = {
    "temperature": {"min": -40, "max": 60, "unit": "celsius"},
    "soil_moisture": {"min": 0, "max": 100, "unit": "percent"},
    "humidity": {"min": 0, "max": 100, "unit": "percent"},
    "light": {"min": 0, "max": 100000, "unit": "lux"},
    "ph": {"min": 0, "max": 14, "unit": "pH"},
    "nitrogen": {"min": 0, "max": 500, "unit": "mg/kg"},
    "phosphorus": {"min": 0, "max": 500, "unit": "mg/kg"},
    "potassium": {"min": 0, "max": 500, "unit": "mg/kg"},
}


def validate_sensor_reading(
    sensor_type: str,
    value: float,
    unit: Optional[str] = None,
) -> dict[str, Any]:
    """Validate a sensor reading against expected ranges.

    Args:
        sensor_type: Type of sensor
        value: Reading value
        unit: Optional unit to validate

    Returns:
        Validation result with quality assessment
    """
    result = {
        "valid": True,
        "quality": "good",
        "warnings": [],
        "errors": [],
    }

    sensor_type_lower = sensor_type.lower()
    if sensor_type_lower not in SENSOR_RANGES:
        result["warnings"].append(f"Unknown sensor type: {sensor_type}")
        return result

    range_info = SENSOR_RANGES[sensor_type_lower]

    # Check value range
    if value < range_info["min"]:
        result["valid"] = False
        result["quality"] = "error"
        result["errors"].append(
            f"Value {value} below minimum {range_info['min']} for {sensor_type}"
        )
    elif value > range_info["max"]:
        result["valid"] = False
        result["quality"] = "error"
        result["errors"].append(
            f"Value {value} above maximum {range_info['max']} for {sensor_type}"
        )
    elif value < range_info["min"] * 1.1 or value > range_info["max"] * 0.9:
        result["quality"] = "warning"
        result["warnings"].append(f"Value {value} near boundary for {sensor_type}")

    # Check unit if provided
    if unit and unit.lower() != range_info["unit"]:
        result["warnings"].append(
            f"Unexpected unit '{unit}', expected '{range_info['unit']}'"
        )

    return result


def sanitize_input(value: str, max_length: int = 255) -> str:
    """Sanitize string input.

    Args:
        value: Input string
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Remove control characters
    sanitized = "".join(c for c in value if c.isprintable())

    # Truncate to max length
    return sanitized[:max_length]
