"""Targeted tests pushing data/loader.py, data/sample_data.py, and utils/simulation_db.py to 95%+ coverage."""

import os
import sys
import json
import logging
import tempfile

import pytest
import pandas as pd
import polars as pl
from unittest.mock import patch, MagicMock, PropertyMock

# ── Comprehensive streamlit mock ────────────────────────────────────────────
st_mock = MagicMock()
st_mock.cache_data = lambda **kw: lambda fn: fn
st_mock.columns.side_effect = lambda *a, **kw: [MagicMock() for _ in range(a[0] if a else 1)]
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

# ── Imports ─────────────────────────────────────────────────────────────────
from data.loader import (
    DataLoader, _validate_data,
    DataValidationError, DataLoadError,
    load_data_polars as module_load_data_polars,
    transform_data_fast as module_transform_data_fast,
    convert_polars_to_pandas as module_convert_polars_to_pandas,
)
from data import sample_data as sd
from utils import simulation_db as db_mod


# =============================================================================
# DATA / LOADER.PY
# =============================================================================

class TestLoaderValidateDataException:
    """Cover lines 90-91: except Exception handler in _validate_data."""

    def test_exception_on_numeric_validation(self):
        """_validate_data falls into except Exception when a column type raises."""
        df = pl.DataFrame({
            "station": ["Berlin Hbf"],
            "platform": ["1"],
            "gate_id": ["G001"],
            "door_state": ["open"],
            "sensor_temp": ["not_a_number"],  # string → .min() will fail in polars
            "sensor_vib": [1.0],
            "people": [100],
        })
        with pytest.raises(DataValidationError, match="Data validation error"):
            _validate_data(df)


class TestLoaderLoadDataPolarsPaths:
    """Cover lines 157, 160, 166-170: fallback + exception handlers.
    Uses __wrapped__ to bypass @st.cache_data so coverage sees execution."""

    def _unwrapped(self):
        # Fallback to fn itself when mock cache_data is a no-op (no __wrapped__)
        return getattr(DataLoader.load_data_polars, '__wrapped__', DataLoader.load_data_polars)

    def test_fallback_parquet_none_csv_succeeds(self, tmp_path):
        """Line 157: parquet returns None → falls back to CSV."""
        import data.loader as ldr_mod
        csv_path = tmp_path / "stations.csv"
        pl.DataFrame({
            "station": ["Berlin Hbf"], "platform": ["1"], "gate_id": ["G001"],
            "door_state": ["open"], "sensor_temp": [25.0], "sensor_vib": [1.0],
            "people": [100], "humidity": [55], "door_motor_current": [1.5],
            "power_consumption": [15], "capacity": [200], "delay": [0],
        }).write_csv(str(csv_path))

        with patch.object(DataLoader, "_load_parquet", return_value=None):
            with patch.object(DataLoader, "_get_csv_path", return_value=str(csv_path)):
                fn = self._unwrapped()
                result = fn()
                assert isinstance(result, pl.DataFrame)
                assert len(result) > 0

    def test_both_fail_raises_dataloaderror(self):
        """Line 160: both parquet + CSV return None → raise DataLoadError."""
        fn = self._unwrapped()
        with patch.object(DataLoader, "_load_parquet", return_value=None):
            with patch.object(DataLoader, "_load_csv", return_value=None):
                with pytest.raises(DataLoadError, match="Failed to load data from both"):
                    fn()

    def test_validation_error_re_raised(self):
        """Lines 166-168: DataValidationError re-raised via except handler."""
        import data.loader as ldr_mod
        fn = self._unwrapped()
        with patch.object(DataLoader, "_load_parquet", return_value=None):
            with patch.object(ldr_mod, "_validate_data", side_effect=DataValidationError("Bad")):
                with pytest.raises(DataValidationError, match="Bad"):
                    fn()

    def test_generic_exception_wrapped(self):
        """Lines 169-170: generic Exception → wrapped in DataLoadError."""
        fn = self._unwrapped()
        with patch.object(DataLoader, "_load_parquet", side_effect=ValueError("random error")):
            with pytest.raises(DataLoadError, match="Unexpected error loading data"):
                fn()


