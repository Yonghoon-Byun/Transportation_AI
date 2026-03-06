# KTDB Report Agent - 개발 계획

## 1. 프로젝트 개요

### 목표
교통수요예측 기초자료 분석을 위한 KTDB 데이터 수집·가공·분석·보고서 생성 시스템 구축.
LLM 기반 자연어 쿼리로 전체 프로세스를 자동화하여 **30분 이내** 완료.

### AS-IS vs TO-BE

| 항목 | AS-IS (기존) | TO-BE (목표) |
|------|-------------|-------------|
| 데이터 수집 | KTDB API 직접 연동 (httpx) | xlsx/xls 파일 다운로드 후 파싱 |
| 데이터 저장 | 파일 기반 (pandas DataFrame) | PostgreSQL DB |
| 분석 방식 | 수동 코딩 + DataFrame 쿼리 | Text-to-SQL (LangChain SQL Agent) |
| 백엔드 | 없음 (Streamlit 단독) | FastAPI REST API (동기 엔드포인트) |
| UI | Streamlit 단독 실행 | Streamlit + FastAPI 연동 |
| 보고서 | 수작업 (약 8시간) | HWP/Excel 자동 생성 (30분 이내) |

### 핵심 아키텍처 결정사항
- **Sync SQLAlchemy** 사용 (데이터 분석 도구 특성, async 미사용)
- **psycopg[binary]** (psycopg3 동기 드라이버, asyncpg 미사용)
- **FastAPI 동기 엔드포인트** (`def`, not `async def`)
- **pyhwpx** (Windows + HWP 설치 환경 한정)
- **query_engine.py 삭제** → text_to_sql.py로 대체

---

## 2. 시스템 아키텍처

```
[KTDB 웹사이트]
      |
      v (xlsx/xls 다운로드)
[File Parser] ──────────────────> [PostgreSQL DB]
(openpyxl, xlrd)                       |
                                        v
                           [FastAPI REST API (sync def)]
                                  |              |
                          [LLM Agent]      [통계 분석]
                       (Text-to-SQL)      (statistics.py)
                                  |
                                  v
                          [Streamlit Web UI]
                                  |
                        +---------+---------+
                        |                   |
                        v                   v
                  [HWP 보고서]         [Excel 통계]
                   (pyhwpx)           (openpyxl)
```

### 데이터 흐름 요약
1. 사용자가 KTDB 웹사이트에서 xlsx/xls 파일 다운로드
2. Streamlit UI에서 파일 업로드 → FastAPI /api/upload 호출
3. File Parser → PostgreSQL 적재 (upload_history 기록)
4. 사용자가 자연어 쿼리 입력 → Text-to-SQL → DB 조회
5. 분석 결과 + LLM 문구 생성 → 보고서(HWP/Excel) 다운로드

---

## 3. 폴더 구조

