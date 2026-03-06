"""USCS/AASHTO 기준 토질 분류 모듈."""

from __future__ import annotations

from ..models.schemas import LabTestResult


class SoilClassifier:
    """USCS 및 AASHTO 기준에 따라 토질을 분류하는 클래스."""

    def classify_uscs(self, result: LabTestResult) -> str:
        """USCS(통일분류법) 기준으로 토질을 분류한다.

        Args:
            result: 실내시험 성과 데이터

        Returns:
            USCS 분류 기호 (예: CL, SM, GP, CH 등)
        """
        pass

    def classify_aashto(self, result: LabTestResult) -> str:
        """AASHTO 기준으로 토질을 분류한다.

        Args:
            result: 실내시험 성과 데이터

        Returns:
            AASHTO 분류 기호 (예: A-1-a, A-4, A-7-6 등)
        """
        pass

    def classify_batch(
        self, results: list[LabTestResult], method: str = "uscs"
    ) -> list[str]:
        """여러 시험 결과를 일괄 분류한다.

        Args:
            results: LabTestResult 목록
            method: 분류 기준 ("uscs" 또는 "aashto")

        Returns:
            분류 기호 목록
        """
        pass

    def _classify_coarse_grained(self, ll: float, pi: float, fines: float) -> str:
        """조립토(자갈/모래)를 세부 분류한다.

        Args:
            ll: 액성한계 (%)
            pi: 소성지수 (%)
            fines: 세립분 함유율 (%)

        Returns:
            USCS 분류 기호
        """
        pass

    def _classify_fine_grained(self, ll: float, pi: float) -> str:
        """세립토(실트/점토)를 세부 분류한다.

        Args:
            ll: 액성한계 (%)
            pi: 소성지수 (%)

        Returns:
            USCS 분류 기호
        """
        pass

    def get_description(self, uscs_symbol: str) -> str:
        """USCS 기호에 대한 한국어 설명을 반환한다.

        Args:
            uscs_symbol: USCS 분류 기호

        Returns:
            토질 분류 한국어 설명
        """
        pass
