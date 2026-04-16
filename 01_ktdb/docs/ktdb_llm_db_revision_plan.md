# KTDB 교통 데이터 DB 적재 시스템 — LLM Text-to-SQL 연동 수정 계획서

**작성일**: 2026-03-23
**기반 문서**: `ktdb_raw_data_db_plan.md` (2026-03-20)
**수정 목적**: LLM Text-to-SQL 연동 시 발견된 8가지 문제점 해결 및 end-to-end 5초 KPI 달성을 위한 스키마/뷰/파서 수정
**설계 원칙**: 모델-agnostic (특정 LLM 모델 가정 없음), 기존 적재 시스템과의 하위 호환성 유지

---

## 문제점 요약 및 해결 매핑

| # | 문제 | 해결 영역 | 핵심 변경 |
|---|------|----------|----------|
| 1 | '합계' 파생 행 이중 계산 위험 | 영역 1 (DDL) + 영역 4 (파서) | `is_derived` 컬럼 추가, 뷰에서 자동 제외 |
| 2 | 지명→존번호 매핑 어려움 | 영역 2 (뷰) | `v_zone_lookup` 지명 검색 뷰 |
| 3 | COMMENT ON 완전 부재 | 영역 1 (DDL) | 전 테이블/컬럼 코멘트 추가 |
| 4 | 파티션 전략과 시간 범위 쿼리 비효율 | 영역 1 (DDL) | 전국 OD: RANGE 파티션, 권역 OD: 복합 인덱스 보완 |
| 5 | 집계 레이어 부재 | 영역 2 (뷰) | 17존 Materialized View |
| 6 | 접근수단OD 개념 혼동 | 영역 1 (DDL) + 영역 3 (LLM) | 코멘트 명확화, LLM 미노출 |
| 7 | LLM 전용 통합 뷰 없음 | 영역 2 (뷰) | 지명 JOIN 포함 분석 뷰 레이어 |
| 8 | 수단 카테고리 이름 불일치 | 영역 1 (DDL) + 영역 4 (파서) | `ktdb_mode_mapping` 동의어 테이블 |

---

## 영역 1: DDL 수정 사항

### 1.1 is_derived 컬럼 추가

**문제**: 롱폼 변환 시 purpose='합계', mode='합계'/'승용차택시'/'기타합계' 등 파생 행이 원본 행과 동일 테이블에 저장됨. LLM이 `SUM(trips)` 시 원본+파생이 합산되어 2배 오류 발생.

**Before** (기존 DDL):
```sql
CREATE TABLE public.ktdb_od_purpose_250 (
    id          BIGSERIAL,
    base_year   SMALLINT      NOT NULL,
    o_zone_250  SMALLINT      NOT NULL,
    d_zone_250  SMALLINT      NOT NULL,
    o_zone_17   SMALLINT      NOT NULL,
    d_zone_17   SMALLINT      NOT NULL,
    purpose     VARCHAR(4)    NOT NULL,  -- 출근|등교|업무|귀가|기타|합계
    trips       DOUBLE PRECISION NOT NULL,
    uploaded_at TIMESTAMPTZ   DEFAULT now()
) PARTITION BY LIST (base_year);
```

**After** (수정 DDL):
```sql
CREATE TABLE public.ktdb_od_purpose_250 (
    base_year   SMALLINT         NOT NULL,
    o_zone_250  SMALLINT         NOT NULL,
    d_zone_250  SMALLINT         NOT NULL,
    o_zone_17   SMALLINT         NOT NULL,
    d_zone_17   SMALLINT         NOT NULL,
    purpose     VARCHAR(4)       NOT NULL,
    trips       DOUBLE PRECISION NOT NULL,
    is_derived  BOOLEAN          NOT NULL DEFAULT FALSE,
    uploaded_at TIMESTAMPTZ      DEFAULT now()
) PARTITION BY RANGE (base_year);
```

> `id BIGSERIAL` 제거: 1.47억행 기준 ~1.1GB 스토리지 절약. OD 테이블은 자연키(base_year, o_zone, d_zone, purpose/mode)로 식별 가능.

**is_derived 적용 대상 (전 OD 테이블 공통)**:

| 테이블 | is_derived=TRUE 조건 |
|--------|---------------------|
| `ktdb_od_purpose_250` | `purpose = '합계'` |
| `ktdb_od_mode_250` | `mode = '합계'` |
| `ktdb_od_purpose_region` | `purpose = '합계'` |
| `ktdb_od_mode_region` | `mode IN ('승용차택시', '기타합계')` |
| `ktdb_od_freight_250` | 해당 없음 (와이드폼, truck_total은 컬럼이므로 이중 계산 위험 없음) |

### 1.2 파티션 전략 수정

#### 전국 OD: LIST → RANGE 변경

**Before**: `PARTITION BY LIST (base_year)` -- 7개 파티션 개별 생성

**After**: `PARTITION BY RANGE (base_year)` -- BETWEEN 쿼리 시 연속 파티션만 스캔

**변경 근거**:
- 교통 분석의 핵심 쿼리 패턴은 "2023~2030년 추이" 등 연도 범위 조회
- LIST 파티션에서 `WHERE base_year BETWEEN 2023 AND 2030`은 전 파티션 스캔
- RANGE 파티션은 해당 범위의 파티션만 pruning

```sql
-- 전국 목적별 OD (250존, RANGE 파티션)
CREATE TABLE public.ktdb_od_purpose_250 (
    base_year   SMALLINT         NOT NULL,
    o_zone_250  SMALLINT         NOT NULL,
    d_zone_250  SMALLINT         NOT NULL,
    o_zone_17   SMALLINT         NOT NULL,
    d_zone_17   SMALLINT         NOT NULL,
    purpose     VARCHAR(4)       NOT NULL,
    trips       DOUBLE PRECISION NOT NULL,
    is_derived  BOOLEAN          NOT NULL DEFAULT FALSE,
    uploaded_at TIMESTAMPTZ      DEFAULT now()
) PARTITION BY RANGE (base_year);

-- RANGE 파티션: 각 연도를 1년 범위로 설정
-- FROM (inclusive) TO (exclusive) 구문
CREATE TABLE public.ktdb_od_purpose_250_2023
    PARTITION OF public.ktdb_od_purpose_250
    FOR VALUES FROM (2023) TO (2024);
CREATE TABLE public.ktdb_od_purpose_250_2025
    PARTITION OF public.ktdb_od_purpose_250
    FOR VALUES FROM (2025) TO (2026);
CREATE TABLE public.ktdb_od_purpose_250_2030
    PARTITION OF public.ktdb_od_purpose_250
    FOR VALUES FROM (2030) TO (2031);
CREATE TABLE public.ktdb_od_purpose_250_2035
    PARTITION OF public.ktdb_od_purpose_250
    FOR VALUES FROM (2035) TO (2036);
CREATE TABLE public.ktdb_od_purpose_250_2040
    PARTITION OF public.ktdb_od_purpose_250
    FOR VALUES FROM (2040) TO (2041);
CREATE TABLE public.ktdb_od_purpose_250_2045
    PARTITION OF public.ktdb_od_purpose_250
    FOR VALUES FROM (2045) TO (2046);
CREATE TABLE public.ktdb_od_purpose_250_2050
    PARTITION OF public.ktdb_od_purpose_250
    FOR VALUES FROM (2050) TO (2051);

-- 인덱스 (파티션 상위 테이블에 정의 → 각 파티션에 자동 생성)
CREATE INDEX idx_od_purpose_250_oz      ON public.ktdb_od_purpose_250(o_zone_250);
CREATE INDEX idx_od_purpose_250_purpose ON public.ktdb_od_purpose_250(purpose);
CREATE INDEX idx_od_purpose_250_z17     ON public.ktdb_od_purpose_250(o_zone_17, d_zone_17);
CREATE INDEX idx_od_purpose_250_derived ON public.ktdb_od_purpose_250(is_derived)
    WHERE is_derived = FALSE;

-- 전국 주수단별 OD (250존, RANGE 파티션)
CREATE TABLE public.ktdb_od_mode_250 (
    base_year   SMALLINT         NOT NULL,
    o_zone_250  SMALLINT         NOT NULL,
    d_zone_250  SMALLINT         NOT NULL,
    o_zone_17   SMALLINT         NOT NULL,
    d_zone_17   SMALLINT         NOT NULL,
    mode        VARCHAR(10)      NOT NULL,
    trips       DOUBLE PRECISION NOT NULL,
    is_derived  BOOLEAN          NOT NULL DEFAULT FALSE,
    uploaded_at TIMESTAMPTZ      DEFAULT now()
) PARTITION BY RANGE (base_year);

CREATE TABLE public.ktdb_od_mode_250_2023 PARTITION OF public.ktdb_od_mode_250 FOR VALUES FROM (2023) TO (2024);
CREATE TABLE public.ktdb_od_mode_250_2025 PARTITION OF public.ktdb_od_mode_250 FOR VALUES FROM (2025) TO (2026);
CREATE TABLE public.ktdb_od_mode_250_2030 PARTITION OF public.ktdb_od_mode_250 FOR VALUES FROM (2030) TO (2031);
CREATE TABLE public.ktdb_od_mode_250_2035 PARTITION OF public.ktdb_od_mode_250 FOR VALUES FROM (2035) TO (2036);
CREATE TABLE public.ktdb_od_mode_250_2040 PARTITION OF public.ktdb_od_mode_250 FOR VALUES FROM (2040) TO (2041);
CREATE TABLE public.ktdb_od_mode_250_2045 PARTITION OF public.ktdb_od_mode_250 FOR VALUES FROM (2045) TO (2046);
CREATE TABLE public.ktdb_od_mode_250_2050 PARTITION OF public.ktdb_od_mode_250 FOR VALUES FROM (2050) TO (2051);

CREATE INDEX idx_od_mode_250_oz      ON public.ktdb_od_mode_250(o_zone_250);
CREATE INDEX idx_od_mode_250_mode    ON public.ktdb_od_mode_250(mode);
CREATE INDEX idx_od_mode_250_z17     ON public.ktdb_od_mode_250(o_zone_17, d_zone_17);
CREATE INDEX idx_od_mode_250_derived ON public.ktdb_od_mode_250(is_derived)
    WHERE is_derived = FALSE;

-- 화물 OD (250존, RANGE 파티션)
CREATE TABLE public.ktdb_od_freight_250 (
    base_year    SMALLINT         NOT NULL,
    o_zone_250   SMALLINT         NOT NULL,
    d_zone_250   SMALLINT         NOT NULL,
    o_zone_17    SMALLINT         NOT NULL,
    d_zone_17    SMALLINT         NOT NULL,
    truck_small  DOUBLE PRECISION,
    truck_mid    DOUBLE PRECISION,
    truck_large  DOUBLE PRECISION,
    truck_total  DOUBLE PRECISION,
    uploaded_at  TIMESTAMPTZ      DEFAULT now()
) PARTITION BY RANGE (base_year);

CREATE TABLE public.ktdb_od_freight_250_2023 PARTITION OF public.ktdb_od_freight_250 FOR VALUES FROM (2023) TO (2024);
CREATE TABLE public.ktdb_od_freight_250_2025 PARTITION OF public.ktdb_od_freight_250 FOR VALUES FROM (2025) TO (2026);
CREATE TABLE public.ktdb_od_freight_250_2030 PARTITION OF public.ktdb_od_freight_250 FOR VALUES FROM (2030) TO (2031);
CREATE TABLE public.ktdb_od_freight_250_2035 PARTITION OF public.ktdb_od_freight_250 FOR VALUES FROM (2035) TO (2036);
CREATE TABLE public.ktdb_od_freight_250_2040 PARTITION OF public.ktdb_od_freight_250 FOR VALUES FROM (2040) TO (2041);
CREATE TABLE public.ktdb_od_freight_250_2045 PARTITION OF public.ktdb_od_freight_250 FOR VALUES FROM (2045) TO (2046);
CREATE TABLE public.ktdb_od_freight_250_2050 PARTITION OF public.ktdb_od_freight_250 FOR VALUES FROM (2050) TO (2051);

CREATE INDEX idx_od_freight_oz  ON public.ktdb_od_freight_250(o_zone_250);
CREATE INDEX idx_od_freight_z17 ON public.ktdb_od_freight_250(o_zone_17, d_zone_17);
```

