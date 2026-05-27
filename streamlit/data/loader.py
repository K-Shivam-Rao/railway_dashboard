import pandas as pd
import numpy as np
import polars as pl
from datetime import datetime, timedelta
import functools
import streamlit as st
from typing import Dict, List, Tuple, Optional, Union
import os
import logging

from utils.exceptions import DataLoadError, DataValidationError
from utils.logging_config import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────
PARQUET_FILE = "stations.parquet"
CSV_FILE = "stations.csv"

# Required columns for valid data
REQUIRED_COLUMNS = {
    "station",
    "platform",
    "gate_id",
    "door_state",
    "sensor_temp",
    "sensor_vib",
    "people",
}

# Valid door states
VALID_DOOR_STATES = {"open", "closed", "closing", "jammed", "offline"}

# Thresholds for data validation
MAX_TEMP = 100.0  # Celsius
MIN_TEMP = -50.0
MAX_VIB = 10.0  # mm/s
MAX_PEOPLE = 10000  # per gate


def _get_parquet_path() -> str:
    """Get path to parquet file (same directory as this module)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, PARQUET_FILE)


def _get_csv_path() -> str:
    """Get path to csv file (same directory as this module)."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, CSV_FILE)


def _validate_data(df: pl.DataFrame) -> None:
    """
    Validate loaded data for schema and value correctness.
    Raises DataValidationError if validation fails.
    """
    # Check required columns
    available = set(df.columns)
    missing_required = REQUIRED_COLUMNS - available
    if missing_required:
        raise DataValidationError(f"Missing required columns: {missing_required}")
    
    # Validate numeric ranges
    try:
        # Check temperature range
        temp_col = df["sensor_temp"]
        if temp_col.min() < MIN_TEMP or temp_col.max() > MAX_TEMP:
            logger.warning(f"Temperature values outside valid range [{MIN_TEMP}, {MAX_TEMP}]")
        
        # Check vibration range
        vib_col = df["sensor_vib"]
        if vib_col.min() < 0 or vib_col.max() > MAX_VIB:
            logger.warning(f"Vibration values outside valid range [0, {MAX_VIB}]")
        
        # Check people count
        people_col = df["people"]
        if people_col.min() < 0:
            logger.warning("Negative people count detected, filling with 0")
        
        # Validate door states
        door_states = set(df["door_state"].unique())
        invalid_states = door_states - VALID_DOOR_STATES
        if invalid_states:
            logger.warning(f"Invalid door states found: {invalid_states}")
    
    except Exception as e:
        raise DataValidationError(f"Data validation error: {e}")


