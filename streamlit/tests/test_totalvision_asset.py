"""Unit tests for TotalVision AssetData model and generate_asset_health_data.

Covers:
  - AssetData field defaults, types, and instantiation
  - generate_asset_health_data output shape, ranges, and consistency
  - Backlog field invariants (total ≥ critical + high + medium)
  - Sensor count consistency (healthy + degraded + failed ≤ gates_total)
  - RUL bucket sum matching gates_total
  - Health percentage validity (0–100)
  - Deterministic output for the same station seed
  - Empty / None DataFrame edge case
"""

import os
import sys

# Ensure project root is on the path so we can import from core
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd

from core.totalvision import (
    AssetData,
    _clamp,
    _rng_for,
    generate_asset_health_data,
)

# ═══════════════════════════════════════════════════════════
# AssetData model tests
# ═══════════════════════════════════════════════════════════


class TestAssetDataModel:
    """Validate the AssetData dataclass defaults & field types."""

    def test_default_instantiation(self):
        """AssetData() with no args should use all defaults."""
        ad = AssetData()
        assert ad.station == ""
        assert ad.fleet_rul_pct == 70.0
        assert ad.gates_healthy == 0
        assert ad.gates_total == 0

    def test_backlog_fields_exist_and_default_to_zero(self):
        """All 6 backlog fields should exist and default to 0 / 0.0."""
        ad = AssetData()
        # Integer fields
        assert ad.backlog_total == 0
        assert ad.backlog_critical == 0
        assert ad.backlog_high == 0
        assert ad.backlog_medium == 0
        # Float fields
        assert ad.backlog_avg_days_overdue == 0.0
        assert ad.backlog_trend_pct == 0.0

    def test_health_matrix_fields_exist_and_default_to_zero(self):
        """All 6 asset type health fields should exist and default to 0.0."""
        ad = AssetData()
        assert ad.gate_health_pct == 0.0
        assert ad.sensor_health_pct == 0.0
        assert ad.firmware_compliance_pct == 0.0
        assert ad.structural_health_pct == 0.0
        assert ad.power_system_health_pct == 0.0
        assert ad.communication_health_pct == 0.0

    def test_custom_instantiation(self):
        """All new fields accept explicit values."""
        ad = AssetData(
            station="Test Hbf",
            fleet_rul_pct=50.0,
            gates_healthy=10,
            gates_total=20,
            backlog_total=15,
            backlog_critical=3,
            backlog_high=5,
            backlog_medium=7,
            backlog_avg_days_overdue=12.5,
            backlog_trend_pct=-2.0,
            gate_health_pct=85.0,
            sensor_health_pct=72.0,
            firmware_compliance_pct=90.0,
            structural_health_pct=78.0,
            power_system_health_pct=65.0,
            communication_health_pct=88.0,
        )
        assert ad.station == "Test Hbf"
        assert ad.backlog_total == 15
        assert ad.backlog_critical == 3
        assert ad.backlog_high == 5
        assert ad.backlog_medium == 7
        assert ad.backlog_avg_days_overdue == 12.5
        assert ad.backlog_trend_pct == -2.0
        assert ad.gate_health_pct == 85.0
        assert ad.sensor_health_pct == 72.0
        assert ad.firmware_compliance_pct == 90.0
        assert ad.structural_health_pct == 78.0
        assert ad.power_system_health_pct == 65.0
        assert ad.communication_health_pct == 88.0

    def test_field_types(self):
        """Ensure backlog/health fields are the correct Python types."""
        ad = AssetData(
            backlog_total=10,
            backlog_critical=2,
            backlog_high=3,
            backlog_medium=5,
            backlog_avg_days_overdue=14.0,
            backlog_trend_pct=-1.5,
            gate_health_pct=75.0,
        )
        assert isinstance(ad.backlog_total, int)
        assert isinstance(ad.backlog_critical, int)
        assert isinstance(ad.backlog_high, int)
        assert isinstance(ad.backlog_medium, int)
        assert isinstance(ad.backlog_avg_days_overdue, float)
        assert isinstance(ad.backlog_trend_pct, float)
        assert isinstance(ad.gate_health_pct, float)
        assert isinstance(ad.sensor_health_pct, float)
        assert isinstance(ad.firmware_compliance_pct, float)
        assert isinstance(ad.structural_health_pct, float)
        assert isinstance(ad.power_system_health_pct, float)
        assert isinstance(ad.communication_health_pct, float)


# ═══════════════════════════════════════════════════════════
# generate_asset_health_data function tests
# ═══════════════════════════════════════════════════════════


