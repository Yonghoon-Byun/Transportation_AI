"""메인 지반조사 AI Agent 코어 모듈 - LLM 기반 분석 및 해석."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class GeotechnicalAgent:
    """LLM을 활용하여 지반조사 보고서를 자동 분석·해석하는 AI Agent 클래스."""

    def __init__(
        self,
        model: str = "claude-opus-4-6",
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> None:
        """초기화.

        Args:
            model: 사용할 LLM 모델 ID
            temperature: 생성 온도 (0.0 ~ 1.0)
            max_tokens: 최대 생성 토큰 수
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def analyze_report(self, report_path: str | Path) -> dict[str, Any]:
        """지반조사 보고서를 종합 분석한다.

        Args:
            report_path: 보고서 파일 경로 (PDF 또는 Excel)

        Returns:
            지층 구성, 설계정수, 이상치, 종합 의견을 담은 분석 결과 딕셔너리
        """
        pass

    def interpret_spt(self, n_values: list[int], layer_name: str) -> str:
        """SPT N값을 해석하여 지층 강도 특성을 서술한다.

        Args:
            n_values: SPT N값 목록
            layer_name: 지층명

        Returns:
            LLM이 생성한 지층 강도 해석 텍스트
        """
        pass

    def recommend_design_parameters(
        self, layer_name: str, test_results: list[dict[str, Any]]
    ) -> dict[str, float]:
        """시험 결과를 바탕으로 설계지반정수를 추천한다.

        Args:
            layer_name: 지층명
            test_results: 관련 시험 결과 목록

        Returns:
            추천 설계정수 딕셔너리 (단위중량, c, phi, E 등)
        """
        pass

    def generate_summary(self, analysis_results: dict[str, Any]) -> str:
        """분석 결과를 바탕으로 보고서용 종합 요약을 생성한다.

        Args:
            analysis_results: 전체 분석 결과 딕셔너리

        Returns:
            LLM이 생성한 종합 요약 텍스트
        """
        pass

    def _build_prompt(self, template_name: str, context: dict[str, Any]) -> str:
        """프롬프트 템플릿을 로드하고 컨텍스트를 채워 완성 프롬프트를 반환한다.

        Args:
            template_name: prompts/ 폴더의 템플릿 파일명
            context: 템플릿에 채울 변수 딕셔너리

        Returns:
            완성된 프롬프트 문자열
        """
        pass

    def _call_llm(self, prompt: str) -> str:
        """LLM API를 호출하여 응답을 반환한다.

        Args:
            prompt: 완성된 프롬프트 문자열

        Returns:
            LLM 응답 텍스트
        """
        pass
