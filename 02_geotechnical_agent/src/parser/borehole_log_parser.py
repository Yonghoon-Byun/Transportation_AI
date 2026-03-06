"""시추주상도 PDF 파싱 모듈 - OCR 기반 주상도 데이터 추출."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models.schemas import BoreholeLog
from .pdf_extractor import PDFExtractor


class BoreholeLogParser:
    """시추주상도 PDF에서 지층 정보 및 SPT N값을 파싱하는 클래스."""

    def __init__(self, use_ocr: bool = True) -> None:
        """초기화.

        Args:
            use_ocr: OCR 사용 여부 (스캔 PDF의 경우 True)
        """
        self.use_ocr = use_ocr

    def parse(self, pdf_path: str | Path) -> list[BoreholeLog]:
        """주상도 PDF를 파싱하여 BoreholeLog 목록을 반환한다.

        Args:
            pdf_path: 주상도 PDF 파일 경로

        Returns:
            파싱된 BoreholeLog 데이터 목록
        """
        pass

    def parse_multiple(self, pdf_paths: list[str | Path]) -> list[BoreholeLog]:
        """여러 주상도 PDF를 일괄 파싱한다.

        Args:
            pdf_paths: 주상도 PDF 파일 경로 목록

        Returns:
            파싱된 BoreholeLog 데이터 전체 목록
        """
        pass

    def _extract_hole_no(self, text: str) -> str:
        """텍스트에서 시추공 번호를 추출한다.

        Args:
            text: 페이지 텍스트

        Returns:
            시추공 번호 문자열
        """
        pass

    def _extract_layer_data(self, table: list[list[str]]) -> list[dict[str, Any]]:
        """테이블에서 지층 데이터를 추출한다.

        Args:
            table: 파싱된 테이블 데이터

        Returns:
            지층 데이터 딕셔너리 목록
        """
        pass

    def _extract_gwl(self, text: str) -> float | None:
        """텍스트에서 지하수위를 추출한다.

        Args:
            text: 페이지 텍스트

        Returns:
            지하수위 (m), 없으면 None
        """
        pass

    def _apply_ocr(self, pdf_path: Path) -> str:
        """스캔 PDF에 OCR을 적용하여 텍스트를 추출한다.

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            OCR 추출 텍스트
        """
        pass
