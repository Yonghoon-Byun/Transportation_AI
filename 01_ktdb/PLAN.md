# KTDB Report Agent - 개발 계획 v3 (실제 데이터 기반 전면 개정)

> **버전**: v3.0 (2026-03-10) — 실제 KTDB zip 파일 25건 분석 결과 반영
> **이전 버전**: v2 (Critic 승인), `.omc/plans/ktdb-plan-review-v2.md` 권고사항 반영
> **변경 사유**: Phase 0 데이터 탐색 결과, 원본 데이터 형식이 기존 가정(xlsx/xls only)과 근본적으로 상이

---

## Phase 0 완료 현황 (2026-03-10 기준)

### DB 테이블 생성 완료 (25개 = 11 메인 + 14 파티션)

> **주의**: `ktdb` 스키마 생성 불가 (Azure PostgreSQL water user에 CREATE SCHEMA 권한 없음)
> → 모든 테이블은 `public` 스키마에 `ktdb_` 접두사로 생성됨 (예: `public.ktdb_zones_17`)
>
> **DB 연결**: Azure PostgreSQL + PgBouncer (port 6432, `sslmode=require`, `prepare_threshold=None`)

### 데이터 적재 현황

| 테이블 | 행 수 | 상태 |
|--------|-------|------|
| ktdb_zones_17 | 17행 | 완료 |
| ktdb_zones_250 | 250행 | 완료 |
| ktdb_zones_subzone | 3,617행 | 완료 |
| ktdb_od_purpose_subzone | 21,292,453행 (6개 권역 × 7년) | 완료 |
| ktdb_od_purpose_250 | 437,500행 | 완료 |
| ktdb_od_freight | 437,500행 | 완료 |
| ktdb_od_mode_250 | 437,500행 | 완료 |
| ktdb_od_mode_subzone | 진행 중 (~31M행, 수도권 로딩 계속) | 진행 중 |
| ktdb_socioeconomic | 111,188행 | 완료 |

### 생성된 스크립트

| 스크립트 | 역할 |
|---------|------|
| `init_schema.py` | DB 스키마(테이블 + 파티션) 초기화 |
| `seed_zones.py` | 3-tier 존체계 시드 적재 |
| `load_out_od.py` | .OUT 형식 목적별 OD 적재 |
| `load_xlsx_od.py` | .xlsx 형식 OD (250존) 적재 |
| `load_mode_od.py` | 수단별 OD 적재 |
| `load_socioeconomic.py` | 사회경제지표 TXT 적재 |

---

## 변경 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v1 | 2026-03-09 | 초기 계획 (xlsx/xls 가정) |
| v2 | 2026-03-10 | Critic 리뷰 반영 (Phase 3 분할, read-only DB, composite index, COPY) |
| **v3** | **2026-03-10** | **실제 데이터 포맷 기반 전면 개정 (.OUT/.TXT 파서, 3-tier 존체계, 스키마 재설계)** |

---

## 1. 프로젝트 개요

### 목표
교통수요예측 기초자료 분석을 위한 KTDB 데이터 수집/가공/분석/보고서 생성 시스템 구축.
LLM 기반 자연어 쿼리로 전체 프로세스를 자동화하여 **30분 이내** 완료.

### AS-IS vs TO-BE

| 항목 | AS-IS (기존) | TO-BE (목표) |
|------|-------------|-------------|
| 데이터 소스 | KTDB zip 수동 다운로드 후 수작업 분석 | Zip 자동 해제 → 멀티포맷 파싱 → DB 적재 |
| 파일 형식 | .OUT(CP949), .TXT(CP949), .xlsx 혼재 | 통합 파서 엔진 (3종 포맷 자동 감지) |
| 데이터 저장 | 파일 기반 (pandas DataFrame) | PostgreSQL DB (파티션 테이블) |
| 분석 방식 | 수동 코딩 + DataFrame 쿼리 | Text-to-SQL (LangChain SQL Agent) |
| 백엔드 | 없음 (Streamlit 단독) | FastAPI REST API (동기 엔드포인트) |
| UI | Streamlit 단독 실행 | Streamlit + FastAPI 연동 |
| 보고서 | 수작업 (약 8시간) | HWP/Excel 자동 생성 (30분 이내) |

### 핵심 아키텍처 결정사항 (변경 없음)
- **Sync SQLAlchemy** 사용 (데이터 분석 도구 특성, async 미사용)
- **psycopg[binary]** (psycopg3 동기 드라이버, asyncpg 미사용)
- **FastAPI 동기 엔드포인트** (`def`, not `async def`)
- **pyhwpx** (Windows + HWP 설치 환경 한정)
- **Read-only DB role** for LLM-generated SQL (v2 권고 반영)
- **LangChain abstraction layer** (v2 권고 반영)

---

## 2. 실제 데이터 포맷 분석 결과 (Phase 0 완료)

### 2.1 데이터 소스: KTDB Zip 파일 25건

Zip 파일 명명 규칙: `{YYYY}-OD-{CAT}-{TYPE}-{REGION_CODE} {설명}.zip`
- `CAT`: PSN (여객) / FRE (화물)
- `TYPE`: OBJ (목적별) / MOD (수단별) / CAR (화물차)
- `REGION_CODE`: 00(전국250존), 01(수도권), 02(부산울산), 03(대구), 04(대전세종충청), 05(광주), 06(제주)

### 2.2 OD 데이터 — 2가지 포맷

#### Format A: .OUT 텍스트 파일 (권역별 소존 OD) — 주력 데이터

```
O_seq  O_zone   D_seq  D_zone   출근      등교      업무      귀가      합계
1      1101072  1      1101072  1293.031  205.414   464.115   1112.201  3949.478
1      1101072  2      1101053  773.66    646.652   68.285    754.723   2629.308
```

| 속성 | 값 |
|------|-----|
| 인코딩 | CP949 |
| 구분자 | 공백 (space-delimited, 가변 폭) |
| 컬럼 수 | 고정 9개 (목적OD) / 가변 (수단OD) |
| 존 코드 | 7자리 (예: `1101072` = 서울 종로구 청운효자동) |
| 규모 | 권역별 1,310존 (수도권) → **1,716,100 rows/year** |
| 연도 | 2023, 2025, 2030, 2035, 2040, 2045, 2050 (7개년) |
| 목적 컬럼 | 출근, 등교, 업무, 귀가, 합계 (NOT 통근/통학/쇼핑) |
| 파일 패턴 | `ODTRIP{YY}_F.OUT` (목적), `ODMOD{YY}_{MODE}.OUT` (수단) |

#### Format B: .xlsx (전국 250존 OD)

```
출발시도 | 도착시도 | 출발시군구 | 도착시군구 | 출근 | 등교 | 업무 | 귀가 | 기타 | 합계
1       | 1       | 1         | 1         | 19800| 2838 | 10588| 36255| 36197| 105679
```

