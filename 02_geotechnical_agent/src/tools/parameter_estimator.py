"""설계지반정수 산정 모듈 - 경험식 및 상관관계를 활용한 지반정수 추정."""

from __future__ import annotations

from typing import Any

from ..models.schemas import DesignParameter, LabTestResult, MechanicalTestResult


class ParameterEstimator:
    """경험식 기반으로 설계지반정수를 산정하는 클래스.

    SPT N값, 실내시험 결과 등으로부터 단위중량, 점착력, 내부마찰각, 탄성계수를 추정.
    """

    def estimate_from_n_value(
        self, n_value: int, soil_type: str
    ) -> dict[str, float]:
        """SPT N값으로부터 지반정수를 추정한다 (경험식 적용).

        Args:
            n_value: 표준관입시험 N값
            soil_type: 토질 분류 (예: "sand", "clay", "gravel")

        Returns:
            추정된 지반정수 딕셔너리 (phi, c, E, gamma 등)
        """
        pass

    def estimate_unit_weight(
        self, gs: float, wn: float, uscs: str
    ) -> float:
        """비중과 함수비로부터 단위중량을 추정한다.

        Args:
            gs: 비중
            wn: 함수비 (%)
            uscs: USCS 분류 기호

        Returns:
            추정 단위중량 (kN/m³)
        """
        pass

    def estimate_friction_angle(
        self, n_value: int, overburden_pressure: float | None = None
    ) -> float:
        """SPT N값으로부터 내부마찰각을 추정한다 (Peck, Hanson, Thornburn 공식).

        Args:
            n_value: SPT N값
            overburden_pressure: 유효상재압 (kPa). None이면 보정 미적용.

        Returns:
            추정 내부마찰각 (degree)
        """
        pass

    def estimate_cohesion(
        self, qu: float | None = None, n_value: int | None = None
    ) -> float:
        """일축압축강도 또는 N값으로부터 점착력을 추정한다.

        Args:
            qu: 일축압축강도 (kPa). 우선 적용.
            n_value: SPT N값. qu가 없을 때 사용.

        Returns:
            추정 점착력 (kPa)
        """
        pass

    def estimate_elastic_modulus(
        self, n_value: int, soil_type: str
    ) -> float:
        """SPT N값으로부터 탄성계수를 추정한다.

        Args:
            n_value: SPT N값
            soil_type: 토질 분류

        Returns:
            추정 탄성계수 (MPa)
        """
        pass

    def build_design_parameters(
        self,
        layer_name: str,
        stats: dict[str, float],
        lab_results: list[LabTestResult] | None = None,
        mechanical_results: list[MechanicalTestResult] | None = None,
    ) -> DesignParameter:
        """통계량 및 시험 결과를 종합하여 DesignParameter를 생성한다.

        Args:
            layer_name: 지층명
            stats: 지층별 N값 통계량 딕셔너리
            lab_results: 해당 지층 실내시험 결과 목록
            mechanical_results: 해당 지층 역학시험 결과 목록

        Returns:
            산정된 DesignParameter 객체
        """
        pass
