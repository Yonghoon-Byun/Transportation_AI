"""USCS/AASHTO 기준 토질 분류 모듈.

PDF 기획서 기반:
- USCS 통일분류법: 조립토(GW/GP/GM/GC/SW/SP/SM/SC), 세립토(ML/CL/OL/MH/CH/OH/Pt)
- AASHTO 분류: A-1 ~ A-7 그룹 분류
- 소성도 차트(Plasticity Chart) 로직 포함
"""

from __future__ import annotations

from ..models.schemas import PhysicalProperties


class SoilClassifier:
    """USCS 및 AASHTO 기준에 따라 토질을 분류하는 클래스."""

    def classify_uscs(self, props: PhysicalProperties) -> str:
        """USCS(통일분류법) 기준으로 토질을 분류한다.

        Args:
            props: 물리시험 성과 데이터

        Returns:
            USCS 분류 기호 (예: CL, SM, GP, CH 등)
        """
        pass

    def classify_aashto(self, props: PhysicalProperties) -> str:
        """AASHTO 기준으로 토질을 분류한다.

        Args:
            props: 물리시험 성과 데이터

        Returns:
            AASHTO 분류 기호 (예: A-1-a, A-4, A-7-6 등)
        """
        pass

    def classify_batch(
        self, props_list: list[PhysicalProperties], method: str = "uscs"
    ) -> list[str]:
        """여러 시험 결과를 일괄 분류한다.

        Args:
            props_list: PhysicalProperties 목록
            method: 분류 기준 ("uscs" 또는 "aashto")

        Returns:
            분류 기호 목록
        """
        pass

    def _classify_coarse_grained(
        self, gravel_pct: float, sand_pct: float, fines_pct: float,
        ll: float | None, pi: float | None
    ) -> str:
        """조립토(자갈/모래)를 세부 분류한다.

        Args:
            gravel_pct: 자갈 함유율 (%)
            sand_pct: 모래 함유율 (%)
            fines_pct: 세립분 함유율 (%)
            ll: 액성한계 (%)
            pi: 소성지수 (%)

        Returns:
            USCS 분류 기호
        """
        pass

    def _classify_fine_grained(self, ll: float, pi: float) -> str:
        """세립토(실트/점토)를 세부 분류한다.

        소성도 차트(Plasticity Chart) A-line 기준:
        - A-line 위: 점토 (CL/CH)
        - A-line 아래: 실트 (ML/MH)
        - A-line: PI = 0.73 * (LL - 20)

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
