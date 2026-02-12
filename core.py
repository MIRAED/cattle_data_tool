from __future__ import annotations

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                               QHBoxLayout, QWidget, QMenuBar, QCheckBox,
                               QSlider, QLabel, QFileDialog, QMessageBox,
                               QDialog, QTextEdit, QPushButton, QGridLayout, QTabWidget, QScrollArea, QSpinBox)

from dataclasses import dataclass
import numpy as np
from collections import defaultdict
from datetime import date
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from datetime import datetime, timedelta, date

import pyqtgraph as pg

@dataclass
class DatasetEntry:
    """
    Step2 임시 어댑터
    내부는 CowData를 사용하도록 변경
    """

    def __init__(self, cow: CowData):
        self.cow = cow
        self.label = cow.label
        self.visible = True
        self.checkbox = None
        self.curves = {
            "temp": [],
            "activity": [],
        }

@dataclass
class CowData:
    file_path: str
    log_date: date

    timestamps: list
    temps_current: list
    temps_station: list
    temps_avg: list
    acts_current: list
    acts_station: list
    acts_avg: list

    @property
    def key(self):
        return (self.file_path, self.log_date)

    @property
    def label(self):
        return f"{Path(self.file_path).stem}_{self.log_date}"

class DataPool:
    def __init__(self):
        self._data: dict[tuple, CowData] = {}
        self._visible: dict[tuple, bool] = {}

    # -------------------------
    # 기본 관리
    # -------------------------
    def add(self, cow: CowData):
        self._data[cow.key] = cow
        self._visible.setdefault(cow.key, True)

    def remove(self, key):
        self._data.pop(key, None)
        self._visible.pop(key, None)

    def clear(self):
        self._data.clear()
        self._visible.clear()

    # -------------------------
    # 조회
    # -------------------------
    def all(self):
        return list(self._data.values())

    def visible(self):
        return [self._data[k] for k, v in self._visible.items() if v]

    def set_visible(self, key, visible: bool):
        if key in self._visible:
            self._visible[key] = visible

    def is_visible(self, key) -> bool:
        return self._visible.get(key, False)

    def keys(self):
        return list(self._data.keys())
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def __iter__(self):
        return iter(self._data.values())
    
    def items(self):
        return self._data.items()

class StatisticsEngine:
    """데이터 통계 계산 전담 엔진"""

    @staticmethod
    def slice_by_time(dc, start_sec, end_sec):
        """시간 구간에 해당하는 인덱스 추출"""
        indices = [
            i for i, ts in enumerate(dc.time_seconds)
            if start_sec <= ts <= end_sec
        ]
        return indices

    @staticmethod
    def mean(values):
        """None 제외 평균"""
        vals = [v for v in values if v is not None]
        if not vals:
            return None
        return sum(vals) / len(vals)

    @classmethod
    def range_mean(cls, dc, start_sec, end_sec, attr):
        """
        특정 속성(temp/activity)의
        A-B 구간 평균 계산
        """
        idx = cls.slice_by_time(dc, start_sec, end_sec)
        values = [getattr(dc, attr)[i] for i in idx]
        return cls.mean(values)

    @classmethod
    def summarize_between_lines(cls, dc, start_sec, end_sec):
        """라인 A-B 사이 주요 통계 반환"""
        return {
            "temp_mean": cls.range_mean(dc, start_sec, end_sec, "temps"),
            "act_mean": cls.range_mean(dc, start_sec, end_sec, "activities"),
        }
    
    @staticmethod
    def _basic_stats(filtered_values):
        if not filtered_values:
            return None, None, None, None

        avg = sum(filtered_values) / len(filtered_values)
        min_val = min(filtered_values)
        max_val = max(filtered_values)

        if len(filtered_values) > 1:
            variance = sum((x - avg) ** 2 for x in filtered_values) / len(filtered_values)
            std_dev = variance ** 0.5
        else:
            std_dev = 0

        return avg, min_val, max_val, std_dev


    @classmethod
    def calculate_between_lines(cls, data, pos_a, pos_b):
        """라인 A-B 사이 모든 통계 계산"""

        if not data.timestamps:
            return None

        # 시간 → seconds
        start_time = data.timestamps[0]
        time_seconds = [(ts - start_time).total_seconds() for ts in data.timestamps]

        # 범위 인덱스
        indices = [i for i, t in enumerate(time_seconds) if pos_a <= t <= pos_b]

        if not indices:
            return {
                "time_range": None,
                "stats": {}
            }

        # 실제 시간 범위
        first_sec = time_seconds[indices[0]]
        last_sec = time_seconds[indices[-1]]

        from datetime import timedelta
        time_a = start_time + timedelta(seconds=first_sec)
        time_b = start_time + timedelta(seconds=last_sec)

        # 데이터 타입별 통계
        data_configs = {
            'cow_current_temp': data.cow_current_temp,
            'cow_station_temp': data.cow_station_temp,
            'cow_avg_temp': data.cow_avg_temp,
            'cow_current_activity': data.cow_current_activity,
            'cow_station_activity': data.cow_station_activity,
            'cow_avg_activity': data.cow_avg_activity
        }

        results = {}

        for key, values in data_configs.items():
            filtered = [values[i] for i in indices if i < len(values) and values[i] is not None]
            results[key] = cls._basic_stats(filtered)

        return {
            "time_range": (time_a, time_b),
            "stats": results
        }


