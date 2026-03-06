"""자연어 쿼리 기반 데이터 분석 엔진."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class QueryResult:
    """쿼리 분석 결과."""

    query: str
    intent: str
    data: pd.DataFrame | None
    summary: str
    chart_type: str | None = None
    metadata: dict[str, Any] | None = None


class QueryEngine:
    """자연어 쿼리 → 데이터 분석 엔진."""

    def __init__(self, llm_model: str = "gpt-4o-mini") -> None:
        self.llm_model = llm_model
        self._data_registry: dict[str, pd.DataFrame] = {}

    def register_dataset(self, name: str, df: pd.DataFrame) -> None:
        """분석 대상 데이터셋 등록."""
        self._data_registry[name] = df

    def parse_intent(self, query: str) -> dict[str, Any]:
        """자연어 쿼리 의도 파싱."""
        raise NotImplementedError

    def execute(self, query: str) -> QueryResult:
        """쿼리 실행 → 결과 반환."""
        raise NotImplementedError

    def generate_summary(self, data: pd.DataFrame, intent: dict[str, Any]) -> str:
        """분석 결과 자연어 요약 생성."""
        raise NotImplementedError

    def suggest_chart_type(self, intent: dict[str, Any]) -> str:
        """의도에 맞는 차트 타입 추천."""
        raise NotImplementedError
