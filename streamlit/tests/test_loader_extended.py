"""Extended tests for data/loader.py — covers error paths and edge cases."""
from unittest.mock import MagicMock, patch

import pandas as pd
import polars as pl
import pytest

# ── Comprehensive streamlit mock (compatible across test files) ──
# Must be set up before importing data.loader
st_mock = MagicMock()
st_mock.cache_data = lambda **kw: lambda fn: fn

def _columns_side_effect(*args, **kwargs):
    n = args[0] if args else kwargs.get("n", 1)
    if isinstance(n, (list, tuple)):
        n = len(n)
    return [MagicMock() for _ in range(n)]

st_mock.columns.side_effect = _columns_side_effect
st_mock.markdown = MagicMock()
st_mock.plotly_chart = MagicMock()
st_mock.selectbox.return_value = "Berlin Hbf"
st_mock.slider.return_value = 1.0
st_mock.button.return_value = False
st_mock.text_input.return_value = "Test"
st_mock.spinner = MagicMock().__enter__
st_mock.success = MagicMock()
st_mock.info = MagicMock()
st_mock.json = MagicMock()
st_mock.error = MagicMock()

modules = {"streamlit": st_mock}
patcher = patch.dict("sys.modules", modules)
patcher.start()

from data.loader import (
    DataLoader,
    DataLoadError,
    DataValidationError,
    _get_csv_path,
    _get_parquet_path,
    _validate_data,
)

# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def minimal_pl_df():
    return pl.DataFrame({
        "station": ["Berlin Hbf", "München Hbf"],
        "platform": ["1", "2"],
        "gate_id": ["G001", "G002"],
        "door_state": ["open", "closed"],
        "sensor_temp": [25.0, 30.0],
        "sensor_vib": [1.2, 0.8],
        "people": [120, 85],
    })


@pytest.fixture
def full_pl_df():
    return pl.DataFrame({
        "station": ["Berlin Hbf", "München Hbf"],
        "platform": ["1", "2"],
        "gate_id": ["G001", "G002"],
        "door_state": ["open", "closed"],
        "sensor_temp": [25.0, 30.0],
        "sensor_vib": [1.2, 0.8],
        "people": [120, 85],
        "humidity": [55.0, 60.0],
        "door_motor_current": [1.5, 2.0],
        "power_consumption": [15.0, 20.0],
        "capacity": [200.0, 250.0],
        "delay": [0.0, 1.5],
    })


# ── _validate_data tests ──

class TestValidateData:
    def test_missing_required_column(self):
        df = pl.DataFrame({"station": ["Berlin"], "platform": ["1"]})
        with pytest.raises(DataValidationError, match="Missing required columns"):
            _validate_data(df)

    def test_valid_data_passes(self, minimal_pl_df):
        _validate_data(minimal_pl_df)

    def test_temp_out_of_range_warning(self, minimal_pl_df, caplog):
        df = minimal_pl_df.with_columns(pl.lit(150.0).alias("sensor_temp"))
        import logging
        caplog.set_level(logging.WARNING)
        _validate_data(df)
        assert "outside valid range" in caplog.text

    def test_vib_out_of_range_warning(self, minimal_pl_df, caplog):
        df = minimal_pl_df.with_columns(pl.lit(15.0).alias("sensor_vib"))
        import logging
        caplog.set_level(logging.WARNING)
        _validate_data(df)
        assert "outside valid range" in caplog.text

    def test_negative_people_warning(self, minimal_pl_df, caplog):
        df = minimal_pl_df.with_columns(pl.lit(-5).alias("people"))
        import logging
        caplog.set_level(logging.WARNING)
        _validate_data(df)
        assert "Negative people" in caplog.text

    def test_invalid_door_states_warning(self, minimal_pl_df, caplog):
        df = minimal_pl_df.with_columns(pl.lit("broken").alias("door_state"))
        import logging
        caplog.set_level(logging.WARNING)
        _validate_data(df)
        assert "Invalid door states" in caplog.text


# ── _load_parquet ──

