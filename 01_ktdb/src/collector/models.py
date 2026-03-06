"""수집 데이터 모델 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ODMatrixData:
    """OD 매트릭스 데이터."""

    year: int
    zone_system: str
    trip_purpose: str
    matrix: list[list[float]] = field(default_factory=list)
    zone_codes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ZoneInfo:
    """존 정보."""

    zone_code: str
    zone_name: str
    region_code: str
    centroid_lat: float | None = None
    centroid_lon: float | None = None


@dataclass
class SocioeconomicData:
    """사회경제지표 데이터."""

    year: int
    region_code: str
    region_name: str
    population: int | None = None
    employment: int | None = None
    vehicle_count: int | None = None
    gdp: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class APIResponse:
    """API 응답 래퍼."""

    success: bool
    data: Any
    total_count: int = 0
    page: int = 1
    message: str = ""
