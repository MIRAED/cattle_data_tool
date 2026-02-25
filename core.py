from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from collections import defaultdict
from datetime import date
from pathlib import Path
from datetime import date
from PySide6.QtCore import Qt, QTimer

@dataclass(frozen=True)
class Metric:
    group: str      # temp / activity
    kind: str       # current / station / avg

    @property
    def key(self):
        return f"{self.group}_{self.kind}"
    
    @property
    def label(self):
        return f"{self.group.capitalize()} {self.kind.capitalize()}"
    
ALL_METRICS = [
    Metric("temps", "current"),
    Metric("temps", "station"),
    Metric("temps", "avg"),
    Metric("acts", "current"),
    Metric("acts", "station"),
    Metric("acts", "avg"),
]


class DatasetEntry:
    def __init__(self, cow: CowData):
        self.cow = cow
        self.label = cow.label

        # 데이터 전체 on/off
        self.visible = True
        self.checkbox = None

        # metric 단위 visible
        self.metric_visible = {
            metric.key: True for metric in ALL_METRICS
        }

        # metric별 curve 저장
        self.curves = {}

    def set_metric_visible(self, metric_key, state: bool):
        self.metric_visible[metric_key] = state

    def is_metric_visible(self, metric_key):
        return self.metric_visible.get(metric_key, False)
    
    def get_metric_data(self, metric_key: str):
        """
        metric_key 예:
        - temps_current
        - acts_avg
        """
        return getattr(self.cow, metric_key, None)

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

@dataclass
class DrawCommand:
    entry: DatasetEntry
    metric_key: str
    x: list
    y: list
    visible: bool

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
    
    
    
    @classmethod
    def prepare_draw_commands(cls, visible_entries, time_seconds):
        commands = []

        for entry in visible_entries:
            for metric in ALL_METRICS:
                metric_key = metric.key

                print(
                    "METRIC VIS:",
                    metric_key,
                    entry.visible,
                    entry.is_metric_visible(metric_key)
                )

                visible = entry.visible and entry.is_metric_visible(metric_key)

                y_values = entry.get_metric_data(metric_key) if visible else None

                print(
                    metric_key,
                    len(time_seconds),
                    len(y_values) if y_values else None
                )

                commands.append({
                    "entry": entry,
                    "metric": metric_key,
                    "visible": visible,
                    "x": time_seconds if visible else None,
                    "y": y_values
                })

        return commands
 
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