#### 권역별 OD: LIST(region_code) 유지 + 복합 인덱스 보완

**결정 근거**: PostgreSQL은 단일 파티션 키에 대해서만 네이티브 서브파티션을 지원하나, LIST-RANGE 복합 파티션은 파티션 수가 5(권역) x 7(연도) = 35개로 급증하여 관리 복잡도가 과도함. 대신 파티션 내부에 `(base_year)` 복합 인덱스를 추가하여 연도 필터 성능을 확보한다.

**Before**:
```sql
CREATE INDEX idx_od_purpose_region_yr ON public.ktdb_od_purpose_region(base_year);
```

**After**:
```sql
-- 권역별 목적OD (소존, region_code LIST 파티션 -- 기존 유지)
CREATE TABLE public.ktdb_od_purpose_region (
    region_code  SMALLINT         NOT NULL,
    base_year    SMALLINT         NOT NULL,
    o_zone       INTEGER          NOT NULL,
    d_zone       INTEGER          NOT NULL,
    purpose      VARCHAR(6)       NOT NULL,
    trips        DOUBLE PRECISION,
    is_derived   BOOLEAN          NOT NULL DEFAULT FALSE,
    uploaded_at  TIMESTAMPTZ      DEFAULT now()
) PARTITION BY LIST (region_code);

CREATE TABLE public.ktdb_od_purpose_region_12 PARTITION OF public.ktdb_od_purpose_region FOR VALUES IN (12);
CREATE TABLE public.ktdb_od_purpose_region_13 PARTITION OF public.ktdb_od_purpose_region FOR VALUES IN (13);
CREATE TABLE public.ktdb_od_purpose_region_14 PARTITION OF public.ktdb_od_purpose_region FOR VALUES IN (14);
CREATE TABLE public.ktdb_od_purpose_region_15 PARTITION OF public.ktdb_od_purpose_region FOR VALUES IN (15);
CREATE TABLE public.ktdb_od_purpose_region_16 PARTITION OF public.ktdb_od_purpose_region FOR VALUES IN (16);

-- 복합 인덱스: region_code 파티션 pruning + base_year 인덱스 스캔 결합
-- "2023~2030년 부산울산권 출근 OD" → 파티션 12 내에서 base_year 인덱스로 즉시 필터
CREATE INDEX idx_od_purpose_region_yr_purpose
    ON public.ktdb_od_purpose_region(base_year, purpose);
CREATE INDEX idx_od_purpose_region_oz
    ON public.ktdb_od_purpose_region(o_zone);
CREATE INDEX idx_od_purpose_region_derived
    ON public.ktdb_od_purpose_region(is_derived)
    WHERE is_derived = FALSE;

-- 권역별 주수단OD (소존, region_code LIST 파티션 -- 기존 유지)
CREATE TABLE public.ktdb_od_mode_region (
    region_code  SMALLINT         NOT NULL,
    base_year    SMALLINT         NOT NULL,
    o_zone       INTEGER          NOT NULL,
    d_zone       INTEGER          NOT NULL,
    mode         VARCHAR(12)      NOT NULL,
    trips        DOUBLE PRECISION,
    is_derived   BOOLEAN          NOT NULL DEFAULT FALSE,
    uploaded_at  TIMESTAMPTZ      DEFAULT now()
) PARTITION BY LIST (region_code);

CREATE TABLE public.ktdb_od_mode_region_12 PARTITION OF public.ktdb_od_mode_region FOR VALUES IN (12);
CREATE TABLE public.ktdb_od_mode_region_13 PARTITION OF public.ktdb_od_mode_region FOR VALUES IN (13);
CREATE TABLE public.ktdb_od_mode_region_14 PARTITION OF public.ktdb_od_mode_region FOR VALUES IN (14);
CREATE TABLE public.ktdb_od_mode_region_15 PARTITION OF public.ktdb_od_mode_region FOR VALUES IN (15);
CREATE TABLE public.ktdb_od_mode_region_16 PARTITION OF public.ktdb_od_mode_region FOR VALUES IN (16);

CREATE INDEX idx_od_mode_region_yr_mode
    ON public.ktdb_od_mode_region(base_year, mode);
CREATE INDEX idx_od_mode_region_oz
    ON public.ktdb_od_mode_region(o_zone);
CREATE INDEX idx_od_mode_region_derived
    ON public.ktdb_od_mode_region(is_derived)
    WHERE is_derived = FALSE;
```

### 1.3 ktdb_mode_mapping 테이블 추가

**문제**: 전국 OD와 권역별 OD의 수단 카테고리 이름이 불일치.
- 전국: `승용차|버스|지하철|일반철도|고속철도|항공|해운|합계`
- 권역: `도보자전거|승용차|버스|일반고속철도|도시철도|택시|기타|승용차택시|기타합계`

LLM이 "지하철 통행량"을 쿼리할 때 전국은 `mode='지하철'`, 권역은 `mode='도시철도'`로 변환해야 함. 동의어 매핑 테이블로 해결.

```sql
CREATE TABLE IF NOT EXISTS public.ktdb_mode_mapping (
    canonical_name VARCHAR(20) NOT NULL,   -- 표준명 (LLM/사용자 노출용)
    source_name    VARCHAR(30) NOT NULL,   -- 실제 DB 저장값
    source_scope   VARCHAR(20) NOT NULL,   -- 'national_250' | 'region'
    description    VARCHAR(100),           -- 상세 설명
    PRIMARY KEY (source_name, source_scope)
);

COMMENT ON TABLE public.ktdb_mode_mapping IS
    '교통수단 동의어 매핑. 전국(national_250)과 권역(region)에서 동일 수단이 다른 이름으로 저장됨. LLM이 canonical_name으로 검색 후 source_name으로 쿼리 변환.';
COMMENT ON COLUMN public.ktdb_mode_mapping.canonical_name IS '표준 수단명. LLM 프롬프트 및 사용자 인터페이스에 노출되는 이름';
COMMENT ON COLUMN public.ktdb_mode_mapping.source_name IS '실제 OD 테이블의 mode 컬럼에 저장된 값';
COMMENT ON COLUMN public.ktdb_mode_mapping.source_scope IS 'national_250=전국 250존 OD 테이블, region=권역별 소존 OD 테이블';

-- 초기 데이터
INSERT INTO public.ktdb_mode_mapping (canonical_name, source_name, source_scope, description) VALUES
-- 전국 250존 수단
('승용차',     '승용차',      'national_250', '자가용 승용차'),
('버스',       '버스',        'national_250', '시내/시외/고속버스 통합'),
('지하철',     '지하철',      'national_250', '도시철도(지하철) - 전국 OD 기준'),
('일반철도',   '일반철도',    'national_250', '일반열차 (무궁화/새마을/ITX 등)'),
('고속철도',   '고속철도',    'national_250', 'KTX/SRT 등 고속열차'),
('항공',       '항공',        'national_250', '국내선 항공'),
('해운',       '해운',        'national_250', '여객 해운(연안여객선)'),
('합계',       '합계',        'national_250', '전 수단 합계 (파생값)'),
-- 권역별 소존 수단
('도보자전거', '도보자전거',  'region',       '도보 및 자전거'),
('승용차',     '승용차',      'region',       '자가용 승용차'),
('버스',       '버스',        'region',       '시내/시외/고속버스 통합'),
('철도',       '일반고속철도','region',       '일반철도+고속철도 통합 - 권역 OD 기준'),
('지하철',     '도시철도',    'region',       '도시철도(지하철) - 권역 OD 기준'),
('택시',       '택시',        'region',       '택시'),
('기타',       '기타',        'region',       '기타 교통수단'),
('승용차택시', '승용차택시',  'region',       '승용차+택시 합계 (파생값)'),
('기타합계',   '기타합계',    'region',       '기타 수단 합계 (파생값)');
```

