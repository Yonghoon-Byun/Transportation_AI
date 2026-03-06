"""지층별 통계 분석 모듈 - 평균, 표준편차, 분산 등 기술통계 산출."""

from __future__ import annotations

import math
import statistics
from typing import Any


class LayerStatistics:
    """지층별 지반정수의 기술통계량을 산출하는 클래스."""

    def compute(self, values: list[float]) -> dict[str, float]:
        """수치 목록에 대한 기술통계량을 산출한다.

        Args:
            values: 통계 분석할 수치 데이터 목록

        Returns:
            mean, std, variance, min, max, count, cv(변동계수) 등을 담은 딕셔너리
        """
        pass

    def compute_by_layer(
        self,
        layer_data: dict[str, list[float]],
    ) -> dict[str, dict[str, float]]:
        """지층별로 기술통계량을 일괄 산출한다.

        Args:
            layer_data: 지층명을 키, 수치 목록을 값으로 하는 딕셔너리

        Returns:
            지층명을 키, 통계량 딕셔너리를 값으로 하는 딕셔너리
        """
        pass

    def compute_n_value_stats(
        self,
        grouped_data: dict[str, list[dict[str, Any]]],
    ) -> dict[str, dict[str, float]]:
        """지층별 SPT N값 통계량을 산출한다.

        Args:
            grouped_data: 지층별 그룹화된 주상도 데이터

        Returns:
            지층명을 키, N값 통계량을 값으로 하는 딕셔너리
        """
        pass

    def compute_confidence_interval(
        self,
        values: list[float],
        confidence: float = 0.95,
    ) -> tuple[float, float]:
        """수치 목록에 대한 신뢰구간을 산출한다.

        Args:
            values: 수치 데이터 목록
            confidence: 신뢰수준 (기본 0.95 = 95%)

        Returns:
            (하한, 상한) 신뢰구간 튜플
        """
        pass

    def characteristic_value(
        self,
        values: list[float],
        conservative_factor: float = 0.05,
    ) -> float:
        """유로코드 기반 특성값(characteristic value)을 산출한다.

        평균에서 변동을 고려한 보수적 설계값을 반환한다.

        Args:
            values: 수치 데이터 목록
            conservative_factor: 보수율 (기본 5% 하한)

        Returns:
            특성값
        """
        pass
