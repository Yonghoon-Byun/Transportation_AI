"""Excel 보고서 생성 모듈."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class ExcelGenerator:
    """Excel 보고서 생성기 (openpyxl 기반)."""

    def __init__(self, title: str = "") -> None:
        self.title = title
        self._sheets: dict[str, pd.DataFrame] = {}

    def add_sheet(self, name: str, df: pd.DataFrame) -> None:
        """시트 추가."""
        self._sheets[name] = df

    def add_summary_sheet(self, stats: dict[str, Any]) -> None:
        """요약 통계 시트 생성."""
        raise NotImplementedError

    def apply_style(
        self,
        sheet_name: str,
        header_color: str = "4472C4",
        freeze_panes: str = "A2",
    ) -> None:
        """셀 스타일 적용 (헤더 색상, 고정 행)."""
        raise NotImplementedError

    def embed_chart(self, sheet_name: str, chart_data: dict[str, Any]) -> None:
        """차트 삽입."""
        raise NotImplementedError

    def build(self, output_path: str | Path) -> Path:
        """Excel 파일 생성 및 저장."""
        raise NotImplementedError

    def to_bytes(self) -> bytes:
        """메모리 내 Excel 바이트 반환 (Streamlit 다운로드용)."""
        raise NotImplementedError