### 1.4 COMMENT ON 전면 추가

**문제**: LLM Text-to-SQL은 `information_schema` 또는 `pg_description`에서 테이블/컬럼 코멘트를 컨텍스트로 참조하여 올바른 테이블/컬럼을 선택한다. 코멘트 부재 시 LLM이 잘못된 테이블/컬럼을 선택할 확률이 급증한다.

#### 마스터 테이블 코멘트

```sql
-- ktdb_zones_17
COMMENT ON TABLE public.ktdb_zones_17 IS
    '17존(시도) 마스터 테이블. 전국을 17개 광역시/도 단위로 구분. 모든 OD 데이터의 최상위 공간 단위.';
COMMENT ON COLUMN public.ktdb_zones_17.zone_17 IS '17존 코드 (1~17). 서울=1, 부산=2, ... 제주=17';
COMMENT ON COLUMN public.ktdb_zones_17.sido_name IS '시도명 (예: 서울특별시, 부산광역시)';

-- ktdb_zones_250
COMMENT ON TABLE public.ktdb_zones_250 IS
    '250존(시군구) 마스터 테이블. 전국을 250개 시군구 단위로 구분. 전국 OD 데이터의 기본 공간 단위. zone_17 FK로 시도와 연결.';
COMMENT ON COLUMN public.ktdb_zones_250.zone_250 IS '250존 코드 (1~250). 전국 시군구 단위 존번호';
COMMENT ON COLUMN public.ktdb_zones_250.zone_161 IS '161존 코드 (일부 분석용, nullable)';
COMMENT ON COLUMN public.ktdb_zones_250.zone_17 IS '소속 17존(시도) 코드. FK → ktdb_zones_17';
COMMENT ON COLUMN public.ktdb_zones_250.sido_name IS '시도명';
COMMENT ON COLUMN public.ktdb_zones_250.sigungu_name IS '시군구명 (예: 종로구, 해운대구)';

-- ktdb_zones_region
COMMENT ON TABLE public.ktdb_zones_region IS
    '권역별 소존(읍면동) 마스터 테이블. 5개 권역(부산울산/대구/대전세종충청/광주/제주)의 읍면동 단위 존체계. zone_250으로 전국 250존과 매핑.';
COMMENT ON COLUMN public.ktdb_zones_region.zone_id IS '권역 내 소존 번호 (1부터 시작, 읍면동 단위). 권역 간 번호 중복됨 → region_code와 복합키로 식별';
COMMENT ON COLUMN public.ktdb_zones_region.region_code IS '권역 코드. 12=부산울산, 13=대구광역, 14=대전세종충청, 15=광주광역, 16=제주';
COMMENT ON COLUMN public.ktdb_zones_region.zone_250 IS '매핑되는 전국 250존 번호 (시군구 단위)';
COMMENT ON COLUMN public.ktdb_zones_region.sido IS '시도명';
COMMENT ON COLUMN public.ktdb_zones_region.sigungu IS '시군구명';
COMMENT ON COLUMN public.ktdb_zones_region.dong IS '읍면동명';
COMMENT ON COLUMN public.ktdb_zones_region.is_internal IS '권역 소속 여부. 1=권역내부(해당 권역 시도 소속), 2=권역외부(인접 시도 포함)';
```

#### 전국 OD 테이블 코멘트

```sql
-- ktdb_od_purpose_250
COMMENT ON TABLE public.ktdb_od_purpose_250 IS
    '전국 250존 목적별 여객 OD 통행량. 단위: AAWDT(연평균 평일 일통행량, 통행/일). 7개 기준연도(2023/2025/2030/2035/2040/2045/2050). 롱폼 저장: 각 행이 하나의 (출발존, 도착존, 연도, 목적) 조합.';
COMMENT ON COLUMN public.ktdb_od_purpose_250.base_year IS '기준 연도 (2023=현황, 2025~2050=장래 추정)';
COMMENT ON COLUMN public.ktdb_od_purpose_250.o_zone_250 IS '출발 250존 코드';
COMMENT ON COLUMN public.ktdb_od_purpose_250.d_zone_250 IS '도착 250존 코드';
COMMENT ON COLUMN public.ktdb_od_purpose_250.o_zone_17 IS '출발 17존(시도) 코드';
COMMENT ON COLUMN public.ktdb_od_purpose_250.d_zone_17 IS '도착 17존(시도) 코드';
COMMENT ON COLUMN public.ktdb_od_purpose_250.purpose IS '통행 목적. 출근|등교|업무|귀가|기타 (원본). 합계는 is_derived=TRUE';
COMMENT ON COLUMN public.ktdb_od_purpose_250.trips IS 'AAWDT 통행량 (연평균 평일 일통행량, 통행/일). is_derived=TRUE인 행은 다른 행의 합산값이므로 SUM 집계 시 제외 필요';
COMMENT ON COLUMN public.ktdb_od_purpose_250.is_derived IS 'TRUE=파생 행(합계 등), FALSE=원본 행. SUM 집계 시 is_derived=FALSE만 사용해야 이중 계산 방지';

-- ktdb_od_mode_250
COMMENT ON TABLE public.ktdb_od_mode_250 IS
    '전국 250존 주수단별 여객 OD 통행량. 주수단=최초출발지~최종도착지 기준 주 교통수단(접근구간 제외). 단위: AAWDT(통행/일). 7개 기준연도.';
COMMENT ON COLUMN public.ktdb_od_mode_250.mode IS '주 교통수단. 승용차|버스|지하철|일반철도|고속철도|항공|해운 (원본). 합계는 is_derived=TRUE';
COMMENT ON COLUMN public.ktdb_od_mode_250.trips IS 'AAWDT 통행량. 주수단 기준이므로 동일 통행의 접근수단은 별도(ktdb_od_mode_access_250). 주수단OD 합계 = 목적OD 합계 (동일 모집단)';
COMMENT ON COLUMN public.ktdb_od_mode_250.is_derived IS 'TRUE=파생 행(합계), FALSE=원본 행';

-- ktdb_od_mode_access_250
COMMENT ON TABLE public.ktdb_od_mode_access_250 IS
    '전국 250존 철도역 접근수단 OD. 철도(지하철 포함) 이용 통행에서 철도역까지 접근하는 수단별 통행량. 일반 수단별 OD(ktdb_od_mode_250)와 다름: 주수단이 아닌 접근구간 수단. 2023년 단일.';
COMMENT ON COLUMN public.ktdb_od_mode_access_250.car_taxi IS '승용차/택시로 철도역에 접근한 통행량 (AAWDT)';
COMMENT ON COLUMN public.ktdb_od_mode_access_250.bus IS '버스로 철도역에 접근한 통행량 (AAWDT)';

-- ktdb_od_freight_250
COMMENT ON TABLE public.ktdb_od_freight_250 IS
    '전국 250존 화물자동차 OD 통행량. 톤급별(소형/중형/대형) + 전체. 단위: 대/일(AAWDT). 7개 기준연도.';
COMMENT ON COLUMN public.ktdb_od_freight_250.truck_small IS '소형 화물차 통행량 (1.5톤 미만, 대/일)';
COMMENT ON COLUMN public.ktdb_od_freight_250.truck_mid IS '중형 화물차 통행량 (1.5~5톤, 대/일)';
COMMENT ON COLUMN public.ktdb_od_freight_250.truck_large IS '대형 화물차 통행량 (5톤 이상, 대/일)';
COMMENT ON COLUMN public.ktdb_od_freight_250.truck_total IS '전체 화물차 통행량 (소형+중형+대형, 대/일)';
```

#### 권역별 OD 테이블 코멘트

