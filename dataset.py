# STEP1-B: Standard Dataset Architecture
# This file is designed to be dropped into the current project
# and used as the foundation for future parsers and graph logic.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime


# ============================================================
# 1️⃣ Core Standard Model
# ============================================================

@dataclass
class Dataset:
    """
    Standard data container independent of file format.

    One Dataset = one loaded data file (Excel / CSV / Log / etc.)
    """

    cow_id: str
    source: str  # "excel", "aws_csv", "log", ...

    timestamps: List[datetime] = field(default_factory=list)

    # key: standardized metric name
    # value: list aligned with timestamps
    series: Dict[str, List[float]] = field(default_factory=dict)

    # ----------------------------
    # Helpers
    # ----------------------------

    def add_series(self, name: str, values: List[float]):
        """Register a metric series."""
        self.series[name] = values

    def get_series(self, name: str) -> List[float] | None:
        return self.series.get(name)

    def available_metrics(self) -> List[str]:
        return list(self.series.keys())


# ============================================================
# 2️⃣ Dataset Manager (UI / Graph shared state)
# ============================================================

class DatasetManager:
    """
    Holds all loaded datasets.
    This becomes the single source of truth for UI + Graph.
    """

    def __init__(self):
        self.datasets: List[Dataset] = []

    # ----------------------------
    # CRUD
    # ----------------------------

    def add(self, dataset: Dataset):
        self.datasets.append(dataset)

    def clear(self):
        self.datasets.clear()

    def all(self) -> List[Dataset]:
        return self.datasets


# ============================================================
# 3️⃣ Parser Base Class (future‑proof)
# ============================================================

class BaseParser:
    """All parsers must return a Dataset."""

    source_name: str = "unknown"

    def parse(self, path: str) -> Dataset:  # pragma: no cover (interface)
        raise NotImplementedError


# ============================================================
# 4️⃣ Excel Parser (current vendor format support)
# ============================================================

# NOTE:
# This is a SAFE bridge implementation.
# It keeps compatibility with the existing Excel structure
# while converting into the new Dataset model.

import pandas as pd


class VendorExcelParser(BaseParser):
    source_name = "excel"

    def parse(self, path: str) -> Dataset:
        df = pd.read_excel(path)

        # --------------------------------------------------
        # ⚠️ These column names MUST match current vendor file
        # Adjust ONLY here if vendor format changes.
        # --------------------------------------------------

        cow_id = str(df["cow_id"].iloc[0]) if "cow_id" in df else "unknown"

        dataset = Dataset(cow_id=cow_id, source=self.source_name)

        # ---- timestamps ----
        if "timestamp" in df:
            dataset.timestamps = [
                pd.to_datetime(ts).to_pydatetime() for ts in df["timestamp"]
            ]

        # ---- temperature metrics ----
        mapping = {
            "temp_current": "temp_current",
            "temp_avg": "temp_avg",
            "temp_station": "temp_station",
            "activity_current": "activity_current",
            "activity_avg": "activity_avg",
            "activity_station": "activity_station",
        }

        for col, metric in mapping.items():
            if col in df:
                dataset.add_series(metric, df[col].astype(float).tolist())

        return dataset


# ============================================================
# 5️⃣ Generic Graph Helper (format‑independent)
# ============================================================

# This logic will replace hard‑coded temperature/activity drawing.


def iter_plot_lines(dataset: Dataset):
    """
    Yields (metric_name, timestamps, values)
    for graph engine consumption.
    """

    for name, values in dataset.series.items():
        yield name, dataset.timestamps, values


# ============================================================
# 6️⃣ Minimal Smoke Test (safe to delete later)
# ============================================================

if __name__ == "__main__":
    parser = VendorExcelParser()

    # Change to a real file path when testing locally
    sample_path = "sample.xlsx"

    try:
        ds = parser.parse(sample_path)
        print("Loaded dataset:")
        print(" cow_id:", ds.cow_id)
        print(" metrics:", ds.available_metrics())
        print(" rows:", len(ds.timestamps))

    except FileNotFoundError:
        print("[INFO] Put a real Excel file path in sample_path to test.")