class TestGenerateAssetHealthData:
    """Tests for the generate_asset_health_data function."""

    def test_returns_asset_data_instance(self):
        """Should return an AssetData dataclass instance."""
        result = generate_asset_health_data("Berlin Hbf")
        assert isinstance(result, AssetData)

    def test_station_name_preserved(self):
        """The station string should be propagated to the result."""
        station = "München Hbf"
        result = generate_asset_health_data(station)
        assert result.station == station

    def test_all_backlog_fields_populated(self):
        """All backlog fields should have non-negative values."""
        result = generate_asset_health_data("Frankfurt Hbf")
        assert result.backlog_total >= 0
        assert result.backlog_critical >= 0
        assert result.backlog_high >= 0
        assert result.backlog_medium >= 0
        assert result.backlog_avg_days_overdue >= 0
        # backlog_trend_pct can be negative (improving) or positive (worsening)
        assert isinstance(result.backlog_trend_pct, (int, float))

    def test_backlog_invariant_total_ge_sum_of_parts(self):
        """backlog_total >= backlog_critical + backlog_high + backlog_medium."""
        result = generate_asset_health_data("Hamburg Hbf")
        assert result.backlog_total >= result.backlog_critical + result.backlog_high + result.backlog_medium, (
            f"Backlog total ({result.backlog_total}) < sum of parts "
            f"({result.backlog_critical}+{result.backlog_high}+{result.backlog_medium})"
        )

    def test_backlog_trend_in_valid_range(self):
        """backlog_trend_pct should be within [-30, 30]."""
        for station in ["Berlin Hbf", "München Hbf", "Köln Hbf", "Frankfurt Hbf", "Stuttgart Hbf"]:
            result = generate_asset_health_data(station)
            assert -30 <= result.backlog_trend_pct <= 30, (
                f"{station}: backlog_trend_pct={result.backlog_trend_pct} outside [-30, 30]"
            )

    def test_all_health_matrix_fields_populated(self):
        """All 6 health percentage fields should be populated as floats."""
        result = generate_asset_health_data("Köln Hbf")
        assert isinstance(result.gate_health_pct, float)
        assert isinstance(result.sensor_health_pct, float)
        assert isinstance(result.firmware_compliance_pct, float)
        assert isinstance(result.structural_health_pct, float)
        assert isinstance(result.power_system_health_pct, float)
        assert isinstance(result.communication_health_pct, float)

    def test_health_percentages_in_valid_range(self):
        """Health matrix percentages should be 0 <= pct <= 100."""
        result = generate_asset_health_data("Stuttgart Hbf")
        for name in ["gate_health_pct", "sensor_health_pct", "firmware_compliance_pct",
                      "structural_health_pct", "power_system_health_pct",
                      "communication_health_pct"]:
            val = getattr(result, name)
            assert 0 <= val <= 100, (
                f"{name} = {val} is outside [0, 100]"
            )

    def test_fleet_rul_in_valid_range(self):
        """fleet_rul_pct should be 0 <= pct <= 100."""
        result = generate_asset_health_data("Berlin Hbf")
        assert 0 <= result.fleet_rul_pct <= 100

    def test_gates_total_reasonable(self):
        """gates_total should be between 15 and 45 for any station."""
        for station in ["Berlin Hbf", "München Hbf", "Köln Hbf", "Frankfurt Hbf",
                         "Stuttgart Hbf", "Hamburg Hbf", "Bremen Hbf"]:
            result = generate_asset_health_data(station)
            assert 15 <= result.gates_total <= 45, (
                f"{station}: gates_total={result.gates_total} outside [15, 45]"
            )

    def test_sensor_counts_consistent(self):
        """healthy + degraded + failed should be <= gates_total."""
        result = generate_asset_health_data("Bremen Hbf")
        total_sensors = result.sensor_healthy + result.sensor_degraded + result.sensor_failed
        assert total_sensors <= result.gates_total, (
            f"Sensors ({total_sensors}) exceed gates ({result.gates_total})"
        )

    def test_rul_buckets_sum_to_gates_total(self):
        """All 4 RUL buckets should sum to gates_total."""
        result = generate_asset_health_data("Nürnberg Hbf")
        bucket_sum = (result.rul_bucket_0_25 + result.rul_bucket_25_50 +
                      result.rul_bucket_50_75 + result.rul_bucket_75_100)
        assert bucket_sum == result.gates_total, (
            f"RUL buckets sum ({bucket_sum}) != gates_total ({result.gates_total})"
        )

    def test_firmware_counts_consistent(self):
        """Firmware counts should sum to gates_total."""
        result = generate_asset_health_data("Leipzig Hbf")
        fw_sum = result.firmware_uptodate + result.firmware_pending + result.firmware_critical
        assert fw_sum == result.gates_total, (
            f"Firmware counts sum ({fw_sum}) != gates_total ({result.gates_total})"
        )

    def test_depreciation_schedule_length(self):
        """Depreciation schedule should have 10 entries (2025–2034)."""
        result = generate_asset_health_data("Dresden Hbf")
        assert len(result.depreciation_schedule) == 10

    def test_depreciation_schedule_decreasing(self):
        """Book values in depreciation schedule should decrease over time."""
        result = generate_asset_health_data("Düsseldorf Hbf")
        values = [entry["book_value"] for entry in result.depreciation_schedule]
        for i in range(1, len(values)):
            assert values[i] <= values[i - 1], (
                f"Book value increased from year {i} to {i+1}: "
                f"{values[i-1]} -> {values[i]}"
            )

    def test_deterministic_output(self):
        """Same station should always produce the same AssetData."""
        station = "Berlin Hbf"
        result1 = generate_asset_health_data(station)
        result2 = generate_asset_health_data(station)
        # Compare key fields
        assert result1.fleet_rul_pct == result2.fleet_rul_pct
        assert result1.gates_total == result2.gates_total
        assert result1.backlog_total == result2.backlog_total
        assert result1.backlog_critical == result2.backlog_critical
        assert result1.gate_health_pct == result2.gate_health_pct
        assert result1.sensor_health_pct == result2.sensor_health_pct

    def test_different_stations_differ(self):
        """Different stations should (almost certainly) produce different data."""
        berlin = generate_asset_health_data("Berlin Hbf")
        munich = generate_asset_health_data("München Hbf")
        # At least one of these fields should differ
        fields = ["fleet_rul_pct", "gates_total", "backlog_total",
                   "gate_health_pct", "sensor_health_pct"]
        differing = [f for f in fields if getattr(berlin, f) != getattr(munich, f)]
        assert len(differing) >= 1, (
            f"Berlin and München produced identical data for all {fields}"
        )

    def test_with_empty_dataframe(self):
        """Passing an empty DataFrame should not crash; result is still valid."""
        empty_df = pd.DataFrame()
        result = generate_asset_health_data("Berlin Hbf", df=empty_df)
        assert isinstance(result, AssetData)
        assert result.fleet_rul_pct > 0

    def test_with_dataframe_with_station_data(self):
        """Passing a DataFrame with station data should produce valid output."""
        df = pd.DataFrame({
            "station": ["Berlin Hbf"] * 10,
            "gate_id": list(range(10)),
            "sensor_temp": [35.0 + np.random.uniform(-2, 2) for _ in range(10)],
            "sensor_vib": [6.0 + np.random.uniform(-1, 1) for _ in range(10)],
        })
        result = generate_asset_health_data("Berlin Hbf", df=df)
        assert isinstance(result, AssetData)
        assert result.gates_total >= 10
        assert result.fleet_rul_pct > 0

    def test_with_dataframe_mismatched_station(self):
        """A DataFrame without the requested station should fall back to RNG."""
        df = pd.DataFrame({
            "station": ["Hamburg Hbf"] * 5,
            "gate_id": list(range(5)),
        })
        result = generate_asset_health_data("Berlin Hbf", df=df)
        assert isinstance(result, AssetData)
        assert result.gates_total >= 15  # RNG fallback min

    def test_all_stations_valid(self):
        """Running for all 15 stations should produce valid data for each."""
        stations = [
            "Berlin Hbf", "München Hbf", "Köln Hbf", "Frankfurt Hbf",
            "Stuttgart Hbf", "Hamburg Hbf", "Bremen Hbf", "Kiel Hbf",
            "Nürnberg Hbf", "Leipzig Hbf", "Dresden Hbf", "Mannheim Hbf",
            "Düsseldorf Hbf", "Hannover Hbf", "Freiburg Hbf",
        ]
        for s in stations:
            result = generate_asset_health_data(s)
            assert isinstance(result, AssetData)
            assert result.station == s
            # Quick sanity: some fields should be > 0 for any station
            assert result.gates_total > 0
            assert result.sensor_healthy + result.sensor_degraded + result.sensor_failed > 0
            assert len(result.depreciation_schedule) == 10


