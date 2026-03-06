# KTDB Report Agent

## 프로젝트 개요
KTDB(국가교통DB) 데이터 수집/가공 자동화 및 보고서 품질 표준화를 위한 AI Agent 시스템.
대화형 인터페이스(자연어 쿼리)로 교통 데이터 추출/가공 및 보고서용 성과품을 즉시 생성한다.

상위 프로젝트: `Transportation_AI` (교통부문 AI 개발)

## 핵심 기능
1. **xlsx/xls 파일 파싱**: KTDB 사이트에서 다운로드한 엑셀 파일 자동 파싱
2. **PostgreSQL DB 관리**: 파싱된 데이터를 DB에 적재/관리
3. **Text-to-SQL**: 자연어 쿼리 → SQL 변환 → DB 조회 (LangChain SQL Agent)
4. **통계 분석**: 증감 추이, 분담률, 이상치 탐지
5. **보고서 자동 생성**: HWP(pyhwpx)/Excel 표준 템플릿 기반 보고서 초안
6. **웹 플랫폼**: FastAPI 백엔드 + Streamlit 프론트엔드

## 대상 데이터
- 사회경제지표: 인구, 종사자 수, 세대수, GRDP (시군구 단위)
- 목적별 OD 매트릭스: 통근/통학/업무/쇼핑/귀가/기타
- 수단별 OD 매트릭스: 승용차/버스/철도/도보/자전거
- 화물 OD: 품목별/수단별 물동량

## 시스템 아키텍처
```
[xlsx/xls 파일] → [File Parser] → [PostgreSQL DB]
                                        |
                                        v
                          [FastAPI REST API (sync)]  ←→  [LLM Agent (Text-to-SQL)]
                                        |
                                        v
                              [Streamlit Web UI]
                                        |
                                   +---------+
                                   |         |
                                   v         v
                             [HWP 보고서] [Excel 통계]
```

## 모듈 구조
```
src/
├── collector/       # xlsx/xls 파일 파싱, 스키마 매핑, DB 적재
├── db/              # PostgreSQL 연결, SQLAlchemy ORM, Repository, Alembic
├── preprocessor/    # DB 기반 데이터 정제, 집계, OD 매트릭스 처리
├── analyzer/        # Text-to-SQL, SQL Agent, 통계 분석, 요약 생성
├── agent/           # LangChain AI Agent 오케스트레이션
├── reporter/        # HWP/Excel 보고서 생성, LLM 분석 문구
├── visualizer/      # plotly 차트, 보고서용 표
├── api/             # FastAPI REST API (sync 엔드포인트)
├── ui/              # Streamlit 웹 대시보드 (FastAPI 클라이언트)
└── utils/           # 로깅, 데코레이터
```

## 기술 스택
- **언어**: Python 3.11+
- **DB**: PostgreSQL 16 + SQLAlchemy 2.0 (Sync) + psycopg[binary] + Alembic
- **AI/LLM**: LangChain 0.3+, OpenAI API (Text-to-SQL)
- **백엔드**: FastAPI + uvicorn (동기 엔드포인트)
- **프론트엔드**: Streamlit (httpx로 FastAPI 연동)
- **데이터**: pandas, numpy, openpyxl, xlrd
- **시각화**: plotly, matplotlib
- **보고서**: pyhwpx (HWP, Windows), openpyxl/xlsxwriter (Excel)
- **설정**: pydantic-settings, python-dotenv, pyyaml
- **테스트**: pytest, pytest-cov
- **인프라**: Docker Compose (PostgreSQL)

## 아키텍처 결정사항
- **Sync SQLAlchemy**: 데이터 분석 도구 특성상 동기 방식 사용. asyncpg 미사용.
- **FastAPI sync endpoints**: `def` (not `async def`) 사용
- **pyhwpx**: Windows + HWP 설치 필수. 비Windows 환경은 python-docx 대안.
- **YAML 기반 매핑**: column_mapping.yaml로 KTDB 엑셀 컬럼 → DB 필드 유연 매핑

## 모듈 의존성 방향
```
collector → db → preprocessor → analyzer → visualizer/reporter
                                    ↑
                              agent (LangChain)
                                    ↓
                              api (FastAPI) → ui (Streamlit)
```

## 개발 규칙
- 타입 힌트 필수
- 데이터 파일은 `data/` 폴더 (gitignore 대상)
- 설정값은 `config/settings.py` 또는 `.env`로 관리 (하드코딩 금지)
- API 키/인증 정보는 `.env` 파일 (gitignore 대상)
- 테스트는 `tests/` 폴더에 pytest로 작성
- 모듈간 의존성은 단방향 유지 (순환 참조 금지)
- DB 스키마 변경 시 Alembic 마이그레이션 필수

## KPI 목표
- 데이터 수집/가공 시간: 8시간 → 30분 (90% 단축)
- 데이터 오기입 제로화
- 보고서 작성 속도 2배 향상
- 사내 톤앤매너 유지율 90% 이상
