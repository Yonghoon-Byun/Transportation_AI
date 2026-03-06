"""models 패키지 - 지반조사 데이터 스키마(dataclass) 정의 모듈."""

from .schemas import (
    BoreholeLog,
    LabTestResult,
    MechanicalTestResult,
    ConsolidationResult,
    DesignParameter,
)

__all__ = [
    "BoreholeLog",
    "LabTestResult",
    "MechanicalTestResult",
    "ConsolidationResult",
    "DesignParameter",
]
