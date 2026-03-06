"""사회경제지표 전처리 모듈."""

from __future__ import annotations

import pandas as pd

from src.collector.models import SocioeconomicData


class SocioeconomicPreprocessor:
    """사회경제지표 전처리기."""

    def to_dataframe(self, records: list[SocioeconomicData]) -> pd.DataFrame:
        """SocioeconomicData 리스트 → DataFrame 변환."""
        raise NotImplementedError

    def fill_missing(self, df: pd.DataFrame, method: str = "interpolate") -> pd.DataFrame:
        """결측값 처리 (interpolate / ffill / mean)."""
        raise NotImplementedError

    def compute_growth_rate(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """전년 대비 증감률 계산."""
        raise NotImplementedError

    def merge_with_zones(
        self,
        df: pd.DataFrame,
        zone_df: pd.DataFrame,
        on: str = "region_code",
    ) -> pd.DataFrame:
        """존 정보와 조인."""
        raise NotImplementedError

    def normalize_per_capita(self, df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        """인구 1인당 지표 계산."""
        raise NotImplementedError
