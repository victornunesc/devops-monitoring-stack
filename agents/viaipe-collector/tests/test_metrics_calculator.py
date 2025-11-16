"""
Tests for metrics calculator
"""
import pytest

from src.metrics.metrics_calculator import MetricsCalculator


class TestMetricsCalculator:
    """Test suite for MetricsCalculator"""

    @pytest.fixture
    def calculator(self):
        """Create a metrics calculator instance"""
        return MetricsCalculator()

    # Tests for calculate_availability
    def test_calculate_availability_zero_loss(self, calculator):
        """Test availability calculation with zero packet loss"""
        smoke_data = {"avg_loss": 0}
        result = calculator.calculate_availability(smoke_data)
        assert result == 100.0

    def test_calculate_availability_partial_loss(self, calculator):
        """Test availability calculation with partial packet loss"""
        smoke_data = {"avg_loss": 5.5}
        result = calculator.calculate_availability(smoke_data)
        assert result == 94.5

    def test_calculate_availability_full_loss(self, calculator):
        """Test availability calculation with 100% packet loss"""
        smoke_data = {"avg_loss": 100}
        result = calculator.calculate_availability(smoke_data)
        assert result == 0.0

    def test_calculate_availability_over_100_loss(self, calculator):
        """Test availability calculation with loss > 100% (clamped to 0)"""
        smoke_data = {"avg_loss": 150}
        result = calculator.calculate_availability(smoke_data)
        assert result == 0.0

    def test_calculate_availability_negative_loss(self, calculator):
        """Test availability calculation with negative loss (clamped to 100)"""
        smoke_data = {"avg_loss": -10}
        result = calculator.calculate_availability(smoke_data)
        assert result == 100.0

    def test_calculate_availability_missing_data(self, calculator):
        """Test availability calculation with missing avg_loss"""
        smoke_data = {}
        result = calculator.calculate_availability(smoke_data)
        assert result == 100.0

    def test_calculate_availability_invalid_data(self, calculator):
        """Test availability calculation with invalid data"""
        smoke_data = {"avg_loss": "invalid"}
        result = calculator.calculate_availability(smoke_data)
        assert result == 0.0

    # Tests for calculate_bandwidth_stats
    def test_calculate_bandwidth_stats_single_interface(self, calculator):
        """Test bandwidth calculation with single interface"""
        interfaces = [
            {
                "avg_in": 1000000,
                "avg_out": 500000,
                "max_in": 2000000,
                "max_out": 1000000
            }
        ]
        result = calculator.calculate_bandwidth_stats(interfaces)
        assert result["avg_in"] == 1000000
        assert result["avg_out"] == 500000
        assert result["max_in"] == 2000000
        assert result["max_out"] == 1000000

    def test_calculate_bandwidth_stats_multiple_interfaces(self, calculator):
        """Test bandwidth calculation with multiple interfaces"""
        interfaces = [
            {
                "avg_in": 1000000,
                "avg_out": 500000,
                "max_in": 2000000,
                "max_out": 1000000
            },
            {
                "avg_in": 500000,
                "avg_out": 250000,
                "max_in": 1000000,
                "max_out": 500000
            }
        ]
        result = calculator.calculate_bandwidth_stats(interfaces)
        assert result["avg_in"] == 1500000
        assert result["avg_out"] == 750000
        assert result["max_in"] == 3000000
        assert result["max_out"] == 1500000

    def test_calculate_bandwidth_stats_empty_interfaces(self, calculator):
        """Test bandwidth calculation with empty interfaces list"""
        interfaces = []
        result = calculator.calculate_bandwidth_stats(interfaces)
        assert result["avg_in"] == 0
        assert result["avg_out"] == 0
        assert result["max_in"] == 0
        assert result["max_out"] == 0

    def test_calculate_bandwidth_stats_missing_fields(self, calculator):
        """Test bandwidth calculation with missing fields"""
        interfaces = [
            {
                "avg_in": 1000000
                # missing other fields
            }
        ]
        result = calculator.calculate_bandwidth_stats(interfaces)
        assert result["avg_in"] == 1000000
        assert result["avg_out"] == 0
        assert result["max_in"] == 0
        assert result["max_out"] == 0

    def test_calculate_bandwidth_stats_invalid_data(self, calculator):
        """Test bandwidth calculation with invalid data"""
        interfaces = [
            {
                "avg_in": "invalid",
                "avg_out": 500000,
                "max_in": 2000000,
                "max_out": 1000000
            }
        ]
        result = calculator.calculate_bandwidth_stats(interfaces)
        assert result == {'avg_in': 0, 'avg_out': 0, 'max_in': 0, 'max_out': 0}

    # Tests for calculate_quality_score
    def test_calculate_quality_score_perfect(self, calculator):
        """Test quality score with perfect conditions"""
        smoke_data = {"val": 10, "loss": 0}
        result = calculator.calculate_quality_score(100.0, smoke_data)
        assert result == 100.0

    def test_calculate_quality_score_good(self, calculator):
        """Test quality score with good conditions"""
        smoke_data = {"val": 30, "loss": 0.5}
        availability = 98.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        # Expected: 98*0.5 + 100*0.3 + 95*0.2 = 49 + 30 + 19 = 98
        assert result == 98.0

    def test_calculate_quality_score_medium_latency(self, calculator):
        """Test quality score with medium latency"""
        smoke_data = {"val": 75, "loss": 0}
        availability = 100.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        # Expected: 100*0.5 + 50*0.3 + 100*0.2 = 50 + 15 + 20 = 85
        assert result == 85.0

    def test_calculate_quality_score_high_latency(self, calculator):
        """Test quality score with high latency"""
        smoke_data = {"val": 150, "loss": 0}
        availability = 100.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        # Latency > 100ms, score should be low or 0
        assert result <= 70.0

    def test_calculate_quality_score_high_loss(self, calculator):
        """Test quality score with high packet loss"""
        smoke_data = {"val": 25, "loss": 5}
        availability = 95.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        # High loss should reduce quality
        assert result < 95.0

    def test_calculate_quality_score_poor_conditions(self, calculator):
        """Test quality score with poor conditions"""
        smoke_data = {"val": 200, "loss": 10}
        availability = 50.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        assert result < 50.0

    def test_calculate_quality_score_missing_data(self, calculator):
        """Test quality score with missing smoke data"""
        smoke_data = {}
        availability = 95.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        # Should handle missing data gracefully
        assert 0 <= result <= 100

    def test_calculate_quality_score_invalid_data(self, calculator):
        """Test quality score with invalid data"""
        smoke_data = {"val": "invalid", "loss": "invalid"}
        availability = 95.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        assert result == 0.0

    def test_calculate_quality_score_clamped_to_100(self, calculator):
        """Test quality score is clamped to 100"""
        smoke_data = {"val": 0, "loss": 0}
        availability = 100.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        assert result <= 100.0

    def test_calculate_quality_score_zero_availability(self, calculator):
        """Test quality score with zero availability"""
        smoke_data = {"val": 25, "loss": 0}
        availability = 0.0
        result = calculator.calculate_quality_score(availability, smoke_data)
        # Score should be low due to 0% availability
        assert result <= 50.0