```
01_ktdb/
├── src/
│   ├── collector/          # xlsx/xls 파일 파싱 및 DB 적재
│   │   ├── file_parser.py  # xlsx/xls 파싱 엔진 (신규)
│   │   ├── schema_mapper.py # 컬럼 -> DB 스키마 매핑 (신규)
│   │   ├── loader.py       # DB bulk insert (신규)
│   │   └── models.py       # Pydantic 파싱 DTO (재작성)
│   ├── db/                 # 데이터베이스 모듈 (전체 신규)
│   │   ├── connection.py   # Sync SQLAlchemy engine/session
│   │   ├── models.py       # ORM 모델 (7개 테이블)
│   │   ├── repository.py   # CRUD 레포지토리
│   │   ├── seed.py         # zone_config.yaml 기반 시드
│   │   └── migrations/     # Alembic 마이그레이션
│   ├── preprocessor/       # DB 기반 전처리 (재작성)
│   │   ├── pipeline.py     # DB read -> clean -> write
│   │   ├── cleaner.py      # 결측치/이상치 정제
│   │   ├── aggregator.py   # SQL 기반 집계
│   │   └── od_matrix.py    # OD 매트릭스 피벗/언피벗
│   ├── analyzer/           # Text-to-SQL 분석 (재작성)
│   │   ├── text_to_sql.py  # LangChain SQL 변환기
│   │   ├── sql_agent.py    # LangChain SQL Agent
│   │   ├── statistics.py   # 통계 분석 함수
│   │   └── summary.py      # LLM 분석 결과 요약
│   ├── visualizer/         # 시각화 (재작성)
│   │   ├── charts.py       # plotly 차트 (bar/line/heatmap/choropleth)
│   │   └── tables.py       # 보고서용 표 스타일링
│   ├── reporter/           # 보고서 생성 (재작성)
│   │   ├── hwp_generator.py   # pyhwpx HWP 생성
│   │   ├── excel_generator.py # openpyxl Excel 생성
│   │   └── text_generator.py  # LLM 분석 문구 생성
│   ├── api/                # FastAPI 백엔드 (신규)
│   │   ├── main.py         # FastAPI 앱 엔트리포인트
│   │   ├── deps.py         # 의존성 주입 (sync DB 세션)
│   │   ├── schemas.py      # Pydantic 요청/응답 스키마
│   │   └── routes/
│   │       ├── upload.py   # POST /api/upload
│   │       ├── data.py     # GET /api/data/{category}
│   │       ├── analysis.py # POST /api/analysis/statistics
│   │       ├── query.py    # POST /api/query (자연어)
│   │       └── report.py   # POST /api/report/generate
│   ├── agent/              # LLM 에이전트 (재작성)
│   │   ├── llm_agent.py    # 전체 플로우 오케스트레이션
│   │   ├── prompt_templates.py  # 교통 도메인 프롬프트
│   │   └── tools.py        # DB 쿼리/분석/보고서 도구
│   ├── ui/                 # Streamlit 웹 UI (재작성)
│   │   ├── app.py          # FastAPI 연동 메인 앱
│   │   ├── components/     # chat.py, data_viewer.py, upload.py
│   │   └── pages/          # dashboard.py, query.py, report.py, upload.py
│   └── utils/
│       ├── logger.py
│       └── decorators.py
├── config/                 # 설정 (신규)
│   ├── settings.py         # pydantic-settings 기반
│   ├── .env.example
│   ├── zone_config.yaml    # KTDB 존-행정구역 매핑 마스터
│   └── column_mapping.yaml # KTDB 컬럼명 -> DB 필드 매핑
├── alembic/                # DB 마이그레이션 (신규)
│   ├── alembic.ini
│   └── versions/
├── data/
│   ├── uploads/            # xlsx/xls 업로드 임시 저장
│   ├── outputs/            # 생성된 보고서
│   ├── samples/            # KTDB 샘플 파일 (Phase 0)
│   └── geo/                # 시군구 GeoJSON (통계청 SGIS)
├── tests/
│   ├── conftest.py         # pytest fixtures (sync DB 세션)
│   ├── fixtures/           # 테스트용 샘플 xlsx
│   ├── test_db.py
│   ├── test_collector.py
│   ├── test_preprocessor.py
│   ├── test_analyzer.py
│   ├── test_agent.py
│   ├── test_visualizer.py
│   ├── test_api.py
│   └── test_e2e.py
├── notebooks/
│   ├── 00_ktdb_file_format_eda.ipynb  # KTDB 파일 포맷 분석 (신규)
│   ├── 01_eda.ipynb
│   ├── 02_file_parsing_test.ipynb
│   └── 03_text_to_sql_test.ipynb
├── requirements.txt
├── pytest.ini
├── docker-compose.yml      # PostgreSQL 컨테이너 (신규)
├── CLAUDE.md
├── PLAN.md
└── README.md
```

> 상세 스펙(zone_config.yaml, column_mapping.yaml, KTDB 파일 포맷)은
> `.omc/plans/ktdb-architecture-revision.md` 참조.

---

## 4. PostgreSQL 스키마 설계 (7개 테이블)