```sql
-- ktdb_od_purpose_region
COMMENT ON TABLE public.ktdb_od_purpose_region IS
    '권역별 소존(읍면동) 목적별 여객 OD 통행량. 5개 권역(부산울산/대구/대전세종충청/광주/제주). 단위: AAWDT(통행/일). 7개 기준연도. region_code로 파티션.';
COMMENT ON COLUMN public.ktdb_od_purpose_region.region_code IS '권역 코드. 12=부산울산, 13=대구광역, 14=대전세종충청, 15=광주광역, 16=제주';
COMMENT ON COLUMN public.ktdb_od_purpose_region.o_zone IS '출발 소존 번호 (권역 내 읍면동 단위, 1부터). ktdb_zones_region.zone_id와 매핑';
COMMENT ON COLUMN public.ktdb_od_purpose_region.d_zone IS '도착 소존 번호';
COMMENT ON COLUMN public.ktdb_od_purpose_region.purpose IS '통행 목적. 출근|등교|업무|귀가|기타 (원본). 합계는 is_derived=TRUE';
COMMENT ON COLUMN public.ktdb_od_purpose_region.trips IS 'AAWDT 통행량 (통행/일)';
COMMENT ON COLUMN public.ktdb_od_purpose_region.is_derived IS 'TRUE=파생 행(합계), FALSE=원본 행';

-- ktdb_od_mode_region
COMMENT ON TABLE public.ktdb_od_mode_region IS
    '권역별 소존(읍면동) 주수단별 여객 OD 통행량. 수단 카테고리가 전국 250존과 다름 (ktdb_mode_mapping 참조). 단위: AAWDT(통행/일). 7개 기준연도.';
COMMENT ON COLUMN public.ktdb_od_mode_region.mode IS '주 교통수단. 도보자전거|승용차|버스|일반고속철도|도시철도|택시|기타 (원본). 승용차택시/기타합계는 is_derived=TRUE. 전국 OD와 수단명 다름 → ktdb_mode_mapping 참조';
COMMENT ON COLUMN public.ktdb_od_mode_region.is_derived IS 'TRUE=파생 행(승용차택시, 기타합계), FALSE=원본 행';

-- ktdb_od_mode_access_region
COMMENT ON TABLE public.ktdb_od_mode_access_region IS
    '권역별 소존 철도역 접근수단 OD. 철도(지하철 포함) 이용 통행에서 철도역까지 접근하는 수단별 통행량. 읍면동 소존+250존 이중 존체계. 2023년 단일. 일반 수단별 OD(ktdb_od_mode_region)와 다른 개념.';
COMMENT ON COLUMN public.ktdb_od_mode_access_region.o_zone_region IS '출발 소존 번호 (읍면동 단위)';
COMMENT ON COLUMN public.ktdb_od_mode_access_region.d_zone_region IS '도착 소존 번호 (읍면동 단위)';
COMMENT ON COLUMN public.ktdb_od_mode_access_region.o_zone_250 IS '출발 250존 번호 (시군구 매핑)';
COMMENT ON COLUMN public.ktdb_od_mode_access_region.d_zone_250 IS '도착 250존 번호 (시군구 매핑)';
COMMENT ON COLUMN public.ktdb_od_mode_access_region.car IS '승용차로 철도역에 접근한 통행량 (AAWDT)';
COMMENT ON COLUMN public.ktdb_od_mode_access_region.taxi IS '택시로 철도역에 접근한 통행량 (AAWDT)';
COMMENT ON COLUMN public.ktdb_od_mode_access_region.bus IS '버스로 철도역에 접근한 통행량 (AAWDT)';
```

#### 지표/관리 테이블 코멘트

```sql
-- ktdb_socioeconomic
COMMENT ON TABLE public.ktdb_socioeconomic IS
    '전국 250존 사회경제지표. 총인구/학령인구/15세이상인구/취업자수/수용학생수/종사자수. 7개 기준연도. 롱폼 저장.';
COMMENT ON COLUMN public.ktdb_socioeconomic.zone_250 IS '250존 코드. FK → ktdb_zones_250';
COMMENT ON COLUMN public.ktdb_socioeconomic.indicator IS '지표명. 총인구|인구_5_24세|인구_15세이상|취업자수|수용학생수|종사자수';
COMMENT ON COLUMN public.ktdb_socioeconomic.value IS '지표값 (인구수/종사자수 등, 단위: 명)';

-- ktdb_socioeconomic_region
COMMENT ON TABLE public.ktdb_socioeconomic_region IS
    '권역별 소존 사회경제지표. 전국(6종)에 3차산업종사자수 추가(7종). 인구 시트명이 권역별로 다름(5-24세/5-29세).';
COMMENT ON COLUMN public.ktdb_socioeconomic_region.indicator IS '지표명. 총인구|인구_5_24세|인구_5_29세|인구_15세이상|취업자수|종사자수|3차산업종사자수|수용학생수';

-- ktdb_occupancy
COMMENT ON TABLE public.ktdb_occupancy IS
    '재차인원 (승용차/버스). 수도권 승용차 재차인원(시군구별), 지역간 승용차 재차인원(17존), 버스 재차인원(17존). 2023년 기준 단일. 모든 권역 zip에 동일 파일 포함(1회만 적재).';
COMMENT ON COLUMN public.ktdb_occupancy.data_type IS 'metro_car=수도권 승용차, inter_car=지역간 승용차, bus=버스';

-- ktdb_data_catalog
COMMENT ON TABLE public.ktdb_data_catalog IS
    '데이터 파일 적재 이력 관리. 중복 적재 방지(idempotent) 및 적재 상태 추적. LLM에 노출하지 않음.';
```

### 1.5 변경되지 않는 테이블 DDL (확인)

다음 테이블은 기존 DDL을 그대로 유지한다. COMMENT ON만 추가.

| 테이블 | DDL 변경 | COMMENT 추가 |
|--------|---------|-------------|
| `ktdb_zones_17` | 없음 | 추가 |
| `ktdb_zones_250` | 없음 | 추가 |
| `ktdb_zones_region` | 없음 | 추가 |
| `ktdb_od_mode_access_250` | 없음 (와이드폼, 비파티션 유지) | 추가 |
| `ktdb_od_mode_access_region` | 없음 (와이드폼, 비파티션 유지) | 추가 |
| `ktdb_socioeconomic` | 없음 | 추가 |
| `ktdb_socioeconomic_region` | 없음 | 추가 |
| `ktdb_occupancy` | 없음 | 추가 |
| `ktdb_data_catalog` | 없음 | 추가 |

---

## 영역 2: LLM 전용 뷰(View) 레이어 설계

### 2.1 설계 원칙

1. **LLM은 원본 테이블이 아닌 뷰만 대상으로 SQL 생성** -- 이중 계산 방지, 지명 자동 JOIN
2. **is_derived=FALSE 필터 내장** -- 뷰 정의에서 파생 행 자동 제외
3. **지명 컬럼 포함** -- LLM이 `WHERE origin_sido='서울특별시'`로 직접 쿼리 가능
4. **Materialized View로 집계 성능 확보** -- 17존 수준 집계 사전 계산

### 2.2 전국 250존 분석 뷰

```sql
-- 전국 목적OD + 지명 (is_derived=FALSE 필터 내장)
CREATE OR REPLACE VIEW public.v_od_purpose_250 AS
SELECT
    oz.sido_name   AS origin_sido,
    oz.sigungu_name AS origin_sigungu,
    dz.sido_name   AS dest_sido,
    dz.sigungu_name AS dest_sigungu,
    p.base_year,
    p.purpose,
    p.trips,
    p.o_zone_250,
    p.d_zone_250
FROM public.ktdb_od_purpose_250 p
JOIN public.ktdb_zones_250 oz ON p.o_zone_250 = oz.zone_250
JOIN public.ktdb_zones_250 dz ON p.d_zone_250 = dz.zone_250
WHERE p.is_derived = FALSE;

COMMENT ON VIEW public.v_od_purpose_250 IS
    '전국 250존 목적별 OD 분석 뷰. 파생 행(합계) 자동 제외. 지명 JOIN 포함. 단위: AAWDT(통행/일). 목적: 출근/등교/업무/귀가/기타.';

-- 전국 주수단OD + 지명
CREATE OR REPLACE VIEW public.v_od_mode_250 AS
SELECT
    oz.sido_name   AS origin_sido,
    oz.sigungu_name AS origin_sigungu,
    dz.sido_name   AS dest_sido,
    dz.sigungu_name AS dest_sigungu,
    m.base_year,
    m.mode,
    m.trips,
    m.o_zone_250,
    m.d_zone_250
FROM public.ktdb_od_mode_250 m
JOIN public.ktdb_zones_250 oz ON m.o_zone_250 = oz.zone_250
JOIN public.ktdb_zones_250 dz ON m.d_zone_250 = dz.zone_250
WHERE m.is_derived = FALSE;

COMMENT ON VIEW public.v_od_mode_250 IS
    '전국 250존 주수단별 OD 분석 뷰. 파생 행(합계) 자동 제외. 수단: 승용차/버스/지하철/일반철도/고속철도/항공/해운. 권역별과 수단명 다름 → ktdb_mode_mapping 참조.';

-- 전국 화물OD + 지명
CREATE OR REPLACE VIEW public.v_od_freight_250 AS
SELECT
    oz.sido_name   AS origin_sido,
    oz.sigungu_name AS origin_sigungu,
    dz.sido_name   AS dest_sido,
    dz.sigungu_name AS dest_sigungu,
    f.base_year,
    f.truck_small,
    f.truck_mid,
    f.truck_large,
    f.truck_total,
    f.o_zone_250,
    f.d_zone_250
FROM public.ktdb_od_freight_250 f
JOIN public.ktdb_zones_250 oz ON f.o_zone_250 = oz.zone_250
JOIN public.ktdb_zones_250 dz ON f.d_zone_250 = dz.zone_250;

COMMENT ON VIEW public.v_od_freight_250 IS
    '전국 250존 화물자동차 OD 분석 뷰. 톤급별(소형<1.5톤/중형1.5~5톤/대형5톤이상) + 전체. 단위: 대/일(AAWDT).';

-- 전국 사회경제지표 + 지명
CREATE OR REPLACE VIEW public.v_socioeconomic AS
SELECT
    z.sido_name,
    z.sigungu_name,
    s.zone_250,
    s.base_year,
    s.indicator,
    s.value
FROM public.ktdb_socioeconomic s
JOIN public.ktdb_zones_250 z ON s.zone_250 = z.zone_250;

COMMENT ON VIEW public.v_socioeconomic IS
    '전국 250존 사회경제지표 분석 뷰. 지표: 총인구/인구_5_24세/인구_15세이상/취업자수/수용학생수/종사자수. 단위: 명.';
```

