"""실내시험 성과표 파싱 모듈 - PDF/Excel 형식의 시험결과 데이터 추출.

PDF 기획서 기반:
- 물성시험총괄표(Summary Table) 우선 인식
- 물리시험(함수비, 비중, LL/PI, 입도분포), 역학시험(qu, c, φ), 압밀시험(Cc, Cr, Pc, Cv, e₀)
- 업체별 양식 차이 대응 (컬럼명 정규화)
"""

from __future__ import annotations

from pathlib import Path

from ..models.schemas import (
    ConsolidationResult,
    LabTestResult,
    MechanicalProperties,
    PhysicalProperties,
)
from .pdf_extractor import PDFExtractor


class LabTestParser:
    """실내시험 성과표(물성, 역학, 압밀 시험)를 파싱하는 클래스."""

    def __init__(self) -> None:
        """초기화."""
        pass

    def parse_physical_properties(
        self, file_path: str | Path
    ) -> list[PhysicalProperties]:
        """물성시험 성과표를 파싱하여 PhysicalProperties 목록을 반환한다.

        Args:
            file_path: 물성시험 성과표 파일 경로 (PDF 또는 Excel)

        Returns:
            파싱된 PhysicalProperties 목록
        """
        pass

    def parse_mechanical_tests(
        self, file_path: str | Path
    ) -> list[MechanicalProperties]:
        """역학시험 성과표(일축압축, 삼축압축, 직접전단 등)를 파싱한다.

        Args:
            file_path: 역학시험 성과표 파일 경로

        Returns:
            파싱된 MechanicalProperties 목록
        """
        pass

    def parse_consolidation_tests(
        self, file_path: str | Path
    ) -> list[ConsolidationResult]:
        """압밀시험 성과표를 파싱한다.

        Args:
            file_path: 압밀시험 성과표 파일 경로

        Returns:
            파싱된 ConsolidationResult 목록
        """
        pass

    def parse_summary_table(
        self, file_path: str | Path
    ) -> LabTestResult:
        """물성시험 총괄표(Summary Table)를 우선 인식하여 파싱한다.

        기획서 요구사항: 보고서 내에 물성시험총괄표와 같은 요약테이블을
        우선적으로 인식해야 함.

        Args:
            file_path: 보고서 파일 경로

        Returns:
            통합된 LabTestResult 객체
        """
        pass

    def _parse_from_excel(self, file_path: Path) -> list[list[str]]:
        """Excel 파일에서 데이터를 추출한다.

        Args:
            file_path: Excel 파일 경로

        Returns:
            행/열 데이터 목록
        """
        pass

    def _parse_from_pdf(self, file_path: Path) -> list[list[str]]:
        """PDF 파일에서 테이블 데이터를 추출한다.

        Args:
            file_path: PDF 파일 경로

        Returns:
            행/열 데이터 목록
        """
        pass

    def _normalize_header(self, header_row: list[str]) -> dict[str, int]:
        """헤더 행을 파싱하여 컬럼명-인덱스 매핑을 반환한다.

        업체별 양식 차이 대응을 위해 column_aliases.yaml 매핑 적용.

        Args:
            header_row: 헤더 행 데이터

        Returns:
            컬럼명을 키, 인덱스를 값으로 하는 딕셔너리
        """
        pass