class TestLoaderLoadAndTransformExceptions:
    """Cover lines 291-302: exception handlers in load_and_transform_data.
    Uses __wrapped__ to bypass @st.cache_data so coverage sees execution."""

    def _unwrapped(self):
        # Fallback to fn itself when mock cache_data is a no-op (no __wrapped__)
        return getattr(DataLoader.load_and_transform_data, '__wrapped__', DataLoader.load_and_transform_data)

    def test_dataloaderror_returns_empty_df_with_columns(self):
        """Lines 291-299: DataLoadError → empty DataFrame with expected columns."""
        fn = self._unwrapped()
        with patch.object(DataLoader, "load_data_polars",
                          side_effect=DataLoadError("Data loading failed")):
            result = fn()
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
            assert "station" in result.columns
            assert "gate_id" in result.columns

    def test_validation_error_returns_empty_df_with_columns(self):
        """Lines 291-299: DataValidationError → empty DataFrame with expected columns."""
        fn = self._unwrapped()
        with patch.object(DataLoader, "load_data_polars",
                          side_effect=DataValidationError("Validation failed")):
            result = fn()
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
            assert "station" in result.columns

    def test_unexpected_error_returns_empty_df(self):
        """Lines 300-302: generic Exception → empty DataFrame without columns."""
        fn = self._unwrapped()
        with patch.object(DataLoader, "load_data_polars",
                          side_effect=ValueError("Unexpected error")):
            result = fn()
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
            assert list(result.columns) == []


# =============================================================================
# DATA / SAMPLE_DATA.PY
# =============================================================================

class TestSampleDataCustomerDfBranchCoverage:
    """Cover lines 408-422: branch coverage for optional columns in get_customer_df."""

    def test_customer_df_missing_optional_columns(self):
        """When CUSTOMERS dicts lack optional fields, the fallback branches run."""
        customers_no_opts = [
            {
                "customer_id": "C001",
                "customer_name": "Test Op",
                "operator_id": "OP999",
                "operator_name": "Test Operator",
                "tier": "Gold",
                "trains_covered": 100,
                "total_contract_value_eur": 500000,
                "platforms_installed": 10,
                "risk_level": "Medium Risk",
                "days_to_renewal": 45,
                "rfm_segment": "Regular",
                "segment": "Medium",
                "recency_score": 8,
                "frequency_score": 6,
                "monetary_score": 7,
                "customer_email": "test@test.com",
                "phone": "+123",
                "region": "Europe",
                "operator_type": "Passenger",
                "contract_start": "2024-01-01",
                "contract_end": "2027-01-01",
                "contract_health_score": 85,
                "health_status": "Healthy",
                "health_score": 85,
                "satisfaction_score": 8,
                "last_engagement": "2026-03-01",
                "churn_risk": "Low",
                "value_tier": "Gold",
                "psd_units": 50,
            }
        ]
        with patch('data.sample_data.CUSTOMERS', customers_no_opts):
            df = sd.get_customer_df()

            # All fallback branches should have executed
            assert "total_routes" in df.columns
            assert df["total_routes"].iloc[0] == 100 // 5  # from fallback
            assert "maintenance_annual_eur" in df.columns
            assert df["maintenance_annual_eur"].iloc[0] == 500000 * 0.1
            assert "last_project_days" in df.columns
            assert df["last_project_days"].iloc[0] >= 30
            assert "open_issues" in df.columns
            assert df["open_issues"].iloc[0] == 2  # Medium Risk → 2
            assert "contract_status" in df.columns
            assert df["contract_status"].iloc[0] == "Urgent"  # 45 days → Urgent

    def test_customer_df_columns_present_no_fallback(self):
        """When optional columns ARE present, fallback branches are skipped."""
        df = sd.get_customer_df()
        # The real CUSTOMERS data should already have these columns
        assert "total_routes" in df.columns
        assert "maintenance_annual_eur" in df.columns
        assert "last_project_days" in df.columns
        assert "open_issues" in df.columns
        assert "contract_status" in df.columns