| 속성 | 값 |
|------|-----|
| 형식 | 이미 Long format (N×N 매트릭스가 아님) |
| 시트명 | `YYYY_목적OD` (데이터), `대존_YYYY` (피벗 요약, SUMIFS 수식) |
| 존 코드 | 정수 1-250 |
| 규모 | ~62,500 rows/year |
| 기타 컬럼 | 출근, 등교, 업무, 귀가, **기타**, 합계 |

#### 수단별 OD (.OUT)

```
O_seq  O_zone   D_seq  D_zone   MOD01    MOD02    MOD03    ...
```
- 수단 코드: MOD01(승용차), MOD02(버스), MOD03(철도) 등
- 별도 zip 파일로 제공 (MOD-10~16: 권역별)

#### 목적별 수단 OD (.OUT)

```
O_seq  O_zone   D_seq  D_zone   출근_승용  출근_버스  출근_철도  ...  귀가_기타
```
- 목적 x 수단 교차 컬럼 (최대 30+ 컬럼)

### 2.3 사회경제지표 — TXT 파일

```
3. 사회경제지표/
├── 인구수/       SUB_POP{YY}.TXT     (~2.3MB, 소존별, ~1,310행)
├── 종사자수/     WORK_POP{YY}.TXT    (~48KB, 시군구별)
├── 취업자수/     EMP_POP_{YY}.TXT    (~2.3MB, 소존별)
└── 학생수/       STU_POP{YY}.TXT     (~82KB)
```

| 속성 | 값 |
|------|-----|
| 인코딩 | CP949 |
| 연도 | 23, 25, 30, 35, 40, 45, 50 (7개년) |
| 구분 | 소존 단위 (인구, 취업자) / 시군구 단위 (종사자, 학생) |

### 2.4 존체계 — 3단계

| 존체계 | 소스 파일 | 존 수 | 용도 |
|--------|----------|-------|------|
| **소존 (7자리)** | `존체계.xlsx` | 1,310 (수도권) | .OUT 파일 매칭 |
| **250존** | `250 존체계.xlsx` | 250 (전국) | .xlsx OD 매칭, 화물OD |
| **17존 (시도)** | `250 존체계.xlsx` 내 매핑 | 17 | 집계/요약 |

존체계 상호 매핑:
- 소존 → 시군구 → 250존 → 17존 (상향 집계 가능)
- `존체계.xlsx`: 시도, 시군구, 행정동, 존번호, 행정기관코드
- `250 존체계.xlsx`: 대존(시도), 소존(시군구), 250존, 161존, 17존

### 2.5 화물 OD — xlsx

```
O_250 | 대존O_17 | D_250 | 대존O_17 | 소형 | 중형 | 대형 | 전체
```

| 속성 | 값 |
|------|-----|
| 분류 기준 | 톤급 (소형/중형/대형), NOT 품목별(commodity_type) |
| 존체계 | 250존 |
| 규모 | ~62,500 rows |

### 2.6 부가 데이터

| 데이터 | 형식 | 비고 |
|--------|------|------|
| 설명자료 | .hwp/.hwpx | 메타데이터/방법론 문서, 파싱 불필요 |
| 사회경제지표 요약 | .xlsx | 기존 사회경제지표 테이블의 요약판 |
| 교통량(AADT) | .xlsx | 참고용 교통량 데이터 |

---

## 3. 시스템 아키텍처 (v3 개정)

