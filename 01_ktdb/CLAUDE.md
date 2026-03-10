# KTDB Report Agent

## 프로젝트 개요
KTDB(국가교통DB) 데이터 수집/가공 자동화 및 보고서 품질 표준화를 위한 AI Agent 시스템.
대화형 인터페이스(자연어 쿼리)로 교통 데이터 추출/가공 및 보고서용 성과품을 즉시 생성한다.

상위 프로젝트: `Transportation_AI` (교통부문 AI 개발)

## 핵심 기능
1. **멀티포맷 파싱**: .OUT(CP949, 공백구분), .TXT(CP949), .xlsx 자동 감지 및 파싱
2. **PostgreSQL DB 관리**: COPY 프로토콜로 대용량 데이터 적재 (파티션 테이블)
3. **Text-to-SQL**: 자연어 쿼리 → SQL 변환 → DB 조회 (LangChain SQL Agent, Read-Only)
4. **통계 분석**: 증감 추이, 수단분담률, 이상치 탐지
5. **보고서 자동 생성**: HWP(pyhwpx)/Excel 표준 템플릿 기반 보고서 초안
6. **웹 플랫폼**: FastAPI 백엔드 + Streamlit 프론트엔드

## 데이터 포맷 (v3 실제 확인)

### 입력 파일
| 포맷 | 파일 패턴 | 인코딩 | 용도 |
|------|----------|--------|------|
| `.OUT` | `ODTRIP{YY}_F.OUT`, `ODMOD{YY}_*.OUT` | CP949, 공백구분 | 권역별 소존 OD (주력 데이터) |
| `.TXT` | `SUB_POP{YY}.TXT`, `WORK_POP{YY}.TXT`, etc. | CP949 | 사회경제지표 |
| `.xlsx` | `*목적OD*.xlsx`, `*화물*톤급*.xlsx` | UTF-8/EUC-KR | 전국 250존 OD, 화물OD |

### 존체계 (3-tier)
- **소존 (7자리)**: 권역별 OD 파일 기준 (예: 1101072 = 서울 종로구 청운효자동)
- **250존**: 전국 OD 및 화물 OD 기준 (정수 1~250)
- **17존 (시도)**: 집계/요약용

### 목적 카테고리 (실제 컬럼명)
- **출근, 등교, 업무, 귀가, 기타, 합계** (NOT 통근/통학/쇼핑)

## DB 연결 정보

### 연결 방식
- **Azure PostgreSQL** + **PgBouncer** (connection pooler)
- 포트: **6432** (PgBouncer), `sslmode=require`
- `prepare_threshold=None` 필수 (PgBouncer prepared statement 비호환)

### 스키마 구조
- `ktdb` 스키마 생성 불가 (CREATE SCHEMA 권한 없음)
- 모든 테이블: `public` 스키마에 `ktdb_` 접두사 사용
- 예: `public.ktdb_zones_17`, `public.ktdb_od_purpose_subzone`

### 테이블 목록 (25개 = 11 메인 + 14 파티션)
| 테이블 | 설명 |
|--------|------|
| `ktdb_zones_17` | 17존 마스터 (시도) |
| `ktdb_zones_250` | 250존 마스터 (전국) |
| `ktdb_zones_subzone` | 소존 마스터 (7자리, 권역별) |
| `ktdb_od_purpose_subzone` | 목적별 OD (소존, 파티션 테이블) |
| `ktdb_od_purpose_subzone_{2023~2050}` | 연도별 파티션 (7개) |
| `ktdb_od_purpose_250` | 목적별 OD (250존) |
| `ktdb_od_mode_subzone` | 수단별 OD (소존, 파티션 테이블) |
| `ktdb_od_mode_subzone_{2023~2050}` | 연도별 파티션 (7개) |
| `ktdb_od_freight` | 화물 OD (250존, 톤급별) |
| `ktdb_socioeconomic` | 사회경제지표 |
| `ktdb_upload_history` | 업로드 이력 |
| `ktdb_query_history` | LLM 쿼리 이력 |