class TestSampleDataSupportTicketTrendMonthsBack:
    """Cover line 706: months_back validation branch in get_support_ticket_trend."""

    def test_invalid_months_back_type(self):
        """Non-int months_back triggers fallback to 6."""
        df = sd.get_support_ticket_trend("OP001", months_back="invalid")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6  # fallback months_back=6

    def test_months_back_zero(self):
        """months_back=0 triggers fallback to 6."""
        df = sd.get_support_ticket_trend("OP001", months_back=0)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6

    def test_months_back_negative(self):
        """months_back=-1 triggers fallback to 6."""
        df = sd.get_support_ticket_trend("OP001", months_back=-1)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 6

    def test_months_back_valid_int(self):
        """Valid int months_back is used directly."""
        df = sd.get_support_ticket_trend("OP001", months_back=3)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3


class TestSampleDataOperatorHealthTrendMonthsBack:
    """Cover line 813: months_back validation branch in get_operator_health_trend."""

    def test_invalid_months_back_type(self):
        """Non-int months_back triggers fallback to 12."""
        df = sd.get_operator_health_trend("OP001", months_back="invalid")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12

    def test_months_back_zero(self):
        """months_back=0 triggers fallback to 12."""
        df = sd.get_operator_health_trend("OP001", months_back=0)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12

    def test_months_back_negative(self):
        """months_back=-1 triggers fallback to 12."""
        df = sd.get_operator_health_trend("OP001", months_back=-1)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 12

    def test_months_back_valid_int(self):
        """Valid int months_back is used directly."""
        df = sd.get_operator_health_trend("OP001", months_back=3)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3


# =============================================================================
# UTILS / SIMULATION_DB.PY
# =============================================================================

# ── Fixture: temporary DB ───────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Use a temporary database file for each test (same pattern as test_simulation_db.py)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    original_path = db_mod.DB_PATH
    db_mod.DB_PATH = tmp.name
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    db_mod.init_simulation_db()
    yield
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    db_mod.DB_PATH = original_path


class TestSimDbGetDbConnectionError:
    """Cover lines 25-29: sqlite3.Error handler in get_db_connection."""

    def test_sqlite_commit_error_triggers_rollback(self, temp_db):
        """sqlite3.Error on commit → rollback() is called (lines 27-28)."""
        import sqlite3
        mock_conn = MagicMock(spec=sqlite3.Connection)
        # commit raises sqlite3.Error AFTER conn is assigned
        mock_conn.commit.side_effect = sqlite3.Error("Commit failed")
        mock_conn.row_factory = sqlite3.Row

        with patch.object(db_mod, "sqlite3") as mock_sqlite3:
            mock_sqlite3.connect.return_value = mock_conn
            mock_sqlite3.Error = sqlite3.Error
            with pytest.raises(sqlite3.Error, match="Commit failed"):
                with db_mod.get_db_connection() as conn:
                    pass
            # Verify rollback was called (line 28)
            mock_conn.rollback.assert_called_once()