```sql
-- 1. 존(zone) 마스터
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    zone_code VARCHAR(10) UNIQUE NOT NULL,
    zone_name VARCHAR(100) NOT NULL,
    region_code VARCHAR(10) NOT NULL,
    region_name VARCHAR(100) NOT NULL,
    sido_code VARCHAR(5),
    sido_name VARCHAR(50),
    sigungu_code VARCHAR(5),
    sigungu_name VARCHAR(50),
    centroid_lat DOUBLE PRECISION,
    centroid_lon DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. 사회경제지표
CREATE TABLE socioeconomic_indicators (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    region_code VARCHAR(10) NOT NULL REFERENCES zones(zone_code),
    population INTEGER,
    households INTEGER,
    employment INTEGER,
    students INTEGER,
    vehicle_count INTEGER,
    grdp DOUBLE PRECISION,
    area_km2 DOUBLE PRECISION,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, region_code)
);

-- 3. 목적별 OD 매트릭스
CREATE TABLE od_purpose (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    origin_zone VARCHAR(10) NOT NULL,
    destination_zone VARCHAR(10) NOT NULL,
    trip_purpose VARCHAR(20) NOT NULL,  -- 통근/통학/업무/쇼핑/귀가/기타
    volume DOUBLE PRECISION NOT NULL,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_od_purpose_year ON od_purpose(year);
CREATE INDEX idx_od_purpose_origin ON od_purpose(origin_zone);
CREATE INDEX idx_od_purpose_dest ON od_purpose(destination_zone);
CREATE INDEX idx_od_purpose_purpose ON od_purpose(trip_purpose);

-- 4. 수단별 OD 매트릭스
CREATE TABLE od_mode (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    origin_zone VARCHAR(10) NOT NULL,
    destination_zone VARCHAR(10) NOT NULL,
    transport_mode VARCHAR(20) NOT NULL,  -- 승용차/버스/철도/도보/자전거/기타
    volume DOUBLE PRECISION NOT NULL,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_od_mode_year ON od_mode(year);
CREATE INDEX idx_od_mode_origin ON od_mode(origin_zone);
CREATE INDEX idx_od_mode_dest ON od_mode(destination_zone);
CREATE INDEX idx_od_mode_mode ON od_mode(transport_mode);

-- 5. 화물 OD
CREATE TABLE od_freight (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    origin_zone VARCHAR(10) NOT NULL,
    destination_zone VARCHAR(10) NOT NULL,
    commodity_type VARCHAR(50),
    transport_mode VARCHAR(20),
    volume_ton DOUBLE PRECISION NOT NULL,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_od_freight_year ON od_freight(year);

-- 6. 업로드 이력
CREATE TABLE upload_history (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL,       -- xlsx / xls
    data_category VARCHAR(50) NOT NULL,   -- socioeconomic / od_purpose / od_mode / od_freight
    year INTEGER,
    row_count INTEGER,
    status VARCHAR(20) DEFAULT 'pending', -- pending / processing / completed / failed
    error_message TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 7. 쿼리 이력 (LLM 로그)
CREATE TABLE query_history (
    id SERIAL PRIMARY KEY,
    user_query TEXT NOT NULL,
    generated_sql TEXT,
    result_summary TEXT,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. 개발 단계 (Phase 0~5)

### Phase 0: 데이터 획득 및 포맷 분석 (0.5주)
**Goal**: KTDB 샘플 xlsx 파일 확보 및 실제 파일 포맷 분석

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 0.1 KTDB 샘플 확보 | `data/samples/` | ktdb.go.kr에서 4개 카테고리 xlsx 다운로드 | 카테고리별 1건 이상 확보 |
| 0.2 파일 포맷 EDA | `notebooks/00_ktdb_file_format_eda.ipynb` | 헤더 위치, 컬럼명, OD 매트릭스 구조 분석 | 카테고리별 레이아웃 문서화 |
| 0.3 컬럼 매핑 초안 | `config/column_mapping.yaml` | EDA 결과 기반 실제 컬럼명 매핑 작성 | 실제 파일 컬럼명 포함 |

**Phase 0 완료 조건**: 4개 카테고리 샘플 파일 + column_mapping.yaml 초안

---

### Phase 1: 기초 인프라 & DB 구축 (1주)
**Goal**: PostgreSQL 환경 + ORM 모델 + 설정 인프라

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 1.1 config/ 신규 생성 | `config/settings.py`, `.env.example`, `zone_config.yaml`, `column_mapping.yaml` | pydantic-settings 설정 클래스, 환경변수 예시, 존 매핑 마스터 | `from config.settings import settings` 정상 |
| 1.2 Docker Compose | `docker-compose.yml` | PostgreSQL 16 컨테이너 정의, 볼륨 마운트 | `docker-compose up -d` 성공 |
| 1.3 DB 모듈 구현 | `src/db/connection.py`, `models.py`, `repository.py`, `seed.py` | Sync SQLAlchemy engine, ORM 7개 테이블, CRUD 레포지토리, zone 시드 | ORM CRUD 동작 확인 |
| 1.4 Alembic 설정 | `alembic/`, `alembic.ini` | 마이그레이션 초기화, 초기 스크립트 생성 | `alembic upgrade head` 전체 스키마 생성 |
| 1.5 기존 파일 정리 | `src/collector/api_client.py` (삭제), `src/analyzer/query_engine.py` (삭제) | KTDB API 커넥터 폐기, query_engine.py 삭제 | 삭제 파일 없음 확인 |
| 1.6 테스트 인프라 | `tests/conftest.py`, `tests/test_db.py`, `pytest.ini` | SQLite in-memory 테스트 세션, ORM CRUD 단위 테스트 | `pytest tests/test_db.py` 통과 |

**Phase 1 완료 조건**: PostgreSQL 전체 스키마 생성, zone 시드 적재, test_db.py 통과

---

### Phase 2: 데이터 수집 & 적재 파이프라인 (1주)
**Goal**: xlsx/xls 파싱 + PostgreSQL bulk insert

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 2.1 파일 파서 | `src/collector/file_parser.py` | XlsxParser/XlsParser, 메타 행 자동 감지, OD 피벗->롱 포맷 변환, Phase 0 EDA 반영 | 샘플 파일 파싱 성공 |
| 2.2 스키마 매퍼 | `src/collector/schema_mapper.py` | column_mapping.yaml 기반 컬럼 정규화, 지역코드 변환 | 다양한 컬럼명 정규화 |
| 2.3 DB 적재기 | `src/collector/loader.py` | DataLoader, bulk insert, upsert (year+region_code), 배치 처리 | 100만 행 OD 5분 이내 적재 |
| 2.4 업로드 API | `src/api/main.py`, `routes/upload.py`, `schemas.py`, `deps.py` | FastAPI 앱 셋업, POST /api/upload (동기 `def`), GET /api/upload/history | Swagger UI에서 업로드 정상 |
| 2.5 파서 테스트 | `tests/test_collector.py`, `tests/fixtures/` | 파서/매퍼/적재기 단위 테스트, 에지케이스 (빈 파일, 인코딩) | `pytest tests/test_collector.py` 통과 |

**Phase 2 완료 조건**: 실제 KTDB xlsx 파일 업로드 → DB 적재 → API로 이력 조회 정상

---

### Phase 3: LLM 에이전트 & Text-to-SQL (2주)
**Goal**: 자연어 쿼리로 DB 데이터 추출/분석

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 3.1 전처리 DB 기반 구현 | `src/preprocessor/pipeline.py`, `cleaner.py`, `aggregator.py`, `od_matrix.py` | DB 기반 정제/집계/OD 처리 (기존 stub 완전 재작성) | DB 기반 파이프라인 정상 동작 |
| 3.2 Text-to-SQL 엔진 | `src/analyzer/text_to_sql.py` | LangChain SQLDatabaseChain, Sync engine 전달, SELECT 전용 검증, SQL 인젝션 방지 | "2023년 서울 인구" → 정확한 SQL 생성 |
| 3.3 SQL Agent | `src/analyzer/sql_agent.py` | LangChain SQL Agent (GPT-4o-mini), 쿼리 이력 저장, 에러 핸들링 | 복합 쿼리 처리 (시계열 비교 등) |
| 3.4 통계 분석 | `src/analyzer/statistics.py` | describe, growth_rate, rank, 이상치 탐지 (IQR/z-score) | 통계 함수 단위 테스트 통과 |
| 3.5 분석 요약 | `src/analyzer/summary.py`, `src/reporter/text_generator.py` | LLM 기반 사내 톤앤매너 문구 생성 | 분석 결과 문구 생성 정상 |
| 3.6 LLM 에이전트 | `src/agent/llm_agent.py`, `prompt_templates.py`, `tools.py` | SQL Agent + 분석 + 보고서 오케스트레이션, 교통 도메인 프롬프트 | 자연어 → SQL → 분석 → 문구 전체 플로우 |
| 3.7 분석/쿼리 API | `src/api/routes/data.py`, `analysis.py`, `query.py` | GET /api/data/{category}, POST /api/analysis/statistics, POST /api/query (모두 `def` 동기) | API로 자연어 쿼리 실행 정상 |
| 3.8 분석 테스트 | `tests/test_analyzer.py`, `tests/test_agent.py` | Text-to-SQL 단위 테스트, SQL Agent 통합 테스트 (mock LLM), API 엔드포인트 테스트 | `pytest tests/test_analyzer.py tests/test_agent.py` 통과 |

**Phase 3 완료 조건**: 자연어 쿼리 → SQL → DB 조회 → 분석 결과 + 문구 반환 전체 플로우 동작

---

### Phase 4: 시각화 & 보고서 & 웹 UI (1.5주)
**Goal**: 대화형 대시보드 + 자동 보고서 생성

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 4.1 차트 빌더 | `src/visualizer/charts.py`, `tables.py` | bar/line/heatmap/scatter/choropleth, GeoJSON 연동 (통계청 SGIS, `data/geo/`) | 차트 생성 및 파일 저장 정상 |
| 4.2 HWP 생성기 | `src/reporter/hwp_generator.py` | pyhwpx 기반 HWP 생성, 표/차트 이미지 삽입. 비Windows 환경 시 python-docx 대체 | HWP 파일 정상 생성 |
| 4.3 Excel 생성기 | `src/reporter/excel_generator.py` | 다중 시트, 셀 스타일링, 차트 삽입, 바이트 스트림 반환 | 스타일 적용된 Excel 다운로드 정상 |
| 4.4 보고서 API | `src/api/routes/report.py` | POST /api/report/generate (HWP/Excel 선택), GET /api/report/download/{id} (모두 `def` 동기) | API 보고서 생성 → 다운로드 정상 |
| 4.5 Streamlit UI | `src/ui/app.py`, `components/`, `pages/` | FastAPI httpx 클라이언트 연동, 업로드/쿼리/대시보드/보고서 4개 페이지 | 전체 워크플로우 웹 UI 실행 가능 |
| 4.6 시각화 테스트 | `tests/test_visualizer.py`, `tests/test_api.py` | 차트/보고서 생성 단위 테스트, 보고서 API 통합 테스트 | `pytest tests/test_visualizer.py tests/test_api.py` 통과 |

**Phase 4 완료 조건**: 웹 대시보드에서 파일 업로드 → 자연어 쿼리 → 분석 → 보고서 다운로드 전체 동작

---

### Phase 5: 통합 테스트 & 최적화 (0.5주)
**Goal**: E2E 검증, 성능 최적화, 문서화

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 5.1 E2E 통합 테스트 | `tests/test_e2e.py` | 전체 워크플로우 E2E (파일 업로드→DB→쿼리→분석→보고서), 30분 이내 성능 측정 | E2E 통과, 전체 30분 이내 |
| 5.2 성능 최적화 | - | EXPLAIN ANALYZE, 인덱스 튜닝, LLM 응답 캐싱 | OD 100만 행 < 5분, 쿼리 응답 < 10초 |
| 5.3 문서화 | `README.md`, `CLAUDE.md` | 설치/실행 방법, FastAPI Swagger 연동 | 신규 사용자 환경 설정 가능 |

**Phase 5 완료 조건**: pytest 전체 통과 (커버리지 80%+), 전체 30분 이내 처리

---

## 6. 기술 스택 비교표

| 영역 | Before | After |
|------|--------|-------|
| 데이터 수집 | httpx (KTDB API) | openpyxl, xlrd (xlsx/xls 파싱) |
| 데이터 저장 | 파일 기반 (pandas) | PostgreSQL + Sync SQLAlchemy |
| DB 드라이버 | N/A | psycopg[binary] (psycopg3, 동기) |
| DB 마이그레이션 | N/A | Alembic |
| LLM 연동 | LangChain (DataFrame) | LangChain SQL Agent (Text-to-SQL) |
| 백엔드 API | N/A | FastAPI + uvicorn (동기 엔드포인트) |
| UI | Streamlit 단독 | Streamlit (FastAPI 클라이언트) |
| HWP 생성 | python-pptx (우회) | pyhwpx (native HWP, Windows 전용) |
| 컨테이너화 | N/A | Docker Compose (PostgreSQL) |
| GeoJSON | N/A | 통계청 SGIS / 국토정보플랫폼 |

---

## 7. requirements.txt

```
# Data Processing
pandas>=2.2
numpy>=1.26