# ═══════════════════════════════════════════════════════════
# Helper function tests (related)
# ═══════════════════════════════════════════════════════════


class TestClampFunction:
    """Tests for the _clamp utility used by generate_asset_health_data."""

    def test_clamp_within_bounds(self):
        """Value within bounds should be returned unchanged."""
        assert _clamp(50.0) == 50.0

    def test_clamp_below_lower_bound(self):
        """Value below lower bound should clamp to lo."""
        assert _clamp(-10.0) == 0.0

    def test_clamp_above_upper_bound(self):
        """Value above upper bound should clamp to hi."""
        assert _clamp(150.0) == 100.0

    def test_clamp_custom_bounds(self):
        """Custom lo/hi bounds should work."""
        assert _clamp(5.0, lo=10, hi=20) == 10.0
        assert _clamp(25.0, lo=10, hi=20) == 20.0
        assert _clamp(15.0, lo=10, hi=20) == 15.0

    def test_clamp_edge_values(self):
        """Values exactly at bounds should be returned as-is."""
        assert _clamp(0.0) == 0.0
        assert _clamp(100.0) == 100.0


class TestRngForFunction:
    """Tests for the _rng_for utility."""

    def test_deterministic(self):
        """Same station + offset should produce same RNG state."""
        rng1 = _rng_for("Berlin Hbf", 400)
        rng2 = _rng_for("Berlin Hbf", 400)
        assert rng1.rand() == rng2.rand()

    def test_different_stations_differ(self):
        """Different stations should produce different RNG sequences."""
        rng1 = _rng_for("Berlin Hbf", 400)
        rng2 = _rng_for("München Hbf", 400)
        assert rng1.rand() != rng2.rand()

    def test_different_offsets_differ(self):
        """Different offsets for the same station should differ."""
        rng1 = _rng_for("Berlin Hbf", 400)
        rng2 = _rng_for("Berlin Hbf", 500)
        assert rng1.rand() != rng2.rand()
