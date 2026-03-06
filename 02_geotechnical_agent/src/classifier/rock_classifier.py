"""암반 분류 모듈 - RQD, RMR, TCR 기반 암반 품질 평가."""

from __future__ import annotations

from ..models.schemas import BoreholeLog


class RockClassifier:
    """RQD, RMR, TCR 지표를 활용하여 암반을 분류하는 클래스."""

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

    def classify_tcr(self, tcr: float) -> str:
        """TCR(전코어회수율) 값에 따라 암반 회수 상태를 평가한다.

        Args:
            tcr: Total Core Recovery (%)

        Returns:
            코어 회수 상태 평가 문자열
        """
        pass

    def evaluate_from_borehole(self, log: BoreholeLog) -> dict[str, str]:
        """주상도 데이터로부터 종합 암반 평가를 수행한다.

        Args:
            log: BoreholeLog 데이터 (RQD, TCR 포함)

        Returns:
            RQD 등급, TCR 상태 등을 담은 평가 결과 딕셔너리
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