class RangeCalculator:
    @staticmethod
    def calc(entries: list[CowData]):
        all_temps = []
        all_acts = []

        for e in entries:
            all_temps.extend(e.temps_current)
            all_temps.extend(e.temps_station)
            all_temps.extend(e.temps_avg)

            all_acts.extend(e.acts_current)
            all_acts.extend(e.acts_station)
            all_acts.extend(e.acts_avg)

        return all_temps, all_acts

    @staticmethod
    def minmax(values: list[float]):
        if not values:
            return None, None
        return min(values), max(values)



class GraphEngine:
    """
    Step3-1:
    UI와 완전히 분리된 순수 계산 엔진
    pyqtgraph / QWidget / Checkbox 전혀 모름
    """
    # -----------------------------
    # visible CowData 추출
    # -----------------------------
    @staticmethod
    def get_visible_cows(entries):
        """
        entries: Iterable[DatasetEntry]
        return: list[CowData]
        """
        return [e.cow for e in entries if e.visible]
    
    # -----------------------------
    # 전체 범위 계산
    # -----------------------------
    @staticmethod
    def calculate_ranges(cows):
        all_temps = []
        all_acts = []

        for cow in cows:
            all_temps.extend(
                (cow.temps_current or []) +
                (cow.temps_station or []) +
                (cow.temps_avg or [])
            )

            all_acts.extend(
                (cow.acts_current or []) +
                (cow.acts_station or []) +
                (cow.acts_avg or [])
            )
        # None 제거
        all_temps = [v for v in all_temps if v is not None]
        all_acts = [v for v in all_acts if v is not None]
        return all_temps, all_acts
    
    @staticmethod
    def get_indices_in_range(time_seconds, x_min, x_max):
        return [
            i for i, t in enumerate(time_seconds)
            if x_min <= t <= x_max
        ]
    
    @staticmethod
    def clear_curves(entries, main_vb, activity_vb):
        for entry in entries:
            for c in entry.curves["temp"]:
                main_vb.removeItem(c)
            for c in entry.curves["activity"]:
                activity_vb.removeItem(c)

            entry.curves["temp"].clear()
            entry.curves["activity"].clear()


    @staticmethod
    def apply_y_ranges(ui):
        if ui.global_temp_range:
            y_min, y_max = ui.global_temp_range
            ui.main_vb.setYRange(y_min, y_max)

        if ui.global_act_range:
            y_min, y_max = ui.global_act_range
            ui.activity_vb.setYRange(y_min, y_max)


    @staticmethod
    def draw_entries(cls, ui, visible_entries, time_seconds):
        for entry in visible_entries:
            cls.draw_entry(ui, entry, time_seconds)

    @classmethod
    def draw_entry(cls, ui, entry, time_seconds):
        dc = entry.cow

        cls._draw_temp(ui, entry, dc, time_seconds)
        cls._draw_activity(ui, entry, dc, time_seconds)

    @staticmethod
    def _normalize_1d(values):
        if not values:
            return []

        if isinstance(values, (int, float, np.number)):
            return []

        if isinstance(values, (list, tuple, np.ndarray)):
            if len(values) == 0:
                return []

            if len(values) == 1 and isinstance(values[0], (list, tuple, np.ndarray)):
                return list(values[0])

            return list(values)

        return []
    
    @classmethod
    def _plot_series(cls, vb, time_seconds, values, pen, name):
        values_1d = cls._normalize_1d(values)

        pairs = [(t, v) for t, v in zip(time_seconds, values_1d) if v is not None]
        if not pairs:
            return None

        t, v = zip(*pairs)

        curve = pg.PlotCurveItem(
            np.asarray(t),
            np.asarray(v),
            pen=pen,
            name=name,
            clipToView=True
        )
        vb.addItem(curve)
        return curve
    
    @classmethod
    def _draw_temp(cls, ui, entry, dc, time_seconds):
        label = dc.label
        curves = []

        configs = [
            (dc.temps_current, pg.mkPen('r', width=2), "Current Temp"),
            (dc.temps_station, pg.mkPen('m', width=2, style=Qt.DashLine), "Station Temp"),
            (dc.temps_avg, pg.mkPen('orange', width=2), "Avg Temp"),
        ]

        for values, pen, name in configs:
            curve = cls._plot_series(ui.main_vb, time_seconds, values, pen, f"[{label}] {name}")
            if curve:
                curves.append(curve)

        entry.curves["temp"].extend(curves)
    
    @classmethod
    def _draw_activity(cls, ui, entry, dc, time_seconds):
        label = dc.label
        curves = []

        configs = [
            (dc.acts_current, pg.mkPen('g', width=2), "Current Activity"),
            (dc.acts_station, pg.mkPen('c', width=2, style=Qt.DashLine), "Station Activity"),
            (dc.acts_avg, pg.mkPen('b', width=2), "Avg Activity"),
        ]

        for values, pen, name in configs:
            curve = cls._plot_series(ui.activity_vb, time_seconds, values, pen, f"[{label}] {name}")
            if curve:
                curves.append(curve)

        entry.curves["activity"].extend(curves)


    @staticmethod
    def set_x_range(ui, time_seconds):
        if time_seconds:
            ui.main_vb.setXRange(0, max(time_seconds))
            ui.activity_vb.setXLink(ui.main_vb)


    @staticmethod
    def create_analysis_lines(ui, time_seconds):
        if not time_seconds:
            return None, None

        max_time = max(time_seconds)

        line_a = pg.InfiniteLine(pos=max_time * 0.25, angle=90, movable=True)
        line_b = pg.InfiniteLine(pos=max_time * 0.75, angle=90, movable=True)

        ui.graph_widget.addItem(line_a)
        ui.graph_widget.addItem(line_b)

        return line_a, line_b


    @classmethod
    def redraw(cls, ui, visible_entries, time_seconds):
        cls.clear_curves(ui.data_model.get_all_entries(), ui.main_vb, ui.activity_vb)
        cls.apply_y_ranges(ui)
        cls.draw_entries(cls, ui, visible_entries, time_seconds)
        cls.set_x_range(ui, time_seconds)

        lines = cls.create_analysis_lines(ui, time_seconds)

        QTimer.singleShot(0, ui.update_viewbox_geometries)

        return lines


    
class DataModel:
    def __init__(self):
        self._entries = {}

    # -------------------------
    # 기본 관리
    # -------------------------
    def set_entries(self, entries: dict):
        self._entries = entries
    
    def add_entry(self, key, entry):
        self._entries[key] = entry

    def clear(self):
        self._entries.clear()

    # -------------------------
    # 조회
    # -------------------------
    def get_entry(self, key):
        return self._entries.get(key)
    
    def get_all_entries(self):
        return self._entries.values()

    def get_visible_entries(self):
        """visible 플래그 기준 필터 (지금 구조에 맞게 수정 가능)"""
        return [e for e in self._entries.values() if getattr(e, "visible", True)]

    def get_primary_entry(self):
        """통계/시간 기준용 첫 entry"""
        return next(iter(self._entries.values()), None)

    # -------------------------
    # 시간 기준
    # -------------------------
    def get_time_reference(self):
        entry = self.get_primary_entry()
        if not entry:
            return None, None

        dc = entry.cow
        if not dc.timestamps:
            return None, None

        start_time = dc.timestamps[0]
        time_seconds = [(ts - start_time).total_seconds() for ts in dc.timestamps]

        return start_time, time_seconds