# File Parsing
openpyxl>=3.1
xlrd>=2.0

# Database (Sync)
sqlalchemy>=2.0
psycopg[binary]>=3.1
alembic>=1.13

# AI/LLM
langchain>=0.3.0
langchain-community>=0.3.0
langchain-openai>=0.2.0
openai>=1.50

# Web Backend
fastapi>=0.115
uvicorn[standard]>=0.30
python-multipart>=0.0.9

# UI
streamlit>=1.40

# Visualization
plotly>=5.17
matplotlib>=3.8

# Excel Output
xlsxwriter>=3.2

# HWP Generation (Windows + HWP 설치 필요)
pyhwpx>=0.5

# HTTP Client (Streamlit -> FastAPI)
httpx>=0.27

# Configuration
pydantic>=2.5
pydantic-settings>=2.1
python-dotenv>=1.0
pyyaml>=6.0

# Testing
pytest>=8.0
pytest-cov>=5.0

# Logging
loguru>=0.7.2
```

**주요 변경 사항**: pytest-asyncio 제거 (sync 방식), asyncpg 미포함, pyyaml 추가

---

## 8. 위험 요소 및 완화 전략

| 위험 | 영향도 | 발생 가능성 | 완화 전략 |
|------|--------|------------|----------|
| KTDB xlsx 파일 형식 불일치 | 높음 | 높음 | Phase 0에서 실제 샘플 EDA 후 구현. column_mapping.yaml로 유연성 확보. |
| pyhwpx 호환성 (Windows + HWP 전용) | 높음 | 중간 | 개발 환경이 Windows이므로 사용 가능. 비Windows 환경은 python-docx 대체 경로 제공. CI에서 HWP 테스트 skip. |
| Text-to-SQL 정확도 부족 | 높음 | 중간 | 도메인 특화 프롬프트, 쿼리 검증 레이어, few-shot 예제 제공. |
| 대용량 OD 데이터 성능 | 중간 | 중간 | year 기준 파티셔닝, 인덱스, 배치 insert. |
| PostgreSQL 설치/운영 부담 | 중간 | 낮음 | Docker Compose 원클릭 설치. 테스트는 SQLite in-memory 대체. |
| LLM API 비용 | 중간 | 중간 | GPT-4o-mini 기본 사용, 응답 캐싱, 토큰 모니터링. |
| KTDB 샘플 파일 미확보 | 높음 | 낮음 | e-나라지표 등 공개 교통 통계로 대체 테스트. 파서는 제네릭하게 구현. |
| GeoJSON 경계 데이터 미확보 | 낮음 | 낮음 | 통계청 SGIS 또는 국토정보플랫폼 다운로드. 확보 불가 시 단계구분도 후순위 처리. |

---

## 9. 성공 지표 (KPI)

| 지표 | 목표 |
|------|------|
| 처리 시간 단축 | 기존 8시간 → 30분 이내 (90% 개선) |
| 데이터 정확도 | 오기입 0건 |
| 보고서 품질 | 사내 톤앤매너 유지율 90% 이상 |
| 실무자 만족도 | 80% 이상 긍정 응답 |
| 테스트 커버리지 | pytest 전체 통과, 커버리지 80% 이상 |
| 배포 | `docker-compose up` 으로 전체 환경 기동 |

---

## 10. 확인 필요 사항

- [ ] KTDB 웹사이트 계정 및 파일 다운로드 권한 확인 (Phase 0 전제)
- [ ] OpenAI API 키 확보
- [ ] PostgreSQL 운영 환경 결정 (로컬 Docker vs 서버)
- [ ] KTDB 존 체계 문서 (교통분석존 코드표) 확보 경로 확인
- [ ] 사내 보고서 톤앤매너 예시 문서 수집 (LLM 프롬프트 참고용)
- [ ] 한글(HWP) 설치 여부 확인 (pyhwpx 사용 전제)
- [ ] GeoJSON 시군구 경계 데이터 확보 (통계청 SGIS 또는 국토정보플랫폼)