```
[KTDB Zip 파일들]
      |
      v (zip 해제 + 폴더 구조 탐색)
[Zip Extractor] ──> [Format Router]
                         |
              +----------+----------+
              |          |          |
              v          v          v
        [OUT Parser] [TXT Parser] [XLSX Parser]
        (CP949,공백)  (CP949)     (openpyxl)
              |          |          |
              +----------+----------+
                         |
                         v
                  [Schema Mapper]
                  (column_mapping.yaml)
                         |
                         v
              [PostgreSQL COPY Loader]
              (psycopg.copy, 배치)
                         |
                         v
                   [PostgreSQL DB]
                   (파티션 테이블)
                         |
              +----------+----------+
              |                     |
              v                     v
    [Read-Write Session]    [Read-Only Session]
    (적재/관리용)           (LLM 쿼리 전용)
                                    |
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

### 데이터 흐름 요약 (v3)
1. 사용자가 KTDB 웹사이트에서 zip 파일 다운로드 → `data/uploads/` 배치
2. Zip Extractor가 자동 해제 → 폴더 구조 탐색 → 파일 유형 감지
3. Format Router가 파일 확장자 + 내용 기반 적절한 파서 선택
4. 파서별 처리: .OUT(공백구분, CP949) / .TXT(CP949) / .xlsx(openpyxl)
5. Schema Mapper가 파싱 결과를 DB 스키마에 매핑
6. PostgreSQL COPY로 bulk 적재 (upload_history 기록)
7. 사용자가 자연어 쿼리 입력 → Text-to-SQL → Read-Only DB 조회
8. 분석 결과 + LLM 문구 생성 → 보고서(HWP/Excel) 다운로드

---

## 4. 폴더 구조 (v3 개정)

```
01_ktdb/
├── src/
│   ├── collector/              # 멀티포맷 파서 + DB 적재
│   │   ├── __init__.py
│   │   ├── zip_extractor.py    # (신규) zip 해제, 폴더 구조 탐색, 파일 목록 반환
│   │   ├── format_router.py    # (신규) 파일 확장자/내용 기반 파서 라우팅
│   │   ├── out_parser.py       # (신규) .OUT 파일 파서 (CP949, space-delimited)
│   │   ├── txt_parser.py       # (신규) .TXT 사회경제지표 파서 (CP949)
│   │   ├── xlsx_parser.py      # (개명) 기존 file_parser.py → xlsx 전용
│   │   ├── schema_mapper.py    # (개정) 3종 포맷 대응 매핑
│   │   ├── loader.py           # (개정) psycopg.copy 기반 COPY 로더
│   │   └── models.py           # Pydantic 파싱 DTO
│   ├── db/                     # 데이터베이스 모듈
│   │   ├── __init__.py
│   │   ├── connection.py       # (개정) read-write + read-only 이중 세션
│   │   ├── models.py           # (개정) ORM 9개 테이블 + 파티션
│   │   ├── repository.py       # CRUD 레포지토리
│   │   ├── seed.py             # (개정) 3-tier 존체계 시드
│   │   └── migrations/         # Alembic 마이그레이션
│   ├── preprocessor/           # DB 기반 전처리
│   │   ├── __init__.py
│   │   ├── pipeline.py         # DB read → clean → write
│   │   ├── cleaner.py          # 결측치/이상치 정제
│   │   ├── aggregator.py       # SQL 기반 집계 (소존→250존→17존 롤업)
│   │   └── zone_aggregator.py  # (신규) 존체계간 집계 변환
│   ├── analyzer/               # Text-to-SQL 분석
│   │   ├── __init__.py
│   │   ├── text_to_sql.py      # LangChain SQL 변환기 (read-only 전용)
│   │   ├── sql_agent.py        # LangChain SQL Agent
│   │   ├── sql_validator.py    # (신규) sqlparse AST 기반 SELECT 검증
│   │   ├── statistics.py       # 통계 분석 함수
│   │   └── summary.py          # LLM 분석 결과 요약
│   ├── visualizer/             # 시각화
│   │   ├── __init__.py
│   │   ├── charts.py           # plotly 차트
│   │   └── tables.py           # 보고서용 표 스타일링
│   ├── reporter/               # 보고서 생성
│   │   ├── __init__.py
│   │   ├── hwp_generator.py    # pyhwpx HWP 생성
│   │   ├── excel_generator.py  # openpyxl Excel 생성
│   │   └── text_generator.py   # LLM 분석 문구 생성
│   ├── api/                    # FastAPI 백엔드
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI 앱 엔트리포인트
│   │   ├── deps.py             # 의존성 주입 (rw + ro 세션)
│   │   ├── schemas.py          # Pydantic 요청/응답 스키마
│   │   └── routes/
│   │       ├── upload.py       # POST /api/upload (zip 업로드)
│   │       ├── data.py         # GET /api/data/{category}
│   │       ├── analysis.py     # POST /api/analysis/statistics
│   │       ├── query.py        # POST /api/query (자연어)
│   │       └── report.py       # POST /api/report/generate
│   ├── agent/                  # LLM 에이전트
│   │   ├── __init__.py
│   │   ├── llm_agent.py        # 전체 플로우 오케스트레이션
│   │   ├── prompt_templates.py # 교통 도메인 프롬프트
│   │   └── tools.py            # DB 쿼리/분석/보고서 도구
│   ├── ui/                     # Streamlit 웹 UI
│   │   ├── app.py              # FastAPI 연동 메인 앱
│   │   ├── components/         # chat.py, data_viewer.py, upload.py
│   │   └── pages/              # dashboard.py, query.py, report.py, upload.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── decorators.py
├── config/
│   ├── settings.py             # pydantic-settings 기반
│   ├── .env.example
│   ├── zone_config.yaml        # (개정) 3-tier 존체계 매핑 마스터
│   ├── column_mapping.yaml     # (전면 재작성) 3종 파일 포맷 매핑
│   └── file_patterns.yaml      # (신규) zip 내 파일명 패턴 → 데이터 카테고리 매핑
├── alembic/
│   ├── alembic.ini
│   └── versions/
├── data/
│   ├── uploads/                # zip 파일 업로드 저장
│   ├── extracted/              # (신규) zip 해제 임시 폴더
│   ├── outputs/                # 생성된 보고서
│   ├── samples/                # 테스트용 샘플 파일
│   └── geo/                    # 시군구 GeoJSON
├── tests/
│   ├── conftest.py             # pytest fixtures (sync DB 세션)
│   ├── fixtures/               # (개정) .OUT, .TXT, .xlsx 샘플 모두 포함
│   │   ├── sample_od.out       # 소규모 .OUT 샘플
│   │   ├── sample_pop.txt      # 소규모 .TXT 샘플
│   │   ├── sample_od_250.xlsx  # 소규모 xlsx 샘플
│   │   └── sample_zone.xlsx    # 존체계 샘플
│   ├── test_db.py
│   ├── test_out_parser.py      # (신규) .OUT 파서 전용 테스트
│   ├── test_txt_parser.py      # (신규) .TXT 파서 전용 테스트
│   ├── test_xlsx_parser.py     # (개명) 기존 test_collector.py
│   ├── test_zip_extractor.py   # (신규) zip 해제 테스트
│   ├── test_schema_mapper.py   # (신규) 매핑 테스트
│   ├── test_loader.py          # (신규) COPY 로더 테스트
│   ├── test_preprocessor.py
│   ├── test_analyzer.py
│   ├── test_agent.py
│   ├── test_visualizer.py
│   ├── test_api.py
│   └── test_e2e.py
├── notebooks/
│   ├── 00_ktdb_file_format_eda.ipynb   # (완료) Phase 0 EDA
│   ├── 01_out_parser_prototype.ipynb   # (신규) .OUT 파서 프로토타입
│   ├── 02_zone_system_mapping.ipynb    # (신규) 존체계 매핑 검증
│   ├── 03_copy_benchmark.ipynb         # (신규) COPY 로딩 벤치마크
│   ├── 04_text_to_sql_test.ipynb
│   └── 05_eda.ipynb
├── requirements.txt
├── pytest.ini
├── docker-compose.yml
├── CLAUDE.md
├── PLAN.md
└── README.md
```

---

## 5. PostgreSQL 스키마 설계 (v3 — 9개 테이블)

> **실제 구현 주의**: 모든 테이블은 `public` 스키마에 `ktdb_` 접두사로 생성.
> (예: `zones_subzone` → `ktdb_zones_subzone`, `od_purpose_subzone` → `ktdb_od_purpose_subzone`)

### 5.1 존(zone) 마스터 — 3-tier 통합

```sql
-- 1. 소존 마스터 (7자리, 권역별)
CREATE TABLE ktdb_zones_subzone (
    id SERIAL PRIMARY KEY,
    zone_code VARCHAR(10) UNIQUE NOT NULL,       -- 7자리 (예: 1101072)
    zone_seq INTEGER,                            -- O_seq/D_seq
    dong_name VARCHAR(100),                      -- 행정동명
    sigungu_code VARCHAR(10),                    -- 시군구 코드
    sigungu_name VARCHAR(100),                   -- 시군구명
    sido_code VARCHAR(5),                        -- 시도 코드
    sido_name VARCHAR(50),                       -- 시도명
    admin_code VARCHAR(20),                      -- 행정기관코드
    region_id VARCHAR(5) NOT NULL,               -- 권역 코드 (01=수도권, 02=부산울산 등)
    zone_250 INTEGER REFERENCES ktdb_zones_250(zone_code_250),
    centroid_lat DOUBLE PRECISION,
    centroid_lon DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_ktdb_zones_subzone_region ON ktdb_zones_subzone(region_id);
CREATE INDEX idx_ktdb_zones_subzone_sigungu ON ktdb_zones_subzone(sigungu_code);

-- 2. 250존 마스터 (전국)
CREATE TABLE ktdb_zones_250 (
    id SERIAL PRIMARY KEY,
    zone_code_250 INTEGER UNIQUE NOT NULL,       -- 1~250
    zone_name VARCHAR(100),
    sido_code VARCHAR(5),
    sido_name VARCHAR(50),
    zone_161 INTEGER,
    zone_17 INTEGER REFERENCES ktdb_zones_17(zone_code_17),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. 17존 마스터 (시도 대분류)
CREATE TABLE ktdb_zones_17 (
    id SERIAL PRIMARY KEY,
    zone_code_17 INTEGER UNIQUE NOT NULL,        -- 1~17
    sido_name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 사회경제지표 — 소존/시군구 이중 단위

```sql
-- 4. 사회경제지표
CREATE TABLE ktdb_socioeconomic (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    zone_level VARCHAR(10) NOT NULL,             -- 'subzone' / 'sigungu'
    zone_code VARCHAR(10) NOT NULL,
    indicator_type VARCHAR(20) NOT NULL,         -- 'population' / 'employment' / 'worker' / 'student'
    value DOUBLE PRECISION NOT NULL,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, zone_code, indicator_type)
);
CREATE INDEX idx_ktdb_socio_year_type ON ktdb_socioeconomic(year, indicator_type);
CREATE INDEX idx_ktdb_socio_zone ON ktdb_socioeconomic(zone_code);
```

### 5.3 여객 OD — 목적별 (소존 .OUT + 250존 .xlsx)

```sql
-- 5. 목적별 OD (권역 소존, .OUT 파일 — 주력 데이터)
CREATE TABLE ktdb_od_purpose_subzone (
    id BIGSERIAL,
    year INTEGER NOT NULL,
    region_id VARCHAR(5) NOT NULL,
    origin_zone VARCHAR(10) NOT NULL,
    destination_zone VARCHAR(10) NOT NULL,
    commute DOUBLE PRECISION DEFAULT 0,          -- 출근
    school DOUBLE PRECISION DEFAULT 0,           -- 등교
    business DOUBLE PRECISION DEFAULT 0,         -- 업무
    return_home DOUBLE PRECISION DEFAULT 0,      -- 귀가
    total DOUBLE PRECISION DEFAULT 0,            -- 합계
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (year);

CREATE TABLE ktdb_od_purpose_subzone_2023 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2023) TO (2024);
CREATE TABLE ktdb_od_purpose_subzone_2025 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2025) TO (2026);
CREATE TABLE ktdb_od_purpose_subzone_2030 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2030) TO (2031);
CREATE TABLE ktdb_od_purpose_subzone_2035 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2035) TO (2036);
CREATE TABLE ktdb_od_purpose_subzone_2040 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2040) TO (2041);
CREATE TABLE ktdb_od_purpose_subzone_2045 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2045) TO (2046);
CREATE TABLE ktdb_od_purpose_subzone_2050 PARTITION OF ktdb_od_purpose_subzone FOR VALUES FROM (2050) TO (2051);

CREATE INDEX idx_ktdb_od_purp_sub_lookup ON ktdb_od_purpose_subzone(year, origin_zone, destination_zone);
CREATE INDEX idx_ktdb_od_purp_sub_origin ON ktdb_od_purpose_subzone(year, origin_zone);
CREATE INDEX idx_ktdb_od_purp_sub_region ON ktdb_od_purpose_subzone(year, region_id);
CREATE UNIQUE INDEX idx_ktdb_od_purp_sub_unique
    ON ktdb_od_purpose_subzone(year, region_id, origin_zone, destination_zone);

-- 6. 목적별 OD (전국 250존, .xlsx 파일)
CREATE TABLE ktdb_od_purpose_250 (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    origin_sido INTEGER,
    origin_sigungu INTEGER,
    destination_sido INTEGER,
    destination_sigungu INTEGER,
    commute DOUBLE PRECISION DEFAULT 0,
    school DOUBLE PRECISION DEFAULT 0,
    business DOUBLE PRECISION DEFAULT 0,
    return_home DOUBLE PRECISION DEFAULT 0,
    etc DOUBLE PRECISION DEFAULT 0,
    total DOUBLE PRECISION DEFAULT 0,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, origin_sigungu, destination_sigungu)
);
CREATE INDEX idx_ktdb_od_purp_250_lookup ON ktdb_od_purpose_250(year, origin_sigungu, destination_sigungu);
```

### 5.4 여객 OD — 수단별

```sql
-- 7. 수단별 OD (소존 .OUT)
CREATE TABLE ktdb_od_mode_subzone (
    id BIGSERIAL,
    year INTEGER NOT NULL,
    region_id VARCHAR(5) NOT NULL,
    origin_zone VARCHAR(10) NOT NULL,
    destination_zone VARCHAR(10) NOT NULL,
    mode_code VARCHAR(10) NOT NULL,              -- MOD01(승용차), MOD02(버스), MOD03(철도) 등
    volume DOUBLE PRECISION DEFAULT 0,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (year);

CREATE TABLE ktdb_od_mode_subzone_2023 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2023) TO (2024);
CREATE TABLE ktdb_od_mode_subzone_2025 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2025) TO (2026);
CREATE TABLE ktdb_od_mode_subzone_2030 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2030) TO (2031);
CREATE TABLE ktdb_od_mode_subzone_2035 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2035) TO (2036);
CREATE TABLE ktdb_od_mode_subzone_2040 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2040) TO (2041);
CREATE TABLE ktdb_od_mode_subzone_2045 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2045) TO (2046);
CREATE TABLE ktdb_od_mode_subzone_2050 PARTITION OF ktdb_od_mode_subzone FOR VALUES FROM (2050) TO (2051);

CREATE INDEX idx_ktdb_od_mode_sub_lookup ON ktdb_od_mode_subzone(year, origin_zone, destination_zone);
CREATE INDEX idx_ktdb_od_mode_sub_mode ON ktdb_od_mode_subzone(year, mode_code);
CREATE UNIQUE INDEX idx_ktdb_od_mode_sub_unique
    ON ktdb_od_mode_subzone(year, region_id, origin_zone, destination_zone, mode_code);
```

### 5.5 화물 OD

```sql
-- 8. 화물 OD (250존, 톤급별)
CREATE TABLE ktdb_od_freight (
    id BIGSERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    origin_zone_250 INTEGER NOT NULL,
    origin_zone_17 INTEGER,
    destination_zone_250 INTEGER NOT NULL,
    destination_zone_17 INTEGER,
    tonnage_small DOUBLE PRECISION DEFAULT 0,    -- 소형
    tonnage_medium DOUBLE PRECISION DEFAULT 0,   -- 중형
    tonnage_large DOUBLE PRECISION DEFAULT 0,    -- 대형
    tonnage_total DOUBLE PRECISION DEFAULT 0,    -- 전체
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, origin_zone_250, destination_zone_250)
);
CREATE INDEX idx_ktdb_od_freight_lookup ON ktdb_od_freight(year, origin_zone_250, destination_zone_250);
```

### 5.6 시스템 테이블

```sql
-- 9. 업로드 이력
CREATE TABLE ktdb_upload_history (
    id SERIAL PRIMARY KEY,
    zip_filename VARCHAR(500),
    extracted_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,              -- out / txt / xlsx
    data_category VARCHAR(50) NOT NULL,
    region_id VARCHAR(5),
    year INTEGER,
    row_count INTEGER,
    status VARCHAR(20) DEFAULT 'pending',        -- pending / processing / completed / partial_success / failed
    error_message TEXT,
    last_success_row INTEGER,                    -- 재시도용
    uploaded_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 10. 쿼리 이력 (LLM 로그)
CREATE TABLE ktdb_query_history (
    id SERIAL PRIMARY KEY,
    user_query TEXT NOT NULL,
    generated_sql TEXT,
    result_summary TEXT,
    execution_time_ms INTEGER,
    confidence_score DOUBLE PRECISION,
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.7 Read-Only Role (v2 권고 반영)

```sql
CREATE ROLE ktdb_readonly WITH LOGIN PASSWORD '${READONLY_PASSWORD}';
GRANT CONNECT ON DATABASE ktdb TO ktdb_readonly;
GRANT USAGE ON SCHEMA public TO ktdb_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ktdb_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ktdb_readonly;
```

### 5.8 데이터 볼륨 추정

| 테이블 | 행 수/연 | 연도 수 | 총 행 수 | 비고 |
|--------|---------|---------|---------|------|
| ktdb_od_purpose_subzone | 1,716,100 (수도권) | 7 | ~12M (수도권만) | 6개 권역 합산 시 증가 |
| ktdb_od_purpose_250 | 62,500 | 7 | ~438K | 경량 |
| ktdb_od_mode_subzone | 1,716,100 x N_modes | 7 | ~60M+ (수도권, 5수단) | 가장 대규모 |
| ktdb_od_freight | 62,500 | 1 | ~63K | 경량 |
| ktdb_socioeconomic | ~1,310 x 4지표 | 7 | ~37K | 경량 |
| ktdb_zones_subzone | ~1,310 (수도권) | - | ~8K (전권역) | 마스터 |
| ktdb_zones_250 | 250 | - | 250 | 마스터 |
| ktdb_zones_17 | 17 | - | 17 | 마스터 |

**핵심**: OD 소존 테이블이 수천만 행 규모 → PostgreSQL COPY + 파티션 필수

---

## 6. 설정 파일 스펙 (v3)

### 6.1 file_patterns.yaml (신규)

```yaml
patterns:
  od_purpose_subzone:
    file_glob: "ODTRIP*_F.OUT"
    parser: out
    year_regex: "ODTRIP(\\d{2})_F\\.OUT"

  od_mode_subzone:
    file_glob: "ODMOD*_*.OUT"
    parser: out
    year_regex: "ODMOD(\\d{2})_(\\w+)\\.OUT"

  od_purpose_250:
    file_glob: "*목적OD*.xlsx"
    parser: xlsx
    sheet_pattern: "{YYYY}_목적OD"

  od_freight:
    file_glob: "*화물*톤급*.xlsx"
    parser: xlsx

  socioeconomic_population:
    file_glob: "SUB_POP*.TXT"
    parser: txt
    year_regex: "SUB_POP(\\d{2})\\.TXT"

  socioeconomic_worker:
    file_glob: "WORK_POP*.TXT"
    parser: txt

  socioeconomic_employment:
    file_glob: "EMP_POP_*.TXT"
    parser: txt

  socioeconomic_student:
    file_glob: "STU_POP*.TXT"
    parser: txt

ignore:
  - "*.hwp"
  - "*.hwpx"
  - "설명자료*"
  - "*.pdf"

year_mapping:
  "23": 2023
  "25": 2025
  "30": 2030
  "35": 2035
  "40": 2040
  "45": 2045
  "50": 2050

region_mapping:
  "00": { name: "전국", zone_system: "250" }
  "01": { name: "수도권", zone_system: "subzone" }
  "02": { name: "부산울산권", zone_system: "subzone" }
  "03": { name: "대구광역권", zone_system: "subzone" }
  "04": { name: "대전세종충청권", zone_system: "subzone" }
  "05": { name: "광주광역권", zone_system: "subzone" }
  "06": { name: "제주권", zone_system: "subzone" }
```

### 6.2 column_mapping.yaml (v3 전면 재작성)

```yaml
out_format:
  od_purpose:
    columns:
      - { index: 0, name: "O_seq", db_field: null, type: int }
      - { index: 1, name: "O_zone", db_field: "origin_zone", type: str }
      - { index: 2, name: "D_seq", db_field: null, type: int }
      - { index: 3, name: "D_zone", db_field: "destination_zone", type: str }
      - { index: 4, name: "출근", db_field: "commute", type: float }
      - { index: 5, name: "등교", db_field: "school", type: float }
      - { index: 6, name: "업무", db_field: "business", type: float }
      - { index: 7, name: "귀가", db_field: "return_home", type: float }
      - { index: 8, name: "합계", db_field: "total", type: float }
    encoding: cp949
    delimiter: space

xlsx_format:
  od_purpose_250:
    sheet_pattern: "{YYYY}_목적OD"
    columns:
      출발시도: origin_sido
      도착시도: destination_sido
      출발시군구: origin_sigungu
      도착시군구: destination_sigungu
      출근: commute
      등교: school
      업무: business
      귀가: return_home
      기타: etc
      합계: total
    skip_sheets: ["대존_*"]

  od_freight:
    columns:
      O_250: origin_zone_250
      대존O_17: origin_zone_17
      D_250: destination_zone_250
      대존D_17: destination_zone_17
      소형: tonnage_small
      중형: tonnage_medium
      대형: tonnage_large
      전체: tonnage_total

purpose_categories:
  출근: commute
  등교: school
  업무: business
  귀가: return_home
  기타: etc
  합계: total
  # 이전 가정값 (사용 안 함): 통근, 통학, 쇼핑
```

---

## 7. 개발 단계 (Phase 0.5 ~ 5)

### Phase 0: 데이터 획득 및 포맷 분석 — 완료

**Status**: DONE (v3 작성의 근거)

| Task | 상태 | 결과 |
|------|------|------|
| 0.1 KTDB zip 파일 확보 | 완료 | 25건 zip |
| 0.2 파일 포맷 EDA | 완료 | .OUT/.TXT/.xlsx 3종 포맷 확인 |
| 0.3 존체계 분석 | 완료 | 3-tier (소존/250존/17존) 확인 |
| 0.4 컬럼명 확인 | 완료 | 출근/등교/업무/귀가 (not 통근/통학/쇼핑) |

---

### Phase 0.5: 파서 프로토타입 & 검증 (0.5주)
**Goal**: 실제 데이터로 3종 파서 프로토타입 동작 확인

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 0.5.1 .OUT 파서 프로토타입 | `notebooks/01_out_parser_prototype.ipynb` | CP949 인코딩, split() 파싱, 9컬럼 추출 | 1,716,100행 파싱, 0 에러 |
| 0.5.2 .TXT 파서 프로토타입 | `notebooks/01_out_parser_prototype.ipynb` | SUB_POP23.TXT 파싱 검증 | 파싱 성공, 레코드 수 일치 |
| 0.5.3 존체계 매핑 검증 | `notebooks/02_zone_system_mapping.ipynb` | 소존→250존→17존 매핑 완전성 검증 | 매핑 누락 0건 |
| 0.5.4 COPY 벤치마크 | `notebooks/03_copy_benchmark.ipynb` | 1.7M행 COPY 로딩 시간 측정 | < 60초 목표 |
| 0.5.5 config 초안 작성 | `config/file_patterns.yaml`, `column_mapping.yaml` | EDA 결과 기반 실제 매핑 작성 | 실제 파일 파싱 결과와 매핑 일치 |

**Phase 0.5 완료 조건**: 3종 파서 프로토타입 동작 확인 + config 초안 + COPY 벤치마크 결과

---

### Phase 1: 기초 인프라 & DB 구축 (1주)
**Goal**: PostgreSQL 환경 + 9개 테이블 ORM + 3-tier 존 시드 + Read-Only Role

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 1.1 config/ 생성 | `config/settings.py`, `.env.example`, `zone_config.yaml`, `column_mapping.yaml`, `file_patterns.yaml` | pydantic-settings, 환경변수, 3종 YAML 설정 | `from config.settings import settings` 정상 |
| 1.2 Docker Compose | `docker-compose.yml` | PostgreSQL 16 컨테이너, 볼륨, read-only role 초기화 스크립트 | `docker-compose up -d` 성공 |
| 1.3 DB 모듈 구현 | `src/db/connection.py`, `models.py`, `repository.py`, `seed.py` | Sync SQLAlchemy engine, **2개 세션 팩토리** (rw + ro), ORM 9개 테이블 (파티션 포함), 3-tier 존 시드 | ORM CRUD + 파티션 테이블 동작 확인 |
| 1.4 Alembic 설정 | `alembic/`, `alembic.ini` | 마이그레이션 초기화, 파티션 테이블 포함 초기 스크립트 | `alembic upgrade head` 전체 스키마 + 파티션 생성 |
| 1.5 존체계 시드 적재 | `src/db/seed.py` | `존체계.xlsx`, `250 존체계.xlsx` 파싱 → zones_subzone, zones_250, zones_17 적재 | 3개 존 테이블 시드 완료, 매핑 무결성 확인 |
| 1.6 기존 파일 정리 | - | 불필요 파일 삭제 (api_client.py, query_engine.py) | 삭제 확인 |
| 1.7 테스트 인프라 | `tests/conftest.py`, `tests/test_db.py`, `pytest.ini` | SQLite in-memory (파티션 제외), ORM CRUD 단위 테스트 | `pytest tests/test_db.py` 통과 |

**Phase 1 완료 조건**: PostgreSQL 9개 테이블 + 파티션 생성, 3-tier 존 시드 적재, read-only role 동작, test_db.py 통과

---

### Phase 2: 데이터 수집 & 적재 파이프라인 (1.5주)
**Goal**: zip → 멀티포맷 파싱 → PostgreSQL COPY 적재

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 2.1 Zip Extractor | `src/collector/zip_extractor.py` | zip/7z 해제, 폴더 구조 탐색, 파일 목록 + 메타데이터 반환 | 실제 zip 25건 해제 성공 |
| 2.2 Format Router | `src/collector/format_router.py` | `file_patterns.yaml` 기반 파일→파서+카테고리 자동 매핑 | 25건 zip 내 모든 데이터 파일 정확 라우팅 |
| 2.3 .OUT Parser | `src/collector/out_parser.py` | CP949, `str.split()` 파싱, 9컬럼(목적) / 동적컬럼(수단), DataFrame 반환 | ODTRIP23_F.OUT 1.7M행 파싱 < 30초, 0 에러 |
| 2.4 .TXT Parser | `src/collector/txt_parser.py` | CP949, 사회경제지표 TXT 파싱, indicator_type 자동 분류 | SUB_POP23.TXT 파싱 성공 |
| 2.5 .xlsx Parser | `src/collector/xlsx_parser.py` | openpyxl 기반, 시트명 패턴 매칭, `대존_*` 시트 무시, 250존 OD/화물OD | 250존 OD xlsx 파싱 성공 |
| 2.6 Schema Mapper | `src/collector/schema_mapper.py` | `column_mapping.yaml` 기반, 3종 포맷 → DB 테이블 매핑, 존코드 검증 | 매핑 정확성 100% |
| 2.7 COPY Loader | `src/collector/loader.py` | `psycopg.copy` 기반 bulk COPY, 배치 처리 (10만행 단위), savepoint 기반 에러 복구, 진행률 콜백 | 1.7M행 < 2분, partial_success 처리 |
| 2.8 Upload Pipeline | `src/collector/pipeline.py` | zip → extract → route → parse → map → load 전체 오케스트레이션 | zip 1건 전체 파이프라인 동작 |
| 2.9 업로드 API | `src/api/main.py`, `routes/upload.py`, `schemas.py`, `deps.py` | POST /api/upload (zip), GET /api/upload/status/{id}, GET /api/upload/history | Swagger UI zip 업로드 → DB 적재 정상 |
| 2.10 파서 테스트 | `tests/test_out_parser.py`, `test_txt_parser.py`, `test_xlsx_parser.py`, `test_zip_extractor.py`, `test_schema_mapper.py`, `test_loader.py` | 파서별 단위 테스트, 에지케이스 | 전체 파서 테스트 통과 |

**Phase 2 완료 조건**: 실제 KTDB zip 파일 업로드 → 자동 해제 → 3종 포맷 파싱 → DB COPY 적재 → 이력 조회 정상

**성능 목표**:
- .OUT 1.7M행 파싱: < 30초
- .OUT 1.7M행 COPY 적재: < 2분
- zip 1건 전체 파이프라인 (해제+파싱+적재): < 5분
- 25건 zip 전체 적재: < 2시간

---

### Phase 3A: 전처리 & 통계 분석 (1주)
**Goal**: DB 기반 데이터 정제, 존체계 집계, 통계 분석

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 3A.1 데이터 정제 | `src/preprocessor/pipeline.py`, `cleaner.py` | DB read → 결측치/이상치 탐지 → 정제, IQR/z-score | 정제 파이프라인 동작 |
| 3A.2 존체계 집계 | `src/preprocessor/zone_aggregator.py` | 소존 → 시군구 → 250존 → 17존 롤업 집계 SQL | 소존 OD → 250존 OD 집계 정확성 검증 |
| 3A.3 SQL 기반 집계 | `src/preprocessor/aggregator.py` | 연도별/권역별/목적별 집계 뷰, 시계열 증감 계산 | 집계 쿼리 성능 < 5초 |
| 3A.4 통계 분석 | `src/analyzer/statistics.py` | describe, growth_rate, rank, modal_share(수단분담률), 이상치 탐지 | 통계 함수 단위 테스트 통과 |
| 3A.5 전처리 테스트 | `tests/test_preprocessor.py` | 정제/집계/통계 단위 테스트 | `pytest tests/test_preprocessor.py` 통과 |

**Phase 3A 완료 조건**: 소존→250존 집계 정확, 통계 함수 동작, 전처리 파이프라인 검증

---

### Phase 3B: LLM 에이전트 & Text-to-SQL (1.5주)
**Goal**: 자연어 쿼리로 DB 데이터 추출/분석 (Read-Only 연결 전용)

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 3B.1 SQL Validator | `src/analyzer/sql_validator.py` | sqlparse AST 기반 SELECT 전용 검증 (2차 방어선) | 악의적 쿼리 100% 차단 |
| 3B.2 Text-to-SQL 엔진 | `src/analyzer/text_to_sql.py` | LangChain SQLDatabaseChain, **read-only 세션 전용**, 교통 도메인 few-shot | "2023년 수도권 출근 통행량 상위 10개 OD" → 정확 SQL |
| 3B.3 SQL Agent | `src/analyzer/sql_agent.py` | LangChain SQL Agent, 쿼리 이력 저장, confidence_score 산출 | 복합 쿼리 처리 (시계열 비교, 수단분담률 등) |
| 3B.4 분석 요약 | `src/analyzer/summary.py`, `src/reporter/text_generator.py` | LLM 기반 분석 문구 생성 | 분석 결과 → 한글 문구 생성 |
| 3B.5 LLM Agent | `src/agent/llm_agent.py`, `prompt_templates.py`, `tools.py` | SQL Agent + 분석 + 보고서 오케스트레이션, 교통 도메인 프롬프트 | 자연어 → SQL → 분석 → 문구 전체 플로우 |
| 3B.6 분석/쿼리 API | `src/api/routes/data.py`, `analysis.py`, `query.py` | GET /api/data/{category}, POST /api/analysis/statistics, POST /api/query | API로 자연어 쿼리 실행 정상 |
| 3B.7 Text-to-SQL 검증 | `tests/test_analyzer.py`, `tests/test_agent.py` | **30+ 쿼리 테스트셋** (단순조회, 집계, 다중테이블, 시계열, OD), 정확도 90%+ | 테스트셋 90%+ 정확도 |

**Text-to-SQL 검증 프로토콜**:
1. 30+ 쿼리 테스트셋 (복잡도 5등급: 단순조회/단일집계/다중테이블/시계열비교/OD분석)
2. 정확도 목표: 90%+ (핵심 쿼리 패턴)
3. 신뢰도 점수: 0.0~1.0, 0.7 미만 시 사용자에게 수동 확인 유도
4. 실패 3회 시 사전 정의 쿼리 템플릿 제안

**Phase 3B 완료 조건**: 자연어 → SQL → Read-Only DB 조회 → 분석 + 문구 반환 전체 동작, 테스트셋 90%+

---

### Phase 4: 시각화 & 보고서 & 웹 UI (1.5주)
**Goal**: 대화형 대시보드 + 자동 보고서 생성

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 4.1 차트 빌더 | `src/visualizer/charts.py`, `tables.py` | bar/line/heatmap/scatter/choropleth, OD 행렬 히트맵, 수단분담률 파이차트 | 차트 생성 정상 |
| 4.2 HWP 생성기 | `src/reporter/hwp_generator.py` | pyhwpx 기반, 표/차트 삽입, 목적별(출근/등교/업무/귀가) 분석표 | HWP 파일 정상 생성 |
| 4.3 Excel 생성기 | `src/reporter/excel_generator.py` | 다중 시트 (OD요약, 사회경제, 수단분담률), 셀 스타일, 차트 | Excel 다운로드 정상 |
| 4.4 보고서 API | `src/api/routes/report.py` | POST /api/report/generate, GET /api/report/download/{id} | 보고서 생성 → 다운로드 정상 |
| 4.5 Streamlit UI | `src/ui/app.py`, `components/`, `pages/` | FastAPI httpx 연동, 4개 페이지 (업로드/쿼리/대시보드/보고서) | 전체 워크플로우 웹 UI 실행 |
| 4.6 시각화 테스트 | `tests/test_visualizer.py`, `tests/test_api.py` | 차트/보고서 생성 단위+통합 테스트 | 테스트 통과 |

**Phase 4 완료 조건**: 웹 대시보드에서 zip 업로드 → 자연어 쿼리 → 분석 → 보고서 다운로드 전체 동작

---

### Phase 5: 통합 테스트 & 최적화 (0.5주)
**Goal**: E2E 검증, 성능 최적화, 문서화

| Task | 파일 | 작업 | 검증 기준 |
|------|------|------|----------|
| 5.1 E2E 통합 테스트 | `tests/test_e2e.py` | 전체 워크플로우 E2E (zip 업로드→파싱→DB→쿼리→분석→보고서), 30분 이내 | E2E 통과, 전체 30분 이내 |
| 5.2 성능 최적화 | - | EXPLAIN ANALYZE, 파티션 pruning 확인, 인덱스 튜닝, LLM 응답 캐싱 | OD 쿼리 < 5초, 파싱+적재 벤치마크 목표 달성 |
| 5.3 문서화 | `README.md`, `CLAUDE.md` | 설치/실행 방법, 데이터 포맷 설명, zip 업로드 가이드 | 신규 사용자 환경 설정 가능 |

**Phase 5 완료 조건**: pytest 전체 통과 (커버리지 80%+), 전체 30분 이내 처리

---

## 8. 기술 스택 (v3 변경사항)

| 영역 | v2 | v3 변경 |
|------|-----|---------|
| 데이터 소스 | xlsx/xls 파일 | **zip → .OUT/.TXT/.xlsx 3종** |
| 파서 | openpyxl, xlrd | **+ 커스텀 .OUT 파서, .TXT 파서** (CP949) |
| DB 로딩 | ORM bulk insert | **psycopg.copy** (COPY 프로토콜) |
| DB 테이블 | 7개 (단일 스키마) | **9개 + 파티션** (소존/250존 분리) |
| DB 세션 | 단일 | **이중** (read-write + read-only) |
| SQL 검증 | 없음 | **sqlparse** AST 검증 |
| zip 처리 | 없음 | **zipfile + py7zr** (7z 지원) |

### requirements.txt 추가분 (v3)

```
# v3 추가
py7zr>=0.22              # 7z 해제 (일부 KTDB 파일이 .7z)
sqlparse>=0.5            # SQL AST 검증 (Text-to-SQL 방어)
chardet>=5.2             # 인코딩 자동 감지 (CP949 폴백)
```

---

## 9. 에러 처리 & 복구 전략

### 9.1 파일 파싱 에러

| 상황 | 처리 |
|------|------|
| 인코딩 감지 실패 | chardet → CP949 폴백 → UTF-8 폴백 → 에러 |
| .OUT 행 컬럼 수 불일치 | 해당 행 스킵 + 로그 기록, 전체 파싱은 계속 |
| 존코드가 존 마스터에 없음 | 경고 로그 + 적재는 진행 (FK 미사용, 후처리로 매핑) |
| xlsx 시트명 패턴 불일치 | 해당 시트 스킵 + 경고 |

### 9.2 DB 적재 에러

| 상황 | 처리 |
|------|------|
| COPY 중 행 에러 | savepoint 기반: 10만행 배치 단위 커밋, 실패 배치만 롤백 |
| 중복 데이터 | DELETE WHERE (year, region_id, source_file) 후 재적재 |
| 연결 타임아웃 | upload_history.last_success_row 기록, 재시도 시 해당 행부터 |
| 부분 성공 | status = 'partial_success', error_message에 실패 상세 |

### 9.3 Text-to-SQL 에러

| 상황 | 처리 |
|------|------|
| SQL 생성 실패 | 3회 재시도 → 실패 시 사전정의 템플릿 제안 |
| 실행 타임아웃 (>30초) | statement_timeout 설정, 사용자에게 쿼리 단순화 유도 |
| 결과 없음 | "데이터가 없습니다" + 유사 쿼리 제안 |
| 신뢰도 0.7 미만 | 사용자에게 "정확하지 않을 수 있습니다" 경고 표시 |

---

## 10. 커밋 전략

| Phase | 커밋 메시지 패턴 | 예시 |
|-------|-----------------|------|
| 0.5 | `feat(parser): ...` | `feat(parser): add .OUT file parser prototype` |
| 1 | `feat(db): ...` | `feat(db): add partitioned OD tables with 3-tier zone schema` |
| 2 | `feat(collector): ...` | `feat(collector): add zip extractor and format router` |
| 3A | `feat(preprocessor): ...` | `feat(preprocessor): add zone aggregation (subzone → 250)` |
| 3B | `feat(analyzer): ...` | `feat(analyzer): add text-to-sql with read-only enforcement` |
| 4 | `feat(ui): ...` | `feat(ui): add streamlit dashboard with zip upload` |
| 5 | `test: ...` / `docs: ...` | `test: add e2e pipeline test` |

---

## 11. 위험 요소 및 완화 전략 (v3 업데이트)

| 위험 | 영향도 | 발생 가능성 | 완화 전략 |
|------|--------|------------|----------|
| .OUT 파일 포맷 변형 (권역별 차이) | 높음 | 중간 | Phase 0.5에서 전 권역 파싱 검증, file_patterns.yaml 유연 매핑 |
| 소존 OD 데이터 볼륨 (수천만 행) | 높음 | 확실 | COPY 프로토콜 + 파티션 테이블 + 복합 인덱스 |
| 존체계 매핑 불완전 (소존↔250존) | 높음 | 중간 | Phase 0.5에서 매핑 완전성 검증, 누락 시 경고 로그 |
| .TXT 파일 포맷 미확인 (헤더 구조) | 중간 | 높음 | Phase 0.5에서 전수 EDA, 파서 프로토타입 검증 |
| 7z 파일 해제 호환성 | 낮음 | 낮음 | py7zr 라이브러리, 실패 시 수동 해제 안내 |
| Text-to-SQL 정확도 (복잡 스키마) | 높음 | 중간 | 30+ 테스트셋, 신뢰도 점수, 폴백 템플릿 |
| pyhwpx 호환성 (Windows 전용) | 높음 | 중간 | 개발 환경 Windows, python-docx 대안 |
| LLM API 비용 | 중간 | 중간 | GPT-4o-mini 기본, 캐싱 |
| PostgreSQL 설치/운영 | 중간 | 낮음 | Docker Compose |

---

## 12. 성공 지표 (KPI)

| 지표 | 목표 |
|------|------|
| 처리 시간 단축 | 기존 8시간 → 30분 이내 (90% 개선) |
| 데이터 정확도 | 파싱 오류 0건 (실제 데이터 기준) |
| 파싱 성능 | .OUT 1.7M행 < 30초, COPY 적재 < 2분 |
| OD 쿼리 성능 | 단일 쿼리 < 5초 (파티션 pruning) |
| Text-to-SQL 정확도 | 핵심 쿼리 패턴 90%+ |
| 보고서 품질 | 사내 톤앤매너 유지율 90% 이상 |
| 테스트 커버리지 | pytest 전체 통과, 커버리지 80%+ |
| 배포 | `docker-compose up` 전체 환경 기동 |

---

## 13. v2 대비 주요 변경 요약

| 항목 | v2 (기존 가정) | v3 (실제 데이터) |
|------|---------------|-----------------|
| OD 포맷 | xlsx/xls 매트릭스 | **.OUT 텍스트** (주력) + xlsx (250존) |
| 파서 | openpyxl/xlrd only | **.OUT 파서 + .TXT 파서** + openpyxl |
| 존체계 | 단일 체계 | **3-tier**: 소존(7자리) / 250존 / 17존 |
| 사회경제지표 | xlsx | **.TXT 파일** (CP949) |
| 목적 카테고리 | 통근/통학/업무/쇼핑/귀가/기타 | **출근/등교/업무/귀가/기타** (쇼핑 없음) |
| OD 구조 | N×N 매트릭스 → 피벗 필요 | **이미 Long format** (피벗 불필요) |
| 데이터 규모 | 250존 62.5K행 가정 | **소존 1,310존 → 1.7M행/년** |
| 수단 OD | OD 테이블 내 컬럼 | **별도 zip** 파일, 별도 테이블 |
| 화물 분류 | commodity_type + mode | **톤급** (소형/중형/대형) |
| 데이터 소스 | 수동 xlsx 다운로드 | **Zip 아카이브** (표준 폴더 구조) |
| DB 테이블 | 7개 | **9개** (소존/250존 OD 분리 + zones 3개) |
| DB 로딩 | ORM bulk insert | **COPY 프로토콜** (필수) |
| DB 파티션 | 없음 | **연도별 RANGE 파티션** (소존 OD) |
| 테이블 접두사 | 없음 (별도 스키마 가정) | **`ktdb_` 접두사** (public 스키마) |
| Phase 구조 | 0→1→2→3→4→5 | **0(완료)→0.5→1→2→3A→3B→4→5** |

---

## 14. 확인 필요 사항

- [x] KTDB 웹사이트 파일 다운로드 (25건 zip 확보 완료)
- [x] KTDB 파일 포맷 분석 (Phase 0 완료)
- [x] DB 스키마 초기화 (25개 테이블 생성 완료)
- [x] 주요 데이터 적재 완료 (목적별 OD, 250존 OD, 화물, 사회경제지표)
- [ ] ktdb_od_mode_subzone 수도권 로딩 완료 대기 중
- [ ] OpenAI API 키 확보
- [ ] .TXT 파일 상세 헤더 구조 확인 (Phase 0.5에서 수행)
- [ ] 수단별 .OUT 파일 컬럼 구조 확인 (MOD01~MOD?? 범위)
- [ ] 목적별 수단 OD (.OUT) 컬럼 구조 확인 (출근_승용 등 교차 컬럼)
- [ ] 사내 보고서 톤앤매너 예시 문서 수집
- [ ] 한글(HWP) 설치 여부 확인
- [ ] GeoJSON 시군구 경계 데이터 확보
- [ ] 전 권역(01~06) 소존 수 정확한 확인 (수도권 1,310존은 확인됨)

---

## 15. 이 계획의 한계 및 후속 작업

1. **접근수단 OD** (MOD-20~25): 주수단+접근수단 교차 OD는 v3 스코프 외. 필요 시 별도 테이블 추가.
2. **AADT 교통량 데이터**: 참조용으로만 확인됨. DB 스키마 미설계. 필요 시 Phase 2에서 추가.
3. **설명자료 (.hwp/.hwpx)**: 메타데이터 용도로만 활용. 파싱 대상 아님.
4. **다년도 비교 분석**: 2023/2025/2030/.../2050 시계열 분석은 Phase 3A aggregator에서 지원하되, 장기 예측 모델은 스코프 외.
