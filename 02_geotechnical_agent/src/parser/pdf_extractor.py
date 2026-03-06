"""PDF 구조 분석 공통 모듈 - 테이블 및 이미지 추출 기반 기능 제공."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class PDFExtractor:
    """PDF 파일에서 텍스트, 테이블, 이미지를 추출하는 공통 유틸리티 클래스."""

    def __init__(self, pdf_path: str | Path) -> None:
        """초기화.

        Args:
            pdf_path: 파싱할 PDF 파일 경로
        """
        self.pdf_path = Path(pdf_path)

    def extract_text(self, page_range: tuple[int, int] | None = None) -> str:
        """PDF에서 텍스트를 추출한다.

        Args:
            page_range: 추출할 페이지 범위 (시작, 끝). None이면 전체 페이지.

        Returns:
            추출된 텍스트 문자열
        """
        pass

    def extract_tables(self, page: int | None = None) -> list[list[list[str]]]:
        """PDF에서 테이블 데이터를 추출한다.

        Args:
            page: 특정 페이지 번호. None이면 전체 페이지에서 추출.

        Returns:
            테이블 목록 (각 테이블은 행/열 리스트)
        """
        pass

    def extract_images(self, output_dir: str | Path) -> list[Path]:
        """PDF에서 이미지를 추출하여 저장한다.

        Args:
            output_dir: 이미지를 저장할 디렉토리 경로

        Returns:
            저장된 이미지 파일 경로 목록
        """
        pass

    def get_page_count(self) -> int:
        """PDF 총 페이지 수를 반환한다.

        Returns:
            PDF 페이지 수
        """
        pass

    def detect_table_regions(self, page: int) -> list[dict[str, Any]]:
        """특정 페이지에서 테이블 영역을 감지한다.

        Args:
            page: 분석할 페이지 번호

        Returns:
            테이블 영역 정보 목록 (bbox 좌표 포함)
        """
        pass