class DataLoader:
    """
    DataLoader class encapsulates data loading and transformation logic.
    Uses static methods for Streamlit caching compatibility.
    """

    @staticmethod
    def _get_parquet_path() -> str:
        return _get_parquet_path()

    @staticmethod
    def _get_csv_path() -> str:
        return _get_csv_path()

    @staticmethod
    def save_as_parquet() -> bool:
        """Convert CSV to Parquet format. Returns True if successful."""
        parquet_path = DataLoader._get_parquet_path()
        csv_path = DataLoader._get_csv_path()
        
        if not os.path.exists(csv_path):
            logger.warning(f"CSV file not found: {csv_path}")
            return False
        
        try:
            df_pl = pl.read_csv(csv_path)
            df_pl.write_parquet(parquet_path, compression="zstd")
            logger.info(f"Saved Parquet file: {parquet_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save Parquet: {e}")
            return False

    @staticmethod
    def _load_parquet() -> Optional[pl.DataFrame]:
        """Try loading from Parquet. Returns None if not available."""
        parquet_path = DataLoader._get_parquet_path()
        if not os.path.exists(parquet_path):
            return None
        try:
            return pl.read_parquet(parquet_path)
        except Exception as e:
            logger.warning(f"Failed to load Parquet: {e}")
            return None

    @staticmethod
    def _load_csv() -> pl.DataFrame:
        """Load from CSV using Polars."""
        csv_path = DataLoader._get_csv_path()
        if not os.path.exists(csv_path):
            raise DataLoadError(f"CSV file not found: {csv_path}")
        try:
            return pl.read_csv(csv_path)
        except Exception as e:
            raise DataLoadError(f"Failed to load CSV: {e}")

    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def load_data_polars() -> pl.DataFrame:
        """Load station data using Polars - tries Parquet first, falls back to CSV."""
        try:
            df = DataLoader._load_parquet()
            if df is None:
                df = DataLoader._load_csv()
            
            if df is None:
                raise DataLoadError("Failed to load data from both Parquet and CSV")
            
            # Validate data
            _validate_data(df)
            
            return df
        except (DataLoadError, DataValidationError) as e:
            # Re-raise custom exceptions
            raise e
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading data: {e}")

    @staticmethod
    def convert_polars_to_pandas(df_pl: pl.DataFrame) -> pd.DataFrame:
        """Convert Polars DataFrame to Pandas for backward compatibility."""
        try:
            return df_pl.to_pandas()
        except Exception as e:
            raise DataLoadError(f"Failed to convert Polars to Pandas: {e}")

    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def transform_data_fast(df_pl: pl.DataFrame) -> pl.DataFrame:
        """Fast data transformation using Polars native operations."""
        try:
            now = datetime.now()
            current_hour = now.hour
            is_weekend = now.weekday() >= 5
            peak_hours = [6, 7, 8, 9, 16, 17, 18, 19]
            
            df = df_pl.clone()
            
            # Get numeric columns with defaults filled
            temp = df["sensor_temp"].fill_null(25.0)
            vib = df["sensor_vib"].fill_null(0.0)
            humidity = df["humidity"].fill_null(55.0)
            motor = df["door_motor_current"].fill_null(1.5)
            power = df["power_consumption"].fill_null(15.0)
            capacity = df["capacity"].fill_null(200.0)
            delay = df["delay"].fill_null(0.0)
            people = df["people"]
            door_state = df["door_state"]
            
            # Sync score
            humidity_penalty = (humidity - 70).clip(0) * 0.2
            motor_penalty = (motor - 2.5).clip(0) * 10
            sync_score = (100 - (temp - 25) * 0.5 - vib * 2 - humidity_penalty - motor_penalty).clip(0, 100)
            
            # Maintenance status - inline expression
            maintenance_status = (
                pl.when(door_state == "jammed").then(pl.lit("CRITICAL"))
                .when((temp > 45) | (power > 50)).then(pl.lit("CRITICAL"))
                .when(sync_score < 70).then(pl.lit("WARNING"))
                .when(vib > 2.5).then(pl.lit("WARNING"))
                .otherwise(pl.lit("OPTIMAL"))
            )
            
            # Risk score - inline expression
            risk = (
                pl.when(door_state == "jammed").then(60).otherwise(0) +
                pl.when(temp > 45).then(25).otherwise(0) +
                pl.when((temp > 35) & (temp <= 45)).then(10).otherwise(0) +
                pl.when(vib > 3).then(15).otherwise(0) +
                pl.when((vib > 2.5) & (vib <= 3)).then(10).otherwise(0) +
                pl.when((vib > 1.5) & (vib <= 2.5)).then(5).otherwise(0) +
                pl.when(power > 40).then(10).otherwise(0) +
                pl.when(motor > 3.0).then(15).otherwise(0) +
                pl.when(humidity > 80).then(5).otherwise(0) +
                pl.when(delay.abs() > 10).then(10).otherwise(0)
            ).clip(0, 100)
            
            # Congestion score
            capacity_safe = capacity.replace(0, 200.0)
            congestion = (people / capacity_safe * 100).clip(0, 100)
            
            # Energy rating - inline
            energy_rating = (
                pl.when(power <= 12).then(pl.lit("A"))
                .when(power <= 18).then(pl.lit("B"))
                .when(power <= 25).then(pl.lit("C"))
                .when(power <= 35).then(pl.lit("D"))
                .when(power > 35).then(pl.lit("E"))
                .otherwise(pl.lit("F"))
            )
            
            # Service reliability - inline
            delay_penalty = (
                pl.when(delay.abs() > 5).then(20)
                .when(delay.abs() > 2).then(10)
                .otherwise(0)
            )
            reliability = (100 - delay_penalty).clip(0, 100)
            
            # Door health - inline
            door_penalty = (
                pl.when(door_state == "jammed").then(50)
                .when(motor > 2.5).then(25)
                .otherwise(0)
            )
            door_health = (100 - door_penalty).clip(0, 100)
            
            # Add all derived columns at once
            df = df.with_columns([
                sync_score.cast(pl.Int32).alias("sync_score"),
                maintenance_status.alias("maintenance_status"),
                risk.cast(pl.Int32).alias("risk_score"),
                congestion.cast(pl.Int32).alias("congestion_score"),
                energy_rating.alias("energy_rating"),
                reliability.cast(pl.Int32).alias("service_reliability"),
                door_health.cast(pl.Int32).alias("door_health"),
                pl.lit(current_hour in peak_hours).alias("is_peak_hour"),
                pl.lit(is_weekend).alias("is_weekend"),
            ])
            
            return df
        except Exception as e:
            raise DataLoadError(f"Failed to transform data: {e}")

    @staticmethod
    @st.cache_data(ttl=60, show_spinner=False)
    def load_and_transform_data() -> pd.DataFrame:
        """
        Unified data pipeline: load + transform using Polars.
        Returns Pandas DataFrame for backward compatibility.
        This is the main entry point used by main.py
        Gracefully handles errors by returning empty DataFrame with expected columns.
        """
        try:
            df_pl = DataLoader.load_data_polars()
            df_pl = DataLoader.transform_data_fast(df_pl)
            return df_pl.to_pandas()
        except (DataLoadError, DataValidationError) as e:
            logger.warning(f"Data loading failed: {e}. Returning empty DataFrame.")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                "station", "platform", "gate_id", "door_state", "sensor_temp",
                "sensor_vib", "people", "sync_score", "maintenance_status",
                "risk_score", "congestion_score", "energy_rating",
                "service_reliability", "door_health", "is_peak_hour", "is_weekend"
            ])
        except Exception as e:
            logger.warning(f"Unexpected error: {e}. Returning empty DataFrame.")
            return pd.DataFrame()


# ─────────────────────────────────────
# BACKWARD-COMPATIBLE MODULE-LEVEL FUNCTIONS
# ─────────────────────────────────────
def load_data_polars() -> pl.DataFrame:
    return DataLoader.load_data_polars()

def transform_data_fast(df_pl: pl.DataFrame) -> pl.DataFrame:
    return DataLoader.transform_data_fast(df_pl)

def load_and_transform_data() -> pd.DataFrame:
    return DataLoader.load_and_transform_data()

def convert_polars_to_pandas(df_pl: pl.DataFrame) -> pd.DataFrame:
    return DataLoader.convert_polars_to_pandas(df_pl)

def save_as_parquet() -> bool:
    return DataLoader.save_as_parquet()