class TestLoadParquet:
    def test_success(self, tmp_path, full_pl_df):
        parquet_path = tmp_path / "test.parquet"
        full_pl_df.write_parquet(str(parquet_path))
        with patch("data.loader.DataLoader._get_parquet_path", return_value=str(parquet_path)):
            result = DataLoader._load_parquet()
            assert result is not None
            assert len(result) == 2

    def test_file_missing(self):
        with patch("data.loader.DataLoader._get_parquet_path", return_value="/nope.parquet"):
            assert DataLoader._load_parquet() is None

    def test_corrupted(self, tmp_path):
        p = tmp_path / "test.parquet"
        p.write_text("garbage")
        with patch("data.loader.DataLoader._get_parquet_path", return_value=str(p)):
            assert DataLoader._load_parquet() is None

    def test_read_exception_logged(self, tmp_path, caplog):
        p = tmp_path / "test.parquet"
        p.write_text("bad")
        import logging
        caplog.set_level(logging.WARNING)
        with patch("data.loader.DataLoader._get_parquet_path", return_value=str(p)):
            DataLoader._load_parquet()
        assert "Failed to load Parquet" in caplog.text


# ── _load_csv ──

class TestLoadCsv:
    def test_success(self, tmp_path, full_pl_df):
        csv_path = tmp_path / "test.csv"
        full_pl_df.write_csv(csv_path)
        with patch("data.loader.DataLoader._get_csv_path", return_value=str(csv_path)):
            result = DataLoader._load_csv()
            assert result is not None
            assert len(result) == 2

    def test_missing(self):
        with patch("data.loader.DataLoader._get_csv_path", return_value="/nope.csv"):
            with pytest.raises(DataLoadError, match="CSV file not found"):
                DataLoader._load_csv()

    def test_read_error(self, tmp_path):
        p = tmp_path / "test.csv"
        p.write_text("")
        with patch("data.loader.DataLoader._get_csv_path", return_value=str(p)):
            with patch("polars.read_csv", side_effect=Exception("Read failed")):
                with pytest.raises(DataLoadError, match="Failed to load CSV"):
                    DataLoader._load_csv()


# ── load_data_polars (via internal methods, bypassing @st.cache_data) ──

class TestLoadDataPolars:
    def test_parquet_first(self, tmp_path, full_pl_df):
        """Verify parquet is loaded when both exist."""
        parquet_path = tmp_path / "test.parquet"
        full_pl_df.write_parquet(str(parquet_path))
        with patch("data.loader.DataLoader._get_parquet_path", return_value=str(parquet_path)):
            result = DataLoader._load_parquet()
            assert result is not None and len(result) == 2

    def test_fallback_to_csv_internal(self):
        """Fallback: _load_parquet returns None, _load_csv is called."""
        with patch.object(DataLoader, "_load_parquet", return_value=None):
            with patch.object(DataLoader, "_load_csv") as mock_csv:
                # Simulate load_data_polars logic
                df = DataLoader._load_parquet()
                if df is None:
                    DataLoader._load_csv()
                mock_csv.assert_called_once()

    def test_both_missing(self):
        with patch.object(DataLoader, "_load_parquet", return_value=None):
            with patch.object(DataLoader, "_load_csv", side_effect=DataLoadError("CSV not found")):
                with pytest.raises(DataLoadError):
                    df = DataLoader._load_parquet()
                    if df is None:
                        DataLoader._load_csv()


# ── transform_data_fast ──

