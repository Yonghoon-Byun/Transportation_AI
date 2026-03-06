"""암반 분류 모듈 - RQD, RMR, SMR, TCR 기반 암반 품질 평가.

PDF 기획서 기반:
- RQD: 암질지수 등급 분류
- RMR: Rock Mass Rating (암석강도, RQD, 절리간격, 절리상태, 지하수)
- SMR: Slope Mass Rating (비탈면 암반 안정성)
- TCR: Total Core Recovery 평가
"""

from __future__ import annotations

from ..models.schemas import BoreholeLog, SoilLayer


class RockClassifier:
    """RQD, RMR, SMR, TCR 지표를 활용하여 암반을 분류하는 클래스."""

    def classify_rqd(self, rqd: float) -> str:
        """RQD(암질지수) 값에 따라 암반을 등급 분류한다.

        Args:
            rqd: Rock Quality Designation (%)

        Returns:
            암반 등급 (예: Very Poor, Poor, Fair, Good, Excellent)
        """
        pass

    def classify_rmr(
        self,
        ucs: float,
        rqd: float,
        spacing: float,
        condition: int,
        gwl_rating: int,
    ) -> tuple[float, str]:
        """RMR(암반 질량 평점법) 기준으로 암반을 분류한다.

        Args:
            ucs: 일축압축강도 (MPa)
            rqd: RQD (%)
            spacing: 불연속면 간격 (m)
            condition: 불연속면 상태 평점 (0~30)
            gwl_rating: 지하수 상태 평점 (0~15)

        Returns:
            (RMR 총점, 암반 등급) 튜플
        """
        pass

    def classify_smr(
        self,
        rmr: float,
        f1: float,
        f2: float,
        f3: float,
        f4: float,
    ) -> tuple[float, str]:
        """SMR(비탈면 암반 질량 평점법) 기준으로 암반 비탈면을 분류한다.

        SMR = RMR - (F1 * F2 * F3) + F4

        Args:
            rmr: 기본 RMR 값
            f1: 불연속면과 비탈면 주향 관계 (0.15~1.0)
            f2: 불연속면 경사 (0.15~1.0)
            f3: 불연속면-비탈면 경사 관계 (-60~0)
            f4: 굴착 방법 보정 (-8~+15)

        Returns:
            (SMR 점수, 안정성 등급) 튜플
        """
        pass

    def classify_tcr(self, tcr: float) -> str:
        """TCR(전코어회수율) 값에 따라 암반 회수 상태를 평가한다.

        Args:
            tcr: Total Core Recovery (%)

        Returns:
            코어 회수 상태 평가 문자열
        """
        pass

    def evaluate_rock_layers(self, borehole: BoreholeLog) -> list[dict[str, str]]:
        """주상도 데이터에서 암반층만 추출하여 종합 암반 평가를 수행한다.

        Args:
            borehole: BoreholeLog 데이터 (layers 내 is_rock=True인 층)

        Returns:
            각 암반층의 RQD 등급, TCR 상태 등을 담은 평가 결과 목록
        """
        pass

    def _get_ucs_rating(self, ucs: float) -> int:
        """일축압축강도에 대한 RMR 평점을 반환한다.

        Args:
            ucs: 일축압축강도 (MPa)

        Returns:
            RMR 평점 (0~15)
        """
        pass

    def _get_rqd_rating(self, rqd: float) -> int:
        """RQD에 대한 RMR 평점을 반환한다.

        Args:
            rqd: RQD (%)

        Returns:
            RMR 평점 (3~20)
        """
        pass
