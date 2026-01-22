"""Unit tests for validators."""

import pytest

from app.utils.validators import validate_sensor_reading, sanitize_input


class TestValidateSensorReading:
    """Tests for validate_sensor_reading function."""

    def test_valid_temperature_reading(self):
        """Test valid temperature reading."""
        result = validate_sensor_reading("temperature", 25.5)
        assert result["valid"] is True
        assert result["quality"] == "good"
        assert len(result["errors"]) == 0

    def test_temperature_below_minimum(self):
        """Test temperature below valid range."""
        result = validate_sensor_reading("temperature", -50)
        assert result["valid"] is False
        assert result["quality"] == "error"
        assert len(result["errors"]) > 0

    def test_temperature_above_maximum(self):
        """Test temperature above valid range."""
        result = validate_sensor_reading("temperature", 70)
        assert result["valid"] is False
        assert result["quality"] == "error"

    def test_valid_soil_moisture(self):
        """Test valid soil moisture reading."""
        result = validate_sensor_reading("soil_moisture", 45.0)
        assert result["valid"] is True
        assert result["quality"] == "good"

    def test_soil_moisture_boundary(self):
        """Test soil moisture near boundary."""
        result = validate_sensor_reading("soil_moisture", 95.0)
        assert result["valid"] is True
        assert result["quality"] == "warning"

    def test_valid_humidity(self):
        """Test valid humidity reading."""
        result = validate_sensor_reading("humidity", 60.0)
        assert result["valid"] is True

    def test_valid_light(self):
        """Test valid light reading."""
        result = validate_sensor_reading("light", 5000)
        assert result["valid"] is True

    def test_valid_ph(self):
        """Test valid pH reading."""
        result = validate_sensor_reading("ph", 7.0)
        assert result["valid"] is True

    def test_unknown_sensor_type(self):
        """Test unknown sensor type."""
        result = validate_sensor_reading("unknown_type", 50)
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

    def test_unit_mismatch_warning(self):
        """Test unit mismatch warning."""
        result = validate_sensor_reading("temperature", 25, "fahrenheit")
        assert result["valid"] is True
        assert len(result["warnings"]) > 0


class TestSanitizeInput:
    """Tests for sanitize_input function."""

    def test_normal_string(self):
        """Test normal string sanitization."""
        result = sanitize_input("Hello World")
        assert result == "Hello World"

    def test_string_with_control_characters(self):
        """Test removal of control characters."""
        result = sanitize_input("Hello\x00World\x1f")
        assert result == "HelloWorld"

    def test_max_length_truncation(self):
        """Test max length truncation."""
        result = sanitize_input("A" * 300, max_length=100)
        assert len(result) == 100

    def test_empty_string(self):
        """Test empty string."""
        result = sanitize_input("")
        assert result == ""

    def test_none_value(self):
        """Test None value."""
        result = sanitize_input(None)
        assert result == ""