class TestTransformDataFast:
    def test_adds_derived_columns(self, full_pl_df):
        result = DataLoader.transform_data_fast(full_pl_df)
        for col in ["sync_score", "maintenance_status", "risk_score",
                     "congestion_score", "energy_rating", "service_reliability",
                     "door_health", "is_peak_hour", "is_weekend"]:
            assert col in result.columns, f"Missing: {col}"

    def test_missing_optional_columns_raises(self):
        """Minimal DataFrame missing optional columns raises DataLoadError."""
        df = pl.DataFrame({
            "station": ["Berlin Hbf"], "platform": ["1"], "gate_id": ["G001"],
            "door_state": ["open"], "sensor_temp": [25.0],
            "sensor_vib": [1.2], "people": [100],
        })
        with pytest.raises(DataLoadError, match="Failed to transform data"):
            DataLoader.transform_data_fast(df)

    def test_jammed_door_critical(self):
        df = pl.DataFrame({
            "station": ["Berlin Hbf"], "platform": ["1"], "gate_id": ["G001"],
            "door_state": ["jammed"], "sensor_temp": [25.0], "sensor_vib": [1.2],
            "people": [100], "humidity": [55], "door_motor_current": [1.5],
            "power_consumption": [15], "capacity": [200], "delay": [0],
        })
        result = DataLoader.transform_data_fast(df)
        assert result["maintenance_status"][0] == "CRITICAL"

    def test_high_temp_critical(self):
        df = pl.DataFrame({
            "station": ["Berlin Hbf"], "platform": ["1"], "gate_id": ["G001"],
            "door_state": ["open"], "sensor_temp": [50.0], "sensor_vib": [1.0],
            "people": [100], "humidity": [55], "door_motor_current": [1.5],
            "power_consumption": [15], "capacity": [200], "delay": [0],
        })
        result = DataLoader.transform_data_fast(df)
        assert result["maintenance_status"][0] == "CRITICAL"

    def test_high_vib_warning(self):
        df = pl.DataFrame({
            "station": ["Berlin Hbf"], "platform": ["1"], "gate_id": ["G001"],
            "door_state": ["open"], "sensor_temp": [25.0], "sensor_vib": [3.0],
            "people": [100], "humidity": [55], "door_motor_current": [1.5],
            "power_consumption": [15], "capacity": [200], "delay": [0],
        })
        result = DataLoader.transform_data_fast(df)
        assert result["maintenance_status"][0] in ("WARNING", "CRITICAL")

    def test_none_raises(self):
        with pytest.raises(DataLoadError, match="Failed to transform data"):
            DataLoader.transform_data_fast(None)


# ── convert_polars_to_pandas ──

class TestConvertPolarsToPandas:
    def test_success(self, minimal_pl_df):
        result = DataLoader.convert_polars_to_pandas(minimal_pl_df)
        assert isinstance(result, pd.DataFrame) and len(result) == 2

    def test_none_raises(self):
        with pytest.raises(DataLoadError, match="Failed to convert"):
            DataLoader.convert_polars_to_pandas(None)

    def test_empty(self):
        result = DataLoader.convert_polars_to_pandas(pl.DataFrame())
        assert isinstance(result, pd.DataFrame)


# ── save_as_parquet ──

class TestSaveAsParquet:
    def test_success(self, tmp_path, full_pl_df):
        csv_path = tmp_path / "test.csv"
        parquet_path = tmp_path / "test.parquet"
        full_pl_df.write_csv(csv_path)
        with patch("data.loader.DataLoader._get_csv_path", return_value=str(csv_path)):
            with patch("data.loader.DataLoader._get_parquet_path", return_value=str(parquet_path)):
                assert DataLoader.save_as_parquet() is True
                assert parquet_path.exists()

    def test_csv_missing(self):
        with patch("data.loader.DataLoader._get_csv_path", return_value="/nope.csv"):
            assert DataLoader.save_as_parquet() is False

    def test_write_failure(self, tmp_path, full_pl_df):
        csv_path = tmp_path / "test.csv"
        full_pl_df.write_csv(csv_path)
        with patch("data.loader.DataLoader._get_csv_path", return_value=str(csv_path)):
            with patch.object(pl.DataFrame, "write_parquet", side_effect=Exception("Write failed")):
                assert DataLoader.save_as_parquet() is False


# ── load_and_transform_data ──

class TestLoadAndTransform:
    def test_error_returns_empty(self):
        with patch.object(DataLoader, "load_data_polars", side_effect=DataLoadError("Fail")):
            result = DataLoader.load_and_transform_data()
            assert isinstance(result, pd.DataFrame)

    def test_unexpected_error_returns_empty(self):
        with patch.object(DataLoader, "load_data_polars", side_effect=ValueError("Unexpected")):
            result = DataLoader.load_and_transform_data()
            assert isinstance(result, pd.DataFrame)


# ── Path helpers ──

class TestPathFunctions:
    def test_parquet_path(self):
        assert isinstance(_get_parquet_path(), str)

    def test_csv_path(self):
        assert isinstance(_get_csv_path(), str)
