"""Streamlit 대시보드 앱 엔트리포인트."""

from __future__ import annotations

import streamlit as st


def setup_page() -> None:
    st.set_page_config(
        page_title="KTDB 교통데이터 분석 대시보드",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_sidebar() -> dict[str, object]:
    """사이드바 렌더링 → 사용자 입력값 반환."""
    raise NotImplementedError


def render_overview_tab() -> None:
    """개요 탭: 주요 지표 KPI 카드 + 전국 단계구분도."""
    raise NotImplementedError


def render_od_analysis_tab() -> None:
    """OD 분석 탭: 매트릭스 히트맵 + 출발/도착 순위표."""
    raise NotImplementedError


def render_socioeconomic_tab() -> None:
    """사회경제지표 탭: 시계열 그래프 + 상관관계 분석."""
    raise NotImplementedError


def render_query_tab() -> None:
    """자연어 쿼리 탭: 채팅 인터페이스."""
    raise NotImplementedError


def render_report_tab() -> None:
    """보고서 생성 탭: HWP / Excel 다운로드."""
    raise NotImplementedError


def main() -> None:
    setup_page()

    filters = render_sidebar()

    tab_overview, tab_od, tab_socio, tab_query, tab_report = st.tabs(
        ["개요", "OD 분석", "사회경제지표", "자연어 쿼리", "보고서 생성"]
    )

    with tab_overview:
        render_overview_tab()
    with tab_od:
        render_od_analysis_tab()
    with tab_socio:
        render_socioeconomic_tab()
    with tab_query:
        render_query_tab()
    with tab_report:
        render_report_tab()


if __name__ == "__main__":
    main()