## 시스템 아키텍처
```
[KTDB Zip 파일들]
      |
      v
[Zip Extractor] → [Format Router]
                       |
           +-----------+-----------+
           |           |           |
    [OUT Parser]  [TXT Parser]  [XLSX Parser]
    (CP949,공백)   (CP949)      (openpyxl)
           |           |           |
           +-----------+-----------+
                       |
                [Schema Mapper]
                       |
           [PostgreSQL COPY Loader]
                       |
              [PostgreSQL DB]
              (ktdb_* 테이블)
                       |
         +-------------+-------------+
         |                           |
  [Read-Write Session]      [Read-Only Session]
  (적재/관리용)             (LLM 쿼리 전용)
                                     |
                          [FastAPI REST API (sync)]
                                  |         |
                          [LLM Agent]  [통계 분석]
                       (Text-to-SQL)
                                  |
                          [Streamlit Web UI]
                                  |
                          [HWP/Excel 보고서]
```

## 모듈 구조
```
src/
├── collector/       # 멀티포맷 파싱 (zip_extractor, format_router, out_parser, txt_parser, xlsx_parser)
├── db/              # PostgreSQL 연결, SQLAlchemy ORM, Repository, Alembic
├── preprocessor/    # DB 기반 데이터 정제, 집계, 존체계간 롤업
├── analyzer/        # Text-to-SQL, SQL Agent (read-only), 통계 분석, SQL 검증
├── agent/           # LangChain AI Agent 오케스트레이션
├── reporter/        # HWP/Excel 보고서 생성, LLM 분석 문구
├── visualizer/      # plotly 차트, 보고서용 표
├── api/             # FastAPI REST API (sync 엔드포인트)
├── ui/              # Streamlit 웹 대시보드 (FastAPI 클라이언트)
└── utils/           # 로깅, 데코레이터
```

## 기술 스택
- **언어**: Python 3.11+
- **DB**: Azure PostgreSQL + PgBouncer + SQLAlchemy 2.0 (Sync) + psycopg[binary] + Alembic
- **AI/LLM**: LangChain 0.3+, OpenAI API (Text-to-SQL)
- **백엔드**: FastAPI + uvicorn (동기 엔드포인트)
- **프론트엔드**: Streamlit (httpx로 FastAPI 연동)
- **데이터**: pandas, numpy, openpyxl, chardet
- **시각화**: plotly, matplotlib
- **보고서**: pyhwpx (HWP, Windows), openpyxl/xlsxwriter (Excel)
- **설정**: pydantic-settings, python-dotenv, pyyaml
- **테스트**: pytest, pytest-cov
- **인프라**: Docker Compose (로컬 개발용 PostgreSQL)

## 아키텍처 결정사항
- **Sync SQLAlchemy**: 데이터 분석 도구 특성상 동기 방식. asyncpg 미사용.
- **FastAPI sync endpoints**: `def` (not `async def`) 사용
- **pyhwpx**: Windows + HWP 설치 필수. 비Windows 환경은 python-docx 대안.
- **COPY 프로토콜**: psycopg.copy 사용. ORM bulk insert 미사용 (대용량 필수)
- **Read-Only DB 세션**: LLM 생성 SQL은 read-only 연결로만 실행
- **PgBouncer 호환**: `prepare_threshold=None` 설정 필수

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
- 테이블명 항상 `ktdb_` 접두사 사용 (스키마 분리 불가 대체)

## KPI 목표
- 데이터 수집/가공 시간: 8시간 → 30분 (90% 단축)
- 파싱 성능: .OUT 1.7M행 < 30초, COPY 적재 < 2분
- OD 쿼리 성능: < 5초 (파티션 pruning)
- Text-to-SQL 정확도: 핵심 쿼리 90%+
- 보고서 작성 속도 2배 향상
- 사내 톤앤매너 유지율 90% 이상
