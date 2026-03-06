"""이상치 탐지 모듈 - 지반조사 데이터의 통계적·공학적 이상치 감지.

PDF 기획서 기반:
- 통계적 탐지: IQR, Z-Score
- 공학적 범위 기반 탐지: 지층별 N치 범위, qu 범위, 물성치 범위
- 경고 레벨: WARNING / ERROR / CRITICAL
"""

from __future__ import annotations

import statistics
from typing import Any

from ..models.schemas import AnomalyWarning


class OutlierDetector:
    """IQR, Z-Score 및 공학적 범위 기반으로 지반 데이터 이상치를 탐지하는 클래스."""

    def __init__(self, method: str = "iqr", threshold: float = 1.5) -> None:
        """초기화.

        Args:
            method: 이상치 탐지 방법 ("iqr" 또는 "zscore")
            threshold: IQR 방법의 경우 배수(기본 1.5), Z-Score의 경우 기준값(기본 2.5)
        """
        self.method = method
        self.threshold = threshold

    def detect(self, values: list[float]) -> list[int]:
        """수치 목록에서 이상치 인덱스를 반환한다.

        Args:
            values: 검사할 수치 데이터 목록

        Returns:
            이상치 인덱스 목록
        """
        pass

    def detect_by_iqr(self, values: list[float]) -> list[int]:
        """IQR(사분위 범위) 기반으로 이상치를 탐지한다.

        Args:
            values: 검사할 수치 데이터 목록

        Returns:
            이상치 인덱스 목록
        """
        pass

    def detect_by_zscore(self, values: list[float]) -> list[int]:
        """Z-Score 기반으로 이상치를 탐지한다 (|Z| > threshold).

        Args:
            values: 검사할 수치 데이터 목록

        Returns:
            이상치 인덱스 목록
        """
        pass

    def detect_engineering_outliers(
        self,
        hole_no: str,
        depth: float,
        parameter: str,
        value: float,
    ) -> AnomalyWarning | None:
        """공학적 범위 기반으로 이상치를 탐지한다.

        기획서 기반 기준 범위:
        - N치: 지층별 범위 (매립층 2~20, 충적모래 4~40 등)
        - γt: 14~22 kN/m3
        - φ: 0~45° (토사)
        - c: ≥0 kPa
        - qu: 암반 종류별 범위

        Args:
            hole_no: 시추공 번호
            depth: 심도 (m)
            parameter: 파라미터명
            value: 실측값

        Returns:
            이상치인 경우 AnomalyWarning, 아니면 None
        """
        pass

    def detect_n_value_outliers(
        self, n_values: list[float], layer_name: str, hole_no: str = ""
    ) -> list[AnomalyWarning]:
        """지층별 SPT N값의 이상치를 탐지하고 AnomalyWarning 목록을 반환한다.

        Args:
            n_values: SPT N값 목록
            layer_name: 지층명
            hole_no: 시추공 번호

        Returns:
            AnomalyWarning 목록
        """
        pass

    def validate_depth_monotonic(
        self, depths: list[float], hole_no: str
    ) -> list[AnomalyWarning]:
        """심도 단조증가 검증 (역전 오류 탐지).

        Args:
            depths: 심도 목록
            hole_no: 시추공 번호

        Returns:
            역전 오류 AnomalyWarning 목록
        """
        pass

    def validate_layer_thickness(
        self, layers_thickness_sum: float, total_depth: float, hole_no: str
    ) -> AnomalyWarning | None:
        """층 두께 합산 = 총 심도 검증.

        Args:
            layers_thickness_sum: 지층 두께 합계
            total_depth: 시추 총 심도
            hole_no: 시추공 번호

        Returns:
            불일치 시 AnomalyWarning, 정상이면 None
        """
        pass