### 2.3 17존 집계 Materialized View (성능)

**필요 근거**: "서울에서 부산 출근 통행량"처럼 시도 수준 집계 쿼리가 전형적 분석 패턴. 250존(62,500행/연도) 실시간 집계는 1~2초 가능하나, 권역별 소존(수십만~수백만행)은 불가. 17존 MV로 사전 집계하면 289행(17x17)/연도에서 즉시 응답.

```sql
-- 17존간 목적별 OD 집계 Materialized View
CREATE MATERIALIZED VIEW public.mv_od_purpose_17 AS
SELECT
    oz.sido_name  AS origin_sido,
    dz.sido_name  AS dest_sido,
    p.base_year,
    p.purpose,
    SUM(p.trips)  AS trips
FROM public.ktdb_od_purpose_250 p
JOIN public.ktdb_zones_250 ozn ON p.o_zone_250 = ozn.zone_250
JOIN public.ktdb_zones_17 oz   ON ozn.zone_17 = oz.zone_17
JOIN public.ktdb_zones_250 dzn ON p.d_zone_250 = dzn.zone_250
JOIN public.ktdb_zones_17 dz   ON dzn.zone_17 = dz.zone_17
WHERE p.is_derived = FALSE
GROUP BY oz.sido_name, dz.sido_name, p.base_year, p.purpose;

CREATE INDEX idx_mv_purpose_17_sido ON public.mv_od_purpose_17(origin_sido, dest_sido);
CREATE INDEX idx_mv_purpose_17_year ON public.mv_od_purpose_17(base_year);
CREATE INDEX idx_mv_purpose_17_purpose ON public.mv_od_purpose_17(purpose);

COMMENT ON MATERIALIZED VIEW public.mv_od_purpose_17 IS
    '17존(시도)간 목적별 OD 집계. 250존 OD를 시도 단위로 사전 집계. 17x17x5목적x7연도 = 10,115행. REFRESH 필요 시 REFRESH MATERIALIZED VIEW CONCURRENTLY 실행.';

-- 17존간 주수단별 OD 집계 Materialized View
CREATE MATERIALIZED VIEW public.mv_od_mode_17 AS
SELECT
    oz.sido_name  AS origin_sido,
    dz.sido_name  AS dest_sido,
    m.base_year,
    m.mode,
    SUM(m.trips)  AS trips
FROM public.ktdb_od_mode_250 m
JOIN public.ktdb_zones_250 ozn ON m.o_zone_250 = ozn.zone_250
JOIN public.ktdb_zones_17 oz   ON ozn.zone_17 = oz.zone_17
JOIN public.ktdb_zones_250 dzn ON m.d_zone_250 = dzn.zone_250
JOIN public.ktdb_zones_17 dz   ON dzn.zone_17 = dz.zone_17
WHERE m.is_derived = FALSE
GROUP BY oz.sido_name, dz.sido_name, m.base_year, m.mode;

CREATE INDEX idx_mv_mode_17_sido ON public.mv_od_mode_17(origin_sido, dest_sido);
CREATE INDEX idx_mv_mode_17_year ON public.mv_od_mode_17(base_year);
CREATE INDEX idx_mv_mode_17_mode ON public.mv_od_mode_17(mode);

COMMENT ON MATERIALIZED VIEW public.mv_od_mode_17 IS
    '17존(시도)간 주수단별 OD 집계. 17x17x7수단x7연도 = 14,161행. 수단분담률 계산에 최적.';

-- 17존간 화물 OD 집계
CREATE MATERIALIZED VIEW public.mv_od_freight_17 AS
SELECT
    oz.sido_name  AS origin_sido,
    dz.sido_name  AS dest_sido,
    f.base_year,
    SUM(f.truck_small)  AS truck_small,
    SUM(f.truck_mid)    AS truck_mid,
    SUM(f.truck_large)  AS truck_large,
    SUM(f.truck_total)  AS truck_total
FROM public.ktdb_od_freight_250 f
JOIN public.ktdb_zones_250 ozn ON f.o_zone_250 = ozn.zone_250
JOIN public.ktdb_zones_17 oz   ON ozn.zone_17 = oz.zone_17
JOIN public.ktdb_zones_250 dzn ON f.d_zone_250 = dzn.zone_250
JOIN public.ktdb_zones_17 dz   ON dzn.zone_17 = dz.zone_17
GROUP BY oz.sido_name, dz.sido_name, f.base_year;

CREATE INDEX idx_mv_freight_17_sido ON public.mv_od_freight_17(origin_sido, dest_sido);
CREATE INDEX idx_mv_freight_17_year ON public.mv_od_freight_17(base_year);

COMMENT ON MATERIALIZED VIEW public.mv_od_freight_17 IS
    '17존(시도)간 화물 OD 집계. 톤급별 + 전체. 17x17x7연도 = 2,023행.';
```

### 2.4 권역별 분석 뷰

```sql
-- 권역별 목적OD + 지명 (소존-읍면동)
CREATE OR REPLACE VIEW public.v_od_purpose_region AS
SELECT
    zr.sido        AS origin_sido,
    zr.sigungu     AS origin_sigungu,
    zr.dong        AS origin_dong,
    dr.sido        AS dest_sido,
    dr.sigungu     AS dest_sigungu,
    dr.dong        AS dest_dong,
    p.region_code,
    p.base_year,
    p.purpose,
    p.trips,
    p.o_zone       AS origin_zone_id,
    p.d_zone       AS dest_zone_id
FROM public.ktdb_od_purpose_region p
JOIN public.ktdb_zones_region zr ON p.o_zone = zr.zone_id AND p.region_code = zr.region_code
JOIN public.ktdb_zones_region dr ON p.d_zone = dr.zone_id AND p.region_code = dr.region_code
WHERE p.is_derived = FALSE;

COMMENT ON VIEW public.v_od_purpose_region IS
    '권역별 소존(읍면동) 목적별 OD 분석 뷰. 파생 행(합계) 자동 제외. 지명 JOIN 포함. 주의: 대용량(수천만행) → 반드시 WHERE region_code= 조건 포함 권장.';

-- 권역별 주수단OD + 지명
CREATE OR REPLACE VIEW public.v_od_mode_region AS
SELECT
    zr.sido        AS origin_sido,
    zr.sigungu     AS origin_sigungu,
    zr.dong        AS origin_dong,
    dr.sido        AS dest_sido,
    dr.sigungu     AS dest_sigungu,
    dr.dong        AS dest_dong,
    m.region_code,
    m.base_year,
    m.mode,
    m.trips,
    m.o_zone       AS origin_zone_id,
    m.d_zone       AS dest_zone_id
FROM public.ktdb_od_mode_region m
JOIN public.ktdb_zones_region zr ON m.o_zone = zr.zone_id AND m.region_code = zr.region_code
JOIN public.ktdb_zones_region dr ON m.d_zone = dr.zone_id AND m.region_code = dr.region_code
WHERE m.is_derived = FALSE;

COMMENT ON VIEW public.v_od_mode_region IS
    '권역별 소존(읍면동) 주수단별 OD 분석 뷰. 파생 행(승용차택시, 기타합계) 자동 제외. 수단명이 전국 OD와 다름 → ktdb_mode_mapping 참조.';

-- 권역별 사회경제지표 + 지명
CREATE OR REPLACE VIEW public.v_socioeconomic_region AS
SELECT
    zr.sido,
    zr.sigungu,
    zr.dong,
    s.region_code,
    s.zone_id,
    s.base_year,
    s.indicator,
    s.value
FROM public.ktdb_socioeconomic_region s
JOIN public.ktdb_zones_region zr ON s.zone_id = zr.zone_id AND s.region_code = zr.region_code;

COMMENT ON VIEW public.v_socioeconomic_region IS
    '권역별 소존 사회경제지표 분석 뷰. 전국(6종)과 다른 지표 구성: 3차산업종사자수 추가(7종). 인구 시트명 권역별 차이(인구_5_24세/인구_5_29세).';
```

### 2.5 지명 검색 뷰

**문제 해결**: LLM이 "해운대구" 등 지명으로 존번호를 찾을 수 있도록 통합 검색 뷰 제공.

```sql
CREATE OR REPLACE VIEW public.v_zone_lookup AS
SELECT
    'national_250' AS zone_system,
    zone_250       AS zone_code,
    NULL::SMALLINT AS region_code,
    zone_17,
    sido_name,
    sigungu_name,
    NULL::VARCHAR  AS dong
FROM public.ktdb_zones_250

UNION ALL

SELECT
    'region'       AS zone_system,
    zone_id        AS zone_code,
    region_code,
    NULL::SMALLINT AS zone_17,
    sido,
    sigungu,
    dong
FROM public.ktdb_zones_region;

COMMENT ON VIEW public.v_zone_lookup IS
    '통합 존 검색 뷰. 전국 250존(시군구)과 권역별 소존(읍면동)을 하나의 뷰로 통합. LLM이 지명으로 존번호를 검색할 때 사용. zone_system으로 전국/권역 구분.';
```

### 2.6 LLM 노출 대상 확정

