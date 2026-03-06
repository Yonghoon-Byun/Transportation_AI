"""그래프/차트 생성 모듈."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go


class ChartBuilder:
    """교통 데이터 차트 빌더."""

    DEFAULT_TEMPLATE = "plotly_white"

    def bar(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        title: str = "",
        **kwargs: Any,
    ) -> go.Figure:
        """막대 차트 생성."""
        raise NotImplementedError

    def line(
        self,
        df: pd.DataFrame,
        x: str,
        y: str | list[str],
        title: str = "",
        **kwargs: Any,
    ) -> go.Figure:
        """선 그래프 생성."""
        raise NotImplementedError

    def heatmap(
        self,
        matrix: pd.DataFrame,
        title: str = "",
        colorscale: str = "Blues",
        **kwargs: Any,
    ) -> go.Figure:
        """히트맵 생성 (OD 매트릭스 시각화용)."""
        raise NotImplementedError

    def scatter(
        self,
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str | None = None,
        title: str = "",
        **kwargs: Any,
    ) -> go.Figure:
        """산점도 생성."""
        raise NotImplementedError

    def choropleth(
        self,
        df: pd.DataFrame,
        geojson: dict[str, Any],
        locations: str,
        value: str,
        title: str = "",
        **kwargs: Any,
    ) -> go.Figure:
        """단계구분도 생성."""
        raise NotImplementedError

    def save(self, fig: go.Figure, path: str, fmt: str = "html") -> None:
        """차트 파일 저장 (html / png / svg)."""
        raise NotImplementedError
