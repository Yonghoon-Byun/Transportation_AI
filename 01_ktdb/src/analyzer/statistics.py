"""통계 분석 모듈."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DescriptiveStats:
    """기술통계량."""

    mean: float
    median: float
    std: float
    min: float
    max: float
    q1: float
    q3: float
    skewness: float
    kurtosis: float


class StatisticsAnalyzer:
    """교통 데이터 통계 분석기."""

    def describe(self, series: pd.Series) -> DescriptiveStats:
        """기술통계량 계산."""
        raise NotImplementedError

    def correlation_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """상관관계 행렬 계산."""
        raise NotImplementedError

    def time_series_decompose(
        self,
        series: pd.Series,
        period: int = 12,
    ) -> dict[str, pd.Series]:
        """시계열 분해 (추세/계절성/잔차)."""
        raise NotImplementedError

    def growth_rate(self, series: pd.Series, periods: int = 1) -> pd.Series:
        """증감률 계산."""
        raise NotImplementedError

    def rank_by_volume(self, df: pd.DataFrame, value_col: str, top_n: int = 10) -> pd.DataFrame:
        """통행량 기준 순위 산출."""
        raise NotImplementedError

    def detect_outliers_iqr(self, series: pd.Series) -> pd.Series:
        """IQR 기반 이상값 탐지 (bool 마스크 반환)."""
        raise NotImplementedError

    def regression(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        method: str = "ols",
    ) -> dict[str, float]:
        """회귀 분석 (OLS / Ridge / Lasso)."""
        raise NotImplementedError