| 뷰/테이블 | LLM 노출 | 용도 | 예상 크기 |
|----------|---------|------|----------|
| `v_od_purpose_250` | O | 전국 목적OD 분석 | ~2.2M행 (합계 제외) |
| `v_od_mode_250` | O | 전국 수단OD 분석 | ~3.1M행 (합계 제외) |
| `v_od_freight_250` | O | 전국 화물OD 분석 | 437,500행 |
| `v_socioeconomic` | O | 전국 사회경제지표 | 10,500행 |
| `mv_od_purpose_17` | O | 시도간 목적OD (고속) | ~10,115행 |
| `mv_od_mode_17` | O | 시도간 수단OD (고속) | ~14,161행 |
| `mv_od_freight_17` | O | 시도간 화물OD (고속) | ~2,023행 |
| `v_od_purpose_region` | O | 권역별 목적OD 분석 | ~46.4M행 |
| `v_od_mode_region` | O | 권역별 수단OD 분석 | ~64.8M행 |
| `v_socioeconomic_region` | O | 권역별 사회경제지표 | ~122,500행 |
| `v_zone_lookup` | O | 지명→존번호 검색 | ~2,750행 |
| `ktdb_mode_mapping` | O | 수단명 동의어 | ~17행 |
| `ktdb_zones_17` | O | 17존 시도 목록 | 17행 |
| --- | --- | --- | --- |
| `ktdb_od_mode_access_250` | **X** | 접근수단 (혼동 위험) | - |
| `ktdb_od_mode_access_region` | **X** | 접근수단 (혼동 위험) | - |
| `ktdb_occupancy` | **X** | 재차인원 (특수 분석) | - |
| `ktdb_data_catalog` | **X** | 관리용 | - |
| 원본 파티션 테이블들 | **X** | 뷰를 통해서만 접근 | - |

**접근수단OD 미노출 근거**: 일반 수단OD와 개념이 다르지만(주수단 vs 접근수단) 이름이 유사하여 LLM 혼동 위험이 높음. 접근수단OD가 필요한 전문 쿼리는 관리자가 직접 SQL 작성.

---

## 영역 3: LLM 연동 설계

### 3.1 Text-to-SQL 방식 선택 근거

| 방식 | 적합성 | 이유 |
|------|--------|------|
| **LangChain SQL Agent (tool-calling)** | **채택** | 수치 집계에 SQL이 정확, 구조화 데이터 최적, 다단계 쿼리(지명 검색→OD 조회) 가능 |
| RAG (벡터 검색) | 부적합 | OD 데이터는 정형 수치 → 벡터 유사도 검색 무의미 |
| 직접 pandas 분석 | 부적합 | 1.47억행 메모리 로드 불가, DB 파티션/인덱스 활용 불가 |

### 3.2 스키마 컨텍스트 전달 전략

LLM에게 DB 스키마 정보를 전달하는 방법. COMMENT ON이 핵심.

```python
# 스키마 컨텍스트 추출 쿼리 (LLM에 전달할 DDL + COMMENT 자동 생성)
SCHEMA_CONTEXT_QUERY = """
SELECT
    'VIEW' AS object_type,
    c.relname AS object_name,
    obj_description(c.oid) AS table_comment,
    a.attname AS column_name,
    pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
    col_description(c.oid, a.attnum) AS column_comment
FROM pg_class c
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
WHERE c.relname IN (
    -- LLM 노출 대상 뷰/테이블 목록
    'v_od_purpose_250', 'v_od_mode_250', 'v_od_freight_250', 'v_socioeconomic',
    'mv_od_purpose_17', 'mv_od_mode_17', 'mv_od_freight_17',
    'v_od_purpose_region', 'v_od_mode_region', 'v_socioeconomic_region',
    'v_zone_lookup', 'ktdb_mode_mapping', 'ktdb_zones_17'
)
ORDER BY c.relname, a.attnum;
"""
```

**토큰 예산 추정** (노출 뷰 13개 기준):

| 항목 | 예상 토큰 |
|------|----------|
| DDL (CREATE VIEW/TABLE 구문) | ~1,500 |
| COMMENT ON (테이블 + 컬럼) | ~2,000 |
| Few-shot 예시 5종 | ~1,500 |
| 시스템 프롬프트 | ~500 |
| **합계** | **~5,500** |

> 대부분의 LLM 모델은 8K+ 컨텍스트 윈도우를 지원하므로 5,500 토큰은 충분히 수용 가능. 모델 확정 시 토큰 최적화 전략: (1) 불필요한 뷰 제외, (2) 코멘트 축약, (3) 자주 쓰이는 뷰만 포함 후 필요 시 동적 추가.

### 3.3 공간 단위 자동 인식 전략

사용자 입력에서 공간 단위를 인식하고 적절한 뷰/MV를 선택하는 로직.

```
입력: "2023년 서울→부산 출근 통행량"
  └── 시도 수준 → mv_od_purpose_17 (즉시 응답)

입력: "2023년 종로구→해운대구 출근 통행량"
  └── 시군구 수준 → v_od_purpose_250 (250존 뷰)

입력: "2023년 부산울산권 청운효자동→해운대동 출근 통행량"
  └── 읍면동 수준 → v_od_purpose_region (권역 소존 뷰)
```

**LLM 2-step 패턴**: 지명이 포함된 쿼리에서 LLM은 다음 순서로 SQL 생성.

1. **Step 1**: `v_zone_lookup`에서 지명 검색하여 존번호/zone_system 확인
2. **Step 2**: 확인된 zone_system에 맞는 뷰에서 OD 데이터 조회

```sql
-- Step 1 예시: "해운대구"가 어떤 존체계에 속하는지 확인
SELECT zone_system, zone_code, region_code, sido_name, sigungu_name
FROM v_zone_lookup
WHERE sigungu_name LIKE '%해운대%';
-- 결과: zone_system='national_250', zone_code=34, sido_name='부산광역시', sigungu_name='해운대구'

-- Step 2 예시: 확인된 존번호로 OD 쿼리
SELECT origin_sigungu, dest_sigungu, purpose, trips
FROM v_od_purpose_250
WHERE origin_sigungu = '해운대구' AND base_year = 2023;
```

### 3.4 Few-shot 예시 쿼리 (5종)

LLM 시스템 프롬프트에 포함할 전형적 교통 분석 쿼리 패턴.

#### (1) 단일 시도간 OD

```
[질문] 2023년 서울에서 부산으로 출근 통행량은?

[SQL]
SELECT origin_sido, dest_sido, base_year, purpose, trips
FROM mv_od_purpose_17
WHERE origin_sido = '서울특별시'
  AND dest_sido = '부산광역시'
  AND base_year = 2023
  AND purpose = '출근';

[응답 형식]
| 출발 | 도착 | 연도 | 목적 | 통행량(통행/일) |
|------|------|------|------|---------------|
| 서울특별시 | 부산광역시 | 2023 | 출근 | 12,345 |

2023년 기준 서울에서 부산으로의 출근 통행량은 일평균 12,345통행입니다.
이는 AAWDT(연평균 평일 일통행량) 기준으로, 주말/공휴일은 제외된 수치입니다.
```

#### (2) 연도 추이

```
[질문] 부산울산권 2023~2050 승용차 통행 추이를 보여줘

[SQL]
SELECT base_year, SUM(trips) AS total_trips
FROM v_od_mode_region
WHERE region_code = 12
  AND mode = '승용차'
GROUP BY base_year
ORDER BY base_year;

[응답 형식]
| 연도 | 승용차 통행량(통행/일) |
|------|---------------------|
| 2023 | 1,234,567 |
| 2025 | 1,245,678 |
| ... | ... |

부산울산권의 승용차 통행량은 2023년 1,234,567통행/일에서 2050년 X통행/일로
약 Y% 증가(또는 감소)할 것으로 전망됩니다.
```

#### (3) 권역 내부 분석

```
[질문] 대구광역권 2023년 내부 출근 OD TOP 10

[SQL]
SELECT origin_dong, dest_dong, trips
FROM v_od_purpose_region
WHERE region_code = 13
  AND base_year = 2023
  AND purpose = '출근'
ORDER BY trips DESC
LIMIT 10;
```

#### (4) 전국 수단분담률

```
[질문] 2023년 전국 수단분담률은?

[SQL]
SELECT
    mode,
    SUM(trips) AS total_trips,
    ROUND(SUM(trips) * 100.0 / SUM(SUM(trips)) OVER (), 1) AS share_pct
FROM v_od_mode_250
WHERE base_year = 2023
GROUP BY mode
ORDER BY total_trips DESC;

[응답 형식]
| 수단 | 통행량(통행/일) | 분담률(%) |
|------|---------------|----------|
| 승용차 | 65,432,100 | 64.8 |
| 버스 | 20,123,456 | 19.9 |
| ... | ... | ... |
```

#### (5) 비교 분석

```
[질문] 2023 vs 2030 서울 수도권 출근 통행량 변화는?

[SQL]
SELECT
    base_year,
    origin_sido,
    dest_sido,
    SUM(trips) AS trips
FROM mv_od_purpose_17
WHERE purpose = '출근'
  AND base_year IN (2023, 2030)
  AND origin_sido IN ('서울특별시', '인천광역시', '경기도')
  AND dest_sido IN ('서울특별시', '인천광역시', '경기도')
GROUP BY base_year, origin_sido, dest_sido
ORDER BY base_year, trips DESC;
```

### 3.5 LLM 응답 파이프라인

```
자연어 입력
    |
    v
[1. 의도 분류 + 엔티티 추출]
    - 공간 엔티티: 지명(서울, 해운대구, 청운효자동)
    - 시간 엔티티: 연도(2023, 2023~2030)
    - 분석 유형: 수단/목적/화물
    - 집계 수준: 시도/시군구/읍면동
    |
    v
[2. 뷰 선택]
    - 시도 수준 → mv_od_purpose_17 / mv_od_mode_17
    - 시군구 수준 → v_od_purpose_250 / v_od_mode_250
    - 읍면동 수준 → v_od_purpose_region / v_od_mode_region
    - 수단명 변환 필요 시 → ktdb_mode_mapping 참조
    |
    v
[3. SQL 생성] (LLM, tool-calling)
    - 노출 뷰 대상으로만 SQL 생성
    - is_derived=FALSE 필터는 뷰에 내장 → LLM이 신경 쓸 필요 없음
    |
    v
[4. SQL 검증]
    - 읽기 전용 확인 (SELECT만 허용)
    - 대상 테이블/뷰가 노출 목록에 포함되는지 확인
    - LIMIT 없는 대용량 쿼리에 자동 LIMIT 추가
    |
    v
[5. DB 실행] (read-only 세션, prepare_threshold=None)
    |
    v
[6. 결과 처리]
    - A: 표 포맷팅 (pandas → markdown table)
    - B: 해석 텍스트 생성 (LLM 호출)
    |
    v
[7. 통합 응답 반환]
    - 숫자/표(A) + 해석 텍스트(B) 조합
```

