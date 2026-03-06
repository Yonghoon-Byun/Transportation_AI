"""이상치 탐지 모듈 - 지반조사 데이터의 통계적 이상치 감지."""

from __future__ import annotations

import statistics
from typing import Any


class OutlierDetector:
    """IQR, Z-Score 등 통계 기법으로 지반 데이터 이상치를 탐지하는 클래스."""

    def __init__(self, method: str = "iqr", threshold: float = 1.5) -> None:
        """초기화.

        Args:
            method: 이상치 탐지 방법 ("iqr" 또는 "zscore")
            threshold: IQR 방법의 경우 배수(기본 1.5), Z-Score의 경우 기준값(기본 3.0)
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
        """Z-Score 기반으로 이상치를 탐지한다.

        Args:
            values: 검사할 수치 데이터 목록

        Returns:
            이상치 인덱스 목록
        """
        pass

    def detect_n_value_outliers(
        self, n_values: list[float], layer_name: str
    ) -> dict[str, Any]:
        """지층별 SPT N값의 이상치를 탐지하고 결과를 보고한다.

        Args:
            n_values: SPT N값 목록
            layer_name: 지층명

        Returns:
            이상치 인덱스, 이상치 값, 통계 정보를 담은 딕셔너리
        """
        pass

    def flag_outliers(
        self, data: list[dict[str, Any]], field: str
    ) -> list[dict[str, Any]]:
        """데이터 목록의 특정 필드에 이상치 플래그를 추가한다.

        Args:
            data: 딕셔너리 형태의 데이터 목록
            field: 이상치 검사할 필드명

        Returns:
            is_outlier 키가 추가된 데이터 목록
        """
        pass
