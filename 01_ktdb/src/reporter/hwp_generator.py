"""HWP 보고서 생성 모듈."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ReportSection:
    """보고서 섹션."""

    title: str
    content: str = ""
    tables: list[pd.DataFrame] = field(default_factory=list)
    chart_paths: list[str] = field(default_factory=list)


@dataclass
class ReportConfig:
    """보고서 설정."""

    title: str
    subtitle: str = ""
    author: str = ""
    department: str = ""
    template_path: str | None = None


class HWPGenerator:
    """HWP 보고서 생성기 (pyhwpx 기반)."""

    def __init__(self, config: ReportConfig) -> None:
        self.config = config
        self._sections: list[ReportSection] = []

    def add_section(self, section: ReportSection) -> None:
        """섹션 추가."""
        self._sections.append(section)

    def add_cover_page(self, metadata: dict[str, Any]) -> None:
        """표지 페이지 생성."""
        raise NotImplementedError

    def add_table(self, section_idx: int, df: pd.DataFrame, caption: str = "") -> None:
        """섹션에 표 삽입."""
        raise NotImplementedError

    def add_chart(self, section_idx: int, chart_path: str, caption: str = "") -> None:
        """섹션에 차트 이미지 삽입."""
        raise NotImplementedError

    def build(self, output_path: str | Path) -> Path:
        """HWP 파일 생성 및 저장."""
        raise NotImplementedError

    def preview_html(self) -> str:
        """HTML 미리보기 생성."""
        raise NotImplementedError
