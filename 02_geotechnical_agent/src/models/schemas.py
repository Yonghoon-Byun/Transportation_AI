"""지반조사 데이터 모델 스키마.

PDF 기획서 기반 데이터 구조:
- Module 1 (주상도해석): SoilLayer, SPTRecord, BoreholeLog
- Module 2 (데이터통합): PhysicalProperties, MechanicalProperties, ConsolidationResult, LabTestResult
- 설계정수 산정: DesignParameter
- 이상치 탐지: AnomalyWarning
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Module 1: 주상도 해석 (Borehole Log Parser)
# ---------------------------------------------------------------------------

@dataclass
class SPTRecord:
    """표준관입시험(SPT) 원시 기록.

    Attributes:
        depth: 시험 심도 (m)
        n_value: N치 (0~50, 50은 관입불능)
        remarks: 비고 (예: "관입불능", "자갈층")
    """
    depth: float
    n_value: int
    remarks: Optional[str] = None


@dataclass
class SoilLayer:
    """지층 데이터 모델.

    Attributes:
        layer_no: 층 번호
        soil_name: 지층명 (예: "매립토", "퇴적토", "풍화토", "풍화암", "연암")
        depth_from: 상단 심도 (m)
        depth_to: 하단 심도 (m)
        thickness: 층 두께 (m)
        spt_n_values: 해당 층 N치 목록
        n_avg: 평균 N치
        is_rock: 암반층 여부 (풍화암 이하)
        rqd: Rock Quality Designation (%, 암반층만)
        tcr: Total Core Recovery (%, 암반층만)
        color: 색상 기술
        description: 상태 기술
    """
    layer_no: int
    soil_name: str
    depth_from: float
    depth_to: float
    thickness: float
    spt_n_values: list[int] = field(default_factory=list)
    n_avg: Optional[float] = None
    is_rock: bool = False
    rqd: Optional[float] = None
    tcr: Optional[float] = None
    color: Optional[str] = None
    description: Optional[str] = None


@dataclass
class BoreholeLog:
    """시추주상도 데이터 모델 (시추공 1개 = 다층 구조).

    Attributes:
        hole_no: 시추공 번호 (예: "BH-1")
        location_x: X 좌표
        location_y: Y 좌표
        ground_elevation: 지표 표고 (m)
        gwl: 지하수위 (m, 지표 기준)
        total_depth: 시추 총 심도 (m)
        layers: 지층 목록
        spt_records: 심도별 N치 원시 레코드
    """
    hole_no: str
    total_depth: float
    layers: list[SoilLayer] = field(default_factory=list)
    spt_records: list[SPTRecord] = field(default_factory=list)
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    ground_elevation: Optional[float] = None
    gwl: Optional[float] = None


# ---------------------------------------------------------------------------
# Module 2: 데이터 통합 (Data Matcher)
# ---------------------------------------------------------------------------

@dataclass
class PhysicalProperties:
    """물리시험 성과 데이터 (Index Properties).

    Attributes:
        hole_no: 시추공 번호
        depth_from: 시료 상단 심도 (m)
        depth_to: 시료 하단 심도 (m)
        sample_no: 시료 번호
        wn: 자연함수비 (%)
        gs: 비중
        ll: 액성한계 (%)
        pl: 소성한계 (%)
        pi: 소성지수 (%)
        gravel_pct: 자갈 함유율 (%)
        sand_pct: 모래 함유율 (%)
        silt_pct: 실트 함유율 (%)
        clay_pct: 점토 함유율 (%)
        uscs_symbol: USCS 분류 기호 (예: "SM", "CL")
        uscs_name: USCS 분류명
    """
    hole_no: str
    depth_from: float
    depth_to: float
    sample_no: Optional[str] = None
    wn: Optional[float] = None
    gs: Optional[float] = None
    ll: Optional[float] = None
    pl: Optional[float] = None
    pi: Optional[float] = None
    gravel_pct: Optional[float] = None
    sand_pct: Optional[float] = None
    silt_pct: Optional[float] = None
    clay_pct: Optional[float] = None
    uscs_symbol: Optional[str] = None
    uscs_name: Optional[str] = None


@dataclass
class MechanicalProperties:
    """역학시험 성과 데이터 (전단강도, 일축압축 등).

    Attributes:
        hole_no: 시추공 번호
        depth_from: 시료 상단 심도 (m)
        depth_to: 시료 하단 심도 (m)
        sample_no: 시료 번호
        test_type: 시험 종류 ("unconfined", "direct_shear", "triaxial")
        qu: 일축압축강도 (kPa)
        cohesion: 점착력 c (kPa)
        friction_angle: 내부마찰각 phi (도)
    """
    hole_no: str
    depth_from: float
    depth_to: float
    sample_no: Optional[str] = None
    test_type: Optional[str] = None
    qu: Optional[float] = None
    cohesion: Optional[float] = None
    friction_angle: Optional[float] = None


@dataclass
class ConsolidationResult:
    """압밀시험 성과 데이터 (연약지반).

    Attributes:
        hole_no: 시추공 번호
        depth_from: 시료 상단 심도 (m)
        depth_to: 시료 하단 심도 (m)
        sample_no: 시료 번호
        cc: 압축지수 Cc
        cr: 재압축지수(팽창지수) Cr
        pc: 선행압밀하중 (kPa)
        cv: 압밀계수 Cv (cm2/sec)
        e0: 초기 간극비 e0
    """
    hole_no: str
    depth_from: float
    depth_to: float
    sample_no: Optional[str] = None
    cc: Optional[float] = None
    cr: Optional[float] = None
    pc: Optional[float] = None
    cv: Optional[float] = None
    e0: Optional[float] = None


@dataclass
class LabTestResult:
    """실내시험 결과 통합 모델 (시추공 단위).

    Attributes:
        hole_no: 시추공 번호
        physical: 물리시험 결과 목록
        mechanical: 역학시험 결과 목록
        consolidation: 압밀시험 결과 목록
    """
    hole_no: str
    physical: list[PhysicalProperties] = field(default_factory=list)
    mechanical: list[MechanicalProperties] = field(default_factory=list)
    consolidation: list[ConsolidationResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 설계지반정수 산정
# ---------------------------------------------------------------------------

class DesignField(str, Enum):
    """설계 적용 분야."""
    SLOPE_SOIL = "slope_soil"           # 비탈면(토사)
    SLOPE_ROCK = "slope_rock"           # 비탈면(암반)
    FOUNDATION = "foundation"           # 기초(말뚝/얕은기초)
    RETAINING = "retaining"             # 흙막이(가시설)
    TUNNEL = "tunnel"                   # 터널
    SOFT_GROUND = "soft_ground"         # 연약지반


@dataclass
class DesignParameter:
    """설계지반정수 데이터 모델.

    Attributes:
        design_field: 설계 적용 분야
        layer_name: 지층명
        gamma_t: 습윤단위중량 (kN/m3)
        gamma_sat: 포화단위중량 (kN/m3)
        cohesion: 점착력 c (kPa)
        friction_angle: 내부마찰각 phi (도)
        elastic_modulus: 탄성계수 E (MPa)
        poisson_ratio: 포아송비
        n_avg: 평균 N치
        qu: 일축압축강도 (kPa)
        rqd: RQD (%)
        rmr: RMR (암반분류)
        smr: SMR (비탈면 암반)
        gwl: 지하수위 (m)
        cc: 압축지수
        cr: 재압축지수
        pc: 선행압밀하중 (kPa)
        cv: 압밀계수 (cm2/sec)
        e0: 초기 간극비
        kh: 수평지반반력계수 (kN/m3)
        source: 산정 근거 유형 ("measured", "empirical", "estimated")
        basis: 산정 근거 설명 (기준서, 경험식명)
    """
    design_field: str
    layer_name: str
    gamma_t: Optional[float] = None
    gamma_sat: Optional[float] = None
    cohesion: Optional[float] = None
    friction_angle: Optional[float] = None
    elastic_modulus: Optional[float] = None
    poisson_ratio: Optional[float] = None
    n_avg: Optional[float] = None
    qu: Optional[float] = None
    rqd: Optional[float] = None
    rmr: Optional[float] = None
    smr: Optional[float] = None
    gwl: Optional[float] = None
    cc: Optional[float] = None
    cr: Optional[float] = None
    pc: Optional[float] = None
    cv: Optional[float] = None
    e0: Optional[float] = None
    kh: Optional[float] = None
    source: Optional[str] = None
    basis: Optional[str] = None


# ---------------------------------------------------------------------------
# 이상치 탐지
# ---------------------------------------------------------------------------

class AnomalyLevel(str, Enum):
    """이상치 경고 레벨."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AnomalyWarning:
    """이상치 탐지 결과 모델.

    Attributes:
        hole_no: 시추공 번호
        depth: 해당 심도 (m)
        parameter: 이상치가 발견된 파라미터명
        value: 실측값
        expected_range: 공학적 기대 범위 (min, max)
        level: 경고 레벨
        message: 경고 메시지
    """
    hole_no: str
    depth: float
    parameter: str
    value: float
    expected_range: tuple[float, float]
    level: str
    message: str
