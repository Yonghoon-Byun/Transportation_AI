"""표/테이블 생성 모듈."""

from __future__ import annotations

from typing import Any

import pandas as pd


class TableBuilder:
    """교통 데이터 표 빌더."""

    def summary_table(
        self,
        df: pd.DataFrame,
        columns: list[str] | None = None,
        max_rows: int = 20,
    ) -> pd.DataFrame:
        """요약 테이블 생성."""
        raise NotImplementedError

    def ranking_table(
        self,
        df: pd.DataFrame,
        value_col: str,
        label_col: str,
        top_n: int = 10,
        ascending: bool = False,
    ) -> pd.DataFrame:
        """순위 테이블 생성."""
        raise NotImplementedError

    def pivot_table(
        self,
        df: pd.DataFrame,
        index: str,
        columns: str,
        values: str,
        aggfunc: str = "sum",
    ) -> pd.DataFrame:
        """피벗 테이블 생성."""
        raise NotImplementedError

    def format_number(self, df: pd.DataFrame, cols: list[str], decimals: int = 1) -> pd.DataFrame:
        """숫자 컬럼 포맷팅 (천단위 구분, 소수점)."""
        raise NotImplementedError

    def to_html(self, df: pd.DataFrame, **kwargs: Any) -> str:
        """DataFrame → HTML 테이블 변환."""
        raise NotImplementedError

    def to_markdown(self, df: pd.DataFrame) -> str:
        """DataFrame → Markdown 테이블 변환."""
        raise NotImplementedError