### 3.6 Read-Only Role 설정

```sql
-- LLM 전용 읽기 역할 생성
CREATE ROLE ktdb_reader WITH LOGIN PASSWORD '...' NOSUPERUSER NOCREATEDB NOCREATEROLE;

-- 노출 뷰에만 SELECT 권한 부여
GRANT SELECT ON
    public.v_od_purpose_250,
    public.v_od_mode_250,
    public.v_od_freight_250,
    public.v_socioeconomic,
    public.mv_od_purpose_17,
    public.mv_od_mode_17,
    public.mv_od_freight_17,
    public.v_od_purpose_region,
    public.v_od_mode_region,
    public.v_socioeconomic_region,
    public.v_zone_lookup,
    public.ktdb_mode_mapping,
    public.ktdb_zones_17
TO ktdb_reader;

-- 원본 테이블, 관리 테이블, 접근수단OD 테이블에는 권한 없음
-- → LLM이 이 테이블들을 대상으로 SQL 생성해도 실행 실패 → 안전 장치
```

---

## 영역 4: 파서/적재 수정 사항

### 4.1 is_derived 값 자동 세팅 규칙

각 파서에서 DataFrame 생성 후, COPY 적재 전에 `is_derived` 컬럼을 자동 세팅한다.

```python
# src/collector/derived_marker.py

# 파생 행 판별 규칙
DERIVED_RULES = {
    'purpose': {
        'national_250': lambda val: val == '합계',
        'region':       lambda val: val == '합계',
    },
    'mode': {
        'national_250': lambda val: val == '합계',
        'region':       lambda val: val in ('승용차택시', '기타합계'),
    },
}

def mark_derived(df: pd.DataFrame, category_col: str, scope: str) -> pd.DataFrame:
    """
    DataFrame에 is_derived 컬럼 추가.

    Args:
        df: 롱폼 변환 완료된 DataFrame
        category_col: 'purpose' 또는 'mode'
        scope: 'national_250' 또는 'region'
    Returns:
        is_derived 컬럼이 추가된 DataFrame
    """
    rule = DERIVED_RULES[category_col][scope]
    df['is_derived'] = df[category_col].apply(rule)
    return df
```

**적용 위치** (기존 파서별):

| 파서 | 적용 코드 |
|------|----------|
| `od_purpose_250_parser.py` | `df = mark_derived(df, 'purpose', 'national_250')` |
| `od_mode_250_parser.py` | `df = mark_derived(df, 'mode', 'national_250')` |
| `od_purpose_region_parser.py` | `df = mark_derived(df, 'purpose', 'region')` |
| `od_mode_region_parser.py` | `df = mark_derived(df, 'mode', 'region')` |
| `od_freight_250_parser.py` | 해당 없음 (와이드폼, is_derived 불필요) |

**db_columns 수정** (COPY 컬럼 목록에 is_derived 추가):

```python
# Before
db_columns = ['base_year', 'o_zone_250', 'd_zone_250', 'o_zone_17', 'd_zone_17', 'purpose', 'trips']

# After
db_columns = ['base_year', 'o_zone_250', 'd_zone_250', 'o_zone_17', 'd_zone_17', 'purpose', 'trips', 'is_derived']
```

### 4.2 ktdb_mode_mapping 적재

`bulk_loader.py`의 Phase 1(DB 인프라 구축) 단계에서 DDL 실행 직후 INSERT.

```python
# src/collector/mode_mapping_loader.py

MODE_MAPPING_DATA = [
    # (canonical_name, source_name, source_scope, description)
    ('승용차',     '승용차',      'national_250', '자가용 승용차'),
    ('버스',       '버스',        'national_250', '시내/시외/고속버스 통합'),
    ('지하철',     '지하철',      'national_250', '도시철도(지하철) - 전국 OD 기준'),
    ('일반철도',   '일반철도',    'national_250', '일반열차'),
    ('고속철도',   '고속철도',    'national_250', 'KTX/SRT 등 고속열차'),
    ('항공',       '항공',        'national_250', '국내선 항공'),
    ('해운',       '해운',        'national_250', '여객 해운'),
    ('합계',       '합계',        'national_250', '전 수단 합계 (파생값)'),
    ('도보자전거', '도보자전거',  'region',       '도보 및 자전거'),
    ('승용차',     '승용차',      'region',       '자가용 승용차'),
    ('버스',       '버스',        'region',       '시내/시외/고속버스 통합'),
    ('철도',       '일반고속철도','region',       '일반철도+고속철도 통합'),
    ('지하철',     '도시철도',    'region',       '도시철도(지하철) - 권역 OD 기준'),
    ('택시',       '택시',        'region',       '택시'),
    ('기타',       '기타',        'region',       '기타 교통수단'),
    ('승용차택시', '승용차택시',  'region',       '승용차+택시 합계 (파생값)'),
    ('기타합계',   '기타합계',    'region',       '기타 수단 합계 (파생값)'),
]

def load_mode_mapping(conninfo: str):
    """ktdb_mode_mapping 초기 데이터 적재. idempotent (ON CONFLICT DO NOTHING)."""
    with psycopg.connect(conninfo, prepare_threshold=None) as conn:
        with conn.cursor() as cur:
            for canonical, source, scope, desc in MODE_MAPPING_DATA:
                cur.execute(
                    """INSERT INTO ktdb_mode_mapping (canonical_name, source_name, source_scope, description)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (source_name, source_scope) DO NOTHING""",
                    (canonical, source, scope, desc)
                )
        conn.commit()
```

### 4.3 구현 단계 수정 (기존 Phase에 추가)

**Before** (기존 Phase 1):
> 1. `zip_utils.py` 구현
> 2. 전체 테이블 DDL 실행
> 3. 존체계 적재
> 4. FK 정합성 검증

**After** (수정 Phase 1):
> 1. `zip_utils.py` 구현
> 2. 전체 테이블 DDL 실행 (**RANGE 파티션 + is_derived 컬럼 포함**)
> 3. **COMMENT ON 전면 실행**
> 4. **ktdb_mode_mapping 초기 데이터 적재**
> 5. 존체계 적재
> 6. FK 정합성 검증
> 7. **뷰/MV 생성 (DDL 실행)**

**신규 Phase 추가** (기존 Phase 6 이후):

> ### Phase 7: LLM 연동 준비 (0.5일)
> 1. Materialized View 초기 REFRESH 실행
> 2. Read-Only Role 생성 및 권한 부여
> 3. 스키마 컨텍스트 추출 쿼리 실행 → 프롬프트 템플릿 생성
> 4. Few-shot 예시 5종 검증 (기준값 대조)
> 5. end-to-end 5초 KPI 벤치마크

---

## 영역 5: 검증 기준 업데이트

### 5.1 이중 계산 방지 검증 쿼리

```sql
-- 검증 1: 뷰의 SUM(trips)와 원본 합계 행 비교 (목적OD)
-- 뷰는 is_derived=FALSE만 포함 → SUM이 원본 합계와 일치해야 함
WITH view_sum AS (
    SELECT base_year, SUM(trips) AS calc_total
    FROM v_od_purpose_250
    GROUP BY base_year
),
raw_sum AS (
    SELECT base_year, SUM(trips) AS stored_total
    FROM ktdb_od_purpose_250
    WHERE purpose = '합계' AND is_derived = TRUE
    GROUP BY base_year
)
SELECT
    v.base_year,
    v.calc_total,
    r.stored_total,
    ABS(v.calc_total - r.stored_total) / NULLIF(r.stored_total, 0) AS diff_ratio
FROM view_sum v
JOIN raw_sum r ON v.base_year = r.base_year
ORDER BY v.base_year;
-- 모든 연도에서 diff_ratio < 0.001 (0.1% 미만)

-- 검증 2: 2023년 전국 합계 기준값 확인
SELECT SUM(trips) AS total_2023
FROM v_od_purpose_250
WHERE base_year = 2023;
-- 기대값: 100,910,608 (AAWDT 기준)

-- 검증 3: 주수단OD ↔ 목적OD 합계 교차검증 (뷰 기준)
SELECT
    ABS(m.s - p.s) / p.s AS diff_ratio
FROM
    (SELECT SUM(trips) s FROM v_od_mode_250 WHERE base_year = 2023) m,
    (SELECT SUM(trips) s FROM v_od_purpose_250 WHERE base_year = 2023) p;
-- diff_ratio < 0.0001
```

### 5.2 Materialized View 갱신 전략

```sql
-- 데이터 적재 완료 후 MV 갱신
-- CONCURRENTLY 옵션: MV에 UNIQUE INDEX 필요 → 별도 생성
CREATE UNIQUE INDEX idx_mv_purpose_17_uniq
    ON public.mv_od_purpose_17(origin_sido, dest_sido, base_year, purpose);
CREATE UNIQUE INDEX idx_mv_mode_17_uniq
    ON public.mv_od_mode_17(origin_sido, dest_sido, base_year, mode);
CREATE UNIQUE INDEX idx_mv_freight_17_uniq
    ON public.mv_od_freight_17(origin_sido, dest_sido, base_year);

-- 갱신 실행 (서비스 중단 없이)
REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_od_purpose_17;
REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_od_mode_17;
REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_od_freight_17;
```