class TestLoaderModuleLevelFunctions:
    """Cover lines 309, 312, 318: module-level function return statements."""

    def test_module_level_load_data_polars(self, tmp_path):
        """Line 309: module-level load_data_polars return statement."""
        csv_path = tmp_path / "stations.csv"
        pl.DataFrame({
            "station": ["Berlin Hbf"], "platform": ["1"], "gate_id": ["G001"],
            "door_state": ["open"], "sensor_temp": [25.0], "sensor_vib": [1.0],
            "people": [100], "humidity": [55], "door_motor_current": [1.5],
            "power_consumption": [15], "capacity": [200], "delay": [0],
        }).write_csv(str(csv_path))

        with patch.object(DataLoader, "_load_parquet", return_value=None):
            with patch.object(DataLoader, "_get_csv_path", return_value=str(csv_path)):
                # Call the MODULE-level function, not DataLoader.load_data_polars
                result = module_load_data_polars()
                assert isinstance(result, pl.DataFrame)
                assert len(result) > 0

    def test_module_level_transform_data_fast(self, full_pl_df):
        """Line 312: module-level transform_data_fast return statement."""
        result = module_transform_data_fast(full_pl_df)
        assert isinstance(result, pl.DataFrame)
        assert "sync_score" in result.columns

    def test_module_level_convert_polars_to_pandas(self, minimal_pl_df):
        """Line 318: module-level convert_polars_to_pandas return statement."""
        result = module_convert_polars_to_pandas(minimal_pl_df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    @pytest.fixture
    def minimal_pl_df(self):
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
    def full_pl_df(self):
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


class TestSimDbSaveSessionException:
    """Cover lines 160-161: except Exception in save_session."""

    def test_save_session_exception(self, temp_db):
        """save_session handles DB write failure gracefully."""
        with patch.object(db_mod, "get_db_connection",
                          side_effect=Exception("DB write failed")):
            # Should not raise
            db_mod.save_session("test-fail", {"total_incidents": 5}, {"mode": "drill"})


class TestSimDbSaveIncidentsException:
    """Cover lines 194-195: except Exception in save_incidents."""

    def test_save_incidents_exception(self, temp_db):
        """save_incidents handles DB write failure gracefully."""
        with patch.object(db_mod, "get_db_connection",
                          side_effect=Exception("DB write failed")):
            db_mod.save_incidents("test-fail", [
                {"id": "INC-001", "timestamp": "now", "station": "Berlin",
                 "incident_type": "jam", "severity": "HIGH",
                 "description": "test", "assigned_persona": "",
                 "assigned_role": "", "status": "open", "resolution_time_min": 0},
            ])


class TestSimDbSaveAchievementException:
    """Cover lines 211-212: except Exception in save_achievement."""

    def test_save_achievement_exception(self, temp_db):
        """save_achievement handles DB write failure gracefully."""
        with patch.object(db_mod, "get_db_connection",
                          side_effect=Exception("DB write failed")):
            db_mod.save_achievement("test-fail", "BADGE-1", "First Responder")


class TestSimDbSaveScenarioTemplateException:
    """Cover lines 321-323: except Exception in save_scenario_template."""

    def test_save_scenario_template_exception(self, temp_db):
        """save_scenario_template returns False on DB failure."""
        with patch.object(db_mod, "get_db_connection",
                          side_effect=Exception("DB write failed")):
            result = db_mod.save_scenario_template("Test", {"p": 1})
            assert result is False


class TestSimDbGetScenarioTemplatesException:
    """Cover lines 340-341: except Exception in get_scenario_templates."""

    def test_json_loads_failure_returns_empty_dict(self, temp_db):
        """When config_json is invalid JSON, fallback to empty dict."""
        # Insert a row with invalid JSON directly
        with db_mod.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scenario_templates (name, config_json, is_custom, created_at, tags)
                VALUES (?, ?, ?, ?, ?)
            """, ("Bad JSON", "NOT VALID JSON{", 1, "2026-01-01", "test"))
        templates = db_mod.get_scenario_templates()
        assert len(templates) >= 1
        bad = [t for t in templates if t["name"] == "Bad JSON"]
        assert len(bad) == 1
        assert bad[0]["config_json"] == {}  # fallback on parse failure


class TestSimDbDeleteScenarioTemplateException:
    """Cover lines 355-357: except Exception in delete_scenario_template."""

    def test_delete_scenario_template_exception(self, temp_db):
        """delete_scenario_template returns False on DB failure."""
        with patch.object(db_mod, "get_db_connection",
                          side_effect=Exception("DB write failed")):
            result = db_mod.delete_scenario_template("Anything")
            assert result is False


class TestSimDbSaveCompetencyScoresException:
    """Cover lines 388-389: except Exception in save_competency_scores."""

    def test_save_competency_scores_exception(self, temp_db):
        """save_competency_scores handles DB write failure gracefully."""
        with patch.object(db_mod, "get_db_connection",
                          side_effect=Exception("DB write failed")):
            db_mod.save_competency_scores("test-fail", [
                {"persona_name": "Alice", "speed_score": 85.0, "accuracy_score": 90.0,
                 "critical_score": 75.0, "specialty_score": 88.0, "escalation_score": 80.0,
                 "balance_score": 82.0, "overall_score": 84.0},
            ])
