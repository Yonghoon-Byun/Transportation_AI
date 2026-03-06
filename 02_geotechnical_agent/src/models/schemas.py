"""지반조사 데이터 모델 스키마 - BoreholeLog, LabTestResult 등 dataclass 정의."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BoreholeLog:
    """시추주상도 데이터 모델.

    Attributes:
        hole_no: 시추공 번호 (예: BH-1)
        depth_from: 층 상단 심도 (m)
        depth_to: 층 하단 심도 (m)
        layer_name: 지층명 (예: 매립층, 퇴적층, 풍화토 등)
        n_value: 표준관입시험(SPT) N값
        gwl: 지하수위 (m, 해당 없으면 None)
        rqd: Rock Quality Designation (%)
        tcr: Total Core Recovery (%)
    """

    hole_no: str
    depth_from: float
    depth_to: float
    layer_name: str
    n_value: Optional[int] = None
    gwl: Optional[float] = None
    rqd: Optional[float] = None
    tcr: Optional[float] = None


@dataclass
class LabTestResult:
    """실내시험 성과 데이터 모델 (기본 물성 시험).

    Attributes:
        hole_no: 시추공 번호
        depth: 시료 채취 심도 (m)
        test_type: 시험 종류 (예: 입도분석, 아터버그한계 등)
        wn: 함수비 (%)
        gs: 비중
        ll: 액성한계 (%)
        pi: 소성지수 (%)
        grain_size_dist: 입도분포 (dict 형태, 예: {"D10": 0.1, "D50": 0.5})
        uscs: USCS 분류 기호 (예: CL, SM, GP 등)
    """

    hole_no: str
    depth: float
    test_type: str
    wn: Optional[float] = None
    gs: Optional[float] = None
    ll: Optional[float] = None
    pi: Optional[float] = None
    grain_size_dist: dict = field(default_factory=dict)
    uscs: Optional[str] = None


@dataclass
class MechanicalTestResult:
    """역학적 시험 성과 데이터 모델 (전단강도 시험).

    Attributes:
        hole_no: 시추공 번호
        depth: 시료 채취 심도 (m)
        qu: 일축압축강도 (kPa)
        cohesion_c: 점착력 c (kPa)
        friction_angle_phi: 내부마찰각 phi (degree)
    """

    hole_no: str
    depth: float
    qu: Optional[float] = None
    cohesion_c: Optional[float] = None
    friction_angle_phi: Optional[float] = None


@dataclass
class ConsolidationResult:
    """압밀시험 성과 데이터 모델.

    Attributes:
        hole_no: 시추공 번호
        depth: 시료 채취 심도 (m)
        cc: 압축지수 Cc
        cr: 팽창지수 Cr
        pc: 선행압밀하중 (kPa)
        cv: 압밀계수 Cv (cm²/sec)
        e0: 초기 간극비 e0
    """

    hole_no: str
    depth: float
    cc: Optional[float] = None
    cr: Optional[float] = None
    pc: Optional[float] = None
    cv: Optional[float] = None
    e0: Optional[float] = None


@dataclass
class DesignParameter:
    """설계지반정수 데이터 모델.

    Attributes:
        layer_name: 지층명
        unit_weight: 단위중량 (kN/m³)
        c: 점착력 (kPa)
        phi: 내부마찰각 (degree)
        e_modulus: 탄성계수 (MPa)
        description: 비고 및 산정 근거
    """

    layer_name: str
    unit_weight: Optional[float] = None
    c: Optional[float] = None
    phi: Optional[float] = None
    e_modulus: Optional[float] = None
    description: Optional[str] = None