**갱신 시점 판단 기준**:
```sql
-- ktdb_data_catalog의 최신 loaded_at vs MV 마지막 갱신 시점 비교
SELECT
    schemaname, matviewname,
    (SELECT MAX(loaded_at) FROM ktdb_data_catalog WHERE status = 'loaded') AS last_load,
    -- pg_stat_user_tables에서 MV 마지막 vacuum/analyze 시점 확인
    last_analyze
FROM pg_stat_user_tables
WHERE relname IN ('mv_od_purpose_17', 'mv_od_mode_17', 'mv_od_freight_17');
```

### 5.3 LLM 쿼리 정확도 검증 방법

정답이 알려진 5종 쿼리로 회귀 테스트 자동화.

```python
# tests/test_llm_query_accuracy.py

REGRESSION_QUERIES = [
    {
        'question': '2023년 전국 여객 OD 총 통행량',
        'sql': "SELECT SUM(trips) FROM v_od_purpose_250 WHERE base_year = 2023",
        'expected_value': 100_910_608,
        'tolerance': 0.001,  # 0.1% 허용 오차
    },
    {
        'question': '2023년 부산울산권 목적OD 행수 (원본만)',
        'sql': """SELECT COUNT(*)
                  FROM v_od_purpose_region
                  WHERE region_code = 12 AND base_year = 2023""",
        'expected_value': 401_956 * 5,  # 634^2 x 5목적(합계 제외)
        'tolerance': 0.0,
    },
    {
        'question': '17존 MV 행수 확인',
        'sql': "SELECT COUNT(*) FROM mv_od_purpose_17",
        'expected_value': 17 * 17 * 5 * 7,  # 17x17x5목적x7연도 = 10,115
        'tolerance': 0.01,
    },
    {
        'question': '주수단OD = 목적OD 합계 교차검증',
        'sql': """SELECT ABS(
                    (SELECT SUM(trips) FROM v_od_mode_250 WHERE base_year = 2023) -
                    (SELECT SUM(trips) FROM v_od_purpose_250 WHERE base_year = 2023)
                  ) / (SELECT SUM(trips) FROM v_od_purpose_250 WHERE base_year = 2023)""",
        'expected_value': 0.0,
        'tolerance': 0.0001,
    },
    {
        'question': '수단 매핑 테이블 무결성',
        'sql': """SELECT COUNT(DISTINCT source_name)
                  FROM ktdb_mode_mapping
                  WHERE source_scope = 'region'
                    AND source_name NOT IN (
                        SELECT DISTINCT mode FROM ktdb_od_mode_region
                    )""",
        'expected_value': 0,
        'tolerance': 0.0,
    },
]
```

### 5.4 성능 KPI 재설정

**end-to-end 5초 이내** 분해:

| 단계 | 목표 시간 | 달성 전략 |
|------|----------|----------|
| LLM SQL 생성 | 2~3초 | 모델 미정, 예비 할당 |
| DB 쿼리 실행 | **1~2초 이내** | MV(17존): <0.1초, 뷰(250존): <1초, 뷰(소존): <2초 |
| 결과 포맷팅 | 0.3초 | pandas → markdown |
| 해석 텍스트 생성 | 0~1초 | 선택적 LLM 호출 (짧은 결과는 즉시 해석) |

**벤치마크 쿼리** (적재 후 실행):

```sql
-- MV 쿼리 성능 (목표: <0.1초)
EXPLAIN ANALYZE
SELECT origin_sido, dest_sido, trips
FROM mv_od_purpose_17
WHERE base_year = 2023 AND purpose = '출근'
ORDER BY trips DESC LIMIT 10;

-- 250존 뷰 쿼리 성능 (목표: <1초)
EXPLAIN ANALYZE
SELECT origin_sido, origin_sigungu, dest_sido, dest_sigungu, SUM(trips) AS trips
FROM v_od_purpose_250
WHERE base_year = 2023 AND purpose = '출근'
  AND origin_sido = '서울특별시'
GROUP BY 1, 2, 3, 4
ORDER BY trips DESC LIMIT 10;

-- 권역별 소존 뷰 쿼리 성능 (목표: <2초)
EXPLAIN ANALYZE
SELECT origin_dong, dest_dong, trips
FROM v_od_purpose_region
WHERE region_code = 12 AND base_year = 2023 AND purpose = '출근'
ORDER BY trips DESC LIMIT 10;

-- RANGE 파티션 pruning 확인 (전국 OD)
EXPLAIN ANALYZE
SELECT base_year, SUM(trips)
FROM v_od_purpose_250
WHERE base_year BETWEEN 2023 AND 2030
GROUP BY base_year;
-- 확인: 2023/2025/2030 3개 파티션만 스캔되는지
```

### 5.5 완료 기준 (Definition of Done) 업데이트

**Before** (기존 9개):
```
- [ ] 전체 테이블 및 파티션 생성 확인
- [ ] 전국 250존 각 테이블 행수 검증 통과
- [ ] 목적OD 2023년 합계 SUM = 100,910,608 확인
- [ ] 주수단OD ↔ 목적OD 합계 오차 < 0.01%
- [ ] 권역별 OD 연도별 행수 검증
- [ ] ktdb_data_catalog 전체 파일 status='loaded' 확인
- [ ] bulk_loader.py --dry-run → 스킵 확인
- [ ] 시도간 집계 쿼리 < 5초
- [ ] pytest 파서 단위 테스트 통과
```

**After** (15개 -- 추가 6개):
```
- [ ] 전체 테이블 및 파티션 생성 확인 (RANGE 파티션 포함)
- [ ] 전국 250존 각 테이블 행수 검증 통과
- [ ] 목적OD 2023년 합계 SUM = 100,910,608 확인
- [ ] 주수단OD ↔ 목적OD 합계 오차 < 0.01%
- [ ] 권역별 OD 연도별 행수 검증
- [ ] ktdb_data_catalog 전체 파일 status='loaded' 확인
- [ ] bulk_loader.py --dry-run → 스킵 확인
- [ ] 시도간 집계 쿼리 < 5초
- [ ] pytest 파서 단위 테스트 통과
- [ ] **is_derived 컬럼 정합성: 뷰 SUM ↔ 원본 합계 행 일치 확인** (신규)
- [ ] **COMMENT ON 전 테이블/컬럼 존재 확인** (신규)
- [ ] **MV 갱신 완료 (mv_od_purpose_17, mv_od_mode_17, mv_od_freight_17)** (신규)
- [ ] **ktdb_mode_mapping 17행 적재 확인** (신규)
- [ ] **LLM 회귀 테스트 5종 통과** (신규)
- [ ] **RANGE 파티션 pruning 동작 확인 (BETWEEN 쿼리 시 해당 파티션만 스캔)** (신규)
```

---

## 부록: 변경 영향도 요약

### DDL 변경 대상 테이블

| 테이블 | 변경 내용 |
|--------|----------|
| `ktdb_od_purpose_250` | id 제거, is_derived 추가, LIST→RANGE 파티션, COMMENT |
| `ktdb_od_mode_250` | id 제거, is_derived 추가, LIST→RANGE 파티션, COMMENT |
| `ktdb_od_freight_250` | id 제거, LIST→RANGE 파티션, COMMENT |
| `ktdb_od_purpose_region` | is_derived 추가, 복합 인덱스 변경, COMMENT |
| `ktdb_od_mode_region` | is_derived 추가, 복합 인덱스 변경, COMMENT |

### 신규 생성 대상

| 객체 | 유형 |
|------|------|
| `ktdb_mode_mapping` | TABLE |
| `v_od_purpose_250` | VIEW |
| `v_od_mode_250` | VIEW |
| `v_od_freight_250` | VIEW |
| `v_socioeconomic` | VIEW |
| `v_od_purpose_region` | VIEW |
| `v_od_mode_region` | VIEW |
| `v_socioeconomic_region` | VIEW |
| `v_zone_lookup` | VIEW |
| `mv_od_purpose_17` | MATERIALIZED VIEW |
| `mv_od_mode_17` | MATERIALIZED VIEW |
| `mv_od_freight_17` | MATERIALIZED VIEW |

### 파서 수정 대상

| 파서 파일 | 수정 내용 |
|----------|----------|
| `od_purpose_250_parser.py` | `mark_derived()` 호출 추가, db_columns에 is_derived 추가 |
| `od_mode_250_parser.py` | 동일 |
| `od_purpose_region_parser.py` | 동일 |
| `od_mode_region_parser.py` | 동일 |
| `bulk_loader.py` | Phase 1에 COMMENT ON, ktdb_mode_mapping, 뷰/MV 생성 추가 |

### 신규 모듈

| 파일 | 용도 |
|------|------|
| `src/collector/derived_marker.py` | is_derived 자동 세팅 공통 함수 |
| `src/collector/mode_mapping_loader.py` | ktdb_mode_mapping 초기 데이터 적재 |
| `tests/test_llm_query_accuracy.py` | LLM 회귀 테스트 5종 |

---

*본 수정 계획서는 기존 `ktdb_raw_data_db_plan.md`(2026-03-20)의 LLM Text-to-SQL 연동 관점 보완이며, 기존 적재 시스템의 하위 호환성을 유지합니다. 모델-agnostic 설계로 LLM 모델 확정 후 토큰 예산 최적화만 추가하면 됩니다.*
