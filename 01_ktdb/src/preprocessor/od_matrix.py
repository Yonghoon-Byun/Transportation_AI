"""OD 매트릭스 전처리 모듈."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.collector.models import ODMatrixData


class ODMatrixPreprocessor:
    """OD 매트릭스 전처리기."""

    def __init__(self, fill_diagonal_zero: bool = True) -> None:
        self.fill_diagonal_zero = fill_diagonal_zero

    def to_dataframe(self, data: ODMatrixData) -> pd.DataFrame:
        """ODMatrixData → 롱 포맷 DataFrame 변환."""
        raise NotImplementedError

    def to_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """롱 포맷 DataFrame → 매트릭스 변환."""
        raise NotImplementedError

    def normalize(self, matrix: np.ndarray, method: str = "row") -> np.ndarray:
        """매트릭스 정규화 (row / column / total)."""
        raise NotImplementedError

    def remove_outliers(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """이상값 제거 (z-score 기반)."""
        raise NotImplementedError

    def aggregate_by_region(
        self,
        df: pd.DataFrame,
        region_mapping: dict[str, str],
    ) -> pd.DataFrame:
        """존 단위 → 권역 단위 집계."""
        raise NotImplementedError

    def pivot(self, df: pd.DataFrame) -> pd.DataFrame:
        """롱 포맷 → 피벗 테이블 변환."""
        raise NotImplementedError
