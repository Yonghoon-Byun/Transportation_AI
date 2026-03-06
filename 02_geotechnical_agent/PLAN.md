# 도로부 지반조사결과 분석 AI Agent - 상세 개발 계획

## 프로젝트 개요

도로부문 지반조사 보고서(PDF)를 자동 파싱·분석하여 설계분야별 지반정수를 산정하고 성과품을 생성하는 AI Agent.

**목표 KPI**
- 데이터 추출 정확도: 95% 이상
- 지반정수 산정 시간: 기존 대비 70% 단축

**시스템 파이프라인**
```
[원천 데이터(PDF)] → [구조 분석 및 OCR] → [데이터 정형화]
  → [지반정수 산정 알고리즘] → [최종 성과품(보고서+그래프)]
```

---

## 폴더 구조

```
02_geotechnical_agent/
├── src/
│   ├── parser/         # Module 1: PDF 파싱 + 주상도 해석
│   ├── classifier/     # Module 2: 데이터 통합 + 지반 분류 엔진
│   ├── agent/          # Module 3: AI Agent 코어 (Tool-use)
│   ├── reporter/       # Module 4: 보고서 생성 + 그래프
│   └── tools/          # Agent Tool 함수 (각 모듈 래핑)
├── data/               # 샘플 데이터 (gitignore)
├── prompts/            # Agent 프롬프트 템플릿
├── notebooks/          # 탐색적 분석 노트북
├── tests/              # pytest 테스트
├── config/             # 설정 파일 (임계값, 기준값 등)
├── requirements.txt
├── CLAUDE.md
└── PLAN.md
```

---

## 데이터 스키마 정의

### BoreholeLog (주상도)
```python
@dataclass
class SoilLayer:
    layer_no: int           # 층 번호
    soil_name: str          # 지층명 (예: "실트질 모래", "풍화암")
    depth_from: float       # 상단 심도 (m)
    depth_to: float         # 하단 심도 (m)
    thickness: float        # 층 두께 (m)
    spt_n_values: list[int] # 해당 층 N치 목록 (정수)
    n_avg: float            # 평균 N치
    is_rock: bool           # 암반층 여부
    rqd: float | None       # RQD (%, 암반층만)
    tcr: float | None       # TCR (%, 암반층만)
    color: str | None       # 색상 기술
    description: str | None # 상태 기술

@dataclass
class BoreholeLog:
    hole_no: str            # 시추공 번호 (예: "BH-1")
    location_x: float | None
    location_y: float | None
    ground_elevation: float | None  # 지표 표고 (m)
    gwl: float | None       # 지하수위 (m, 지표 기준)
    total_depth: float      # 시추 총 심도 (m)
    layers: list[SoilLayer]
    spt_records: list[SPTRecord]  # 심도별 N치 원시 레코드
```

### SPTRecord (N치 원시 기록)
```python
@dataclass
class SPTRecord:
    depth: float    # 시험 심도 (m)
    n_value: int    # N치 (0~50+, 50은 관입불능 표기)
    remarks: str | None
```

### LabTestResult (실내시험 결과)
```python
@dataclass
class PhysicalProperties:
    hole_no: str
    depth_from: float
    depth_to: float
    sample_no: str | None
    wn: float | None        # 자연함수비 (%)
    gs: float | None        # 비중
    ll: float | None        # 액성한계 (%)
    pl: float | None        # 소성한계 (%)
    pi: float | None        # 소성지수 (%)
    gravel_pct: float | None   # 자갈 함유율 (%)
    sand_pct: float | None     # 모래 함유율 (%)
    silt_pct: float | None     # 실트 함유율 (%)
    clay_pct: float | None     # 점토 함유율 (%)
    uscs_symbol: str | None    # USCS 분류 기호 (예: "SM", "CL")
    uscs_name: str | None

@dataclass
class MechanicalProperties:
    hole_no: str
    depth_from: float
    depth_to: float
    sample_no: str | None
    test_type: str          # "unconfined", "direct_shear", "triaxial"
    qu: float | None        # 일축압축강도 (kPa)
    cohesion: float | None  # 점착력 c (kPa)
    friction_angle: float | None  # 내부마찰각 φ (도)
    # 압밀시험
    cc: float | None        # 압축지수
    cr: float | None        # 팽창지수
    pc: float | None        # 선행압밀하중 (kPa)
    cv: float | None        # 압밀계수 (cm²/s)
    e0: float | None        # 초기 간극비

@dataclass
class LabTestResult:
    hole_no: str
    physical: list[PhysicalProperties]
    mechanical: list[MechanicalProperties]
```

### GeotechnicalParameters (지반정수 산정 결과)
```python
@dataclass
class DesignParameters:
    design_field: str       # "slope_soil", "slope_rock", "foundation",
                            # "retaining", "tunnel", "soft_ground"
    layer_name: str
    gamma_t: float | None   # 단위중량 (kN/m³)
    gamma_sat: float | None # 포화단위중량 (kN/m³)
    cohesion: float | None  # c (kPa)
    friction_angle: float | None  # φ (도)
    elastic_modulus: float | None # E (MPa)
    poisson_ratio: float | None   # ν
    n_avg: float | None     # 평균 N치
    qu: float | None        # 일축압축강도 (kPa)
    rqd: float | None       # RQD (%)
    rmr: float | None       # RMR (암반분류)
    smr: float | None       # SMR (비탈면 암반)
    gwl: float | None       # 지하수위 (m)
    source: str             # "measured" | "empirical" | "estimated"
    basis: str              # 산정 근거 (기준서, 경험식)
```

---

## Phase 1: PDF 파싱 + 주상도 해석 모듈 (`src/parser/`)

### 목표
PDF 원천 데이터에서 주상도(시추주상도) 정보를 구조화된 `BoreholeLog` 객체로 추출.

### 의존성
- pdfplumber, pdfminer.six (텍스트/표 추출)
- pytesseract + pdf2image (OCR 폴백, 스캔본 대응)
- pandas, numpy
- 없음 (외부 API 불필요)

### 세부 태스크

#### 1.1 PDF 전처리
- [ ] PDF 텍스트 레이어 유무 판별 (디지털 vs 스캔본)
- [ ] 디지털 PDF: pdfplumber로 텍스트/표 직접 추출
- [ ] 스캔본 PDF: pdf2image → pytesseract OCR 파이프라인 구현
- [ ] 페이지별 레이아웃 분류 (주상도 페이지 / 시험결과 페이지 / 기타)

#### 1.2 주상도 표 파서
- [ ] 주상도 표 헤더 패턴 정규식 정의 (지층명, 심도, N치, 지하수위 등)
- [ ] 업체별 양식 차이 대응: 컬럼명 정규화 매핑 테이블 작성 (`config/column_aliases.yaml`)
- [ ] 심도(Y축) 기준 행 파싱 로직 구현
- [ ] N치 이상값 처리: "50이상", ">50", "관입불능" → 정수 50 변환
- [ ] 암반층 판별: RQD/TCR 컬럼 존재 시 is_rock=True
- [ ] 지하수위(G.W.L) 추출: 표 외부 메모 영역 포함 탐색

#### 1.3 SPT 기록 파서
- [ ] 심도별 N치 목록 추출 → `SPTRecord` 리스트 생성
- [ ] 층별 N치 집계 (평균, 표준편차, 최소/최대)
- [ ] 과업 내 복수 시추공 → 층별 N치 분포 통계 집계

#### 1.4 이상치 탐지 (1차)
- [ ] N치 범위 검증: 0 ≤ N ≤ 50 (50 초과 시 경고)
- [ ] 심도 단조증가 검증 (역전 오류 탐지)
- [ ] 층 두께 합산 = 총 심도 검증

#### 1.5 데이터 직렬화
- [ ] `BoreholeLog` → JSON 저장 (`data/parsed/`)
- [ ] 복수 시추공 배치 처리 지원

### 예상 산출물
- `src/parser/pdf_loader.py` - PDF 전처리 및 페이지 분류
- `src/parser/borehole_parser.py` - 주상도 표 파서
- `src/parser/spt_parser.py` - N치 기록 파서
- `src/parser/anomaly_detector.py` - 이상치 탐지 (1차)
- `src/parser/schemas.py` - BoreholeLog, SPTRecord 데이터클래스
- `config/column_aliases.yaml` - 컬럼명 정규화 매핑

### 테스트 기준
- 샘플 PDF 3종 이상 파싱 성공률 95% 이상
- N치 추출값과 수동 확인값 일치율 95% 이상
- `tests/test_parser.py`: 정상/이상 케이스 각 10개 이상 단위 테스트
- 이상 심도 데이터 → 경고 메시지 정상 출력

---

## Phase 2: 데이터 통합 + 지반 분류 엔진 (`src/classifier/`)

### 목표
주상도 데이터 + 실내시험 결과를 매칭하여 USCS/AASHTO 분류를 수행하고, 설계분야별 지반정수를 산정.

### 의존성
- Phase 1 산출물 (BoreholeLog, SPTRecord)
- pandas, numpy, scipy

### 세부 태스크

#### 2.1 실내시험 데이터 파서
- [ ] 물리시험 결과표 파싱: Wn, Gs, LL, PL, PI, 입도분포
- [ ] 역학시험 결과표 파싱: qu, c, φ (시험 종류별)
- [ ] 압밀시험 결과표 파싱: Cc, Cr, Pc, Cv, e₀
- [ ] 요약표(Summary Table) 우선 인식 로직 구현
- [ ] `LabTestResult` 객체 생성

#### 2.2 데이터 매칭
- [ ] 매칭 키: 시추공번호(Hole No.) + 채취심도(Depth) ±0.5m 허용오차
- [ ] 주상도 지층 ↔ 실내시험 결과 1:N 매칭
- [ ] 매칭 실패 레코드 경고 로깅

#### 2.3 지반 분류 엔진
- [ ] USCS 통일분류법 구현:
  - 조립토: 자갈/모래 분류 → GW/GP/GM/GC/SW/SP/SM/SC
  - 세립토: LL, PI 기반 → ML/CL/OL/MH/CH/OH/Pt
  - 소성도 차트(Plasticity Chart) 로직 구현
- [ ] AASHTO 분류 구현: A-1~A-7 그룹 분류
- [ ] 암반 분류:
  - RMR(Rock Mass Rating) 산정 로직
  - SMR(Slope Mass Rating) 산정 로직 (비탈면 적용)

#### 2.4 지반정수 산정 (설계분야별)
각 설계분야별 `DesignParameters` 산정:

- [ ] **비탈면(토사)**: γt, γsat, c', φ', G.W.L
  - N치 기반 경험식 (Meyerhof, Peck 등)
  - 직접전단/삼축시험 결과 우선 적용
- [ ] **비탈면(암반)**: qu, RQD, RMR, SMR
  - RMR 산정: 암석강도, RQD, 절리간격, 절리상태, 지하수
- [ ] **기초**: N치, c, φ, E (탄성계수)
  - N치 → E 경험식 (Bowles 등)
- [ ] **흙막이**: γ, c, φ, Es, kh (수평지반반력계수)
  - kh = 변형계수 기반 산정
- [ ] **터널**: E, ν, σc, RQD, TCR
- [ ] **연약지반**: Cc, Cr, Pc, Cv, e₀
  - 압밀침하량 산정 지원

#### 2.5 통계 집계
- [ ] 지층별 각 지반정수 평균/표준편차/분산/최소/최대 산출
- [ ] 이상치 탐지 (2차): 공학적 범위 기반
  - γt: 14~22 kN/m³ (표준), 범위 외 경고
  - φ: 0°~45° (토사), 범위 외 경고
  - c: ≥0 kPa, 음수 경고
  - qu: 암반 종류별 기준 범위 적용
- [ ] 경고 메시지 구조화 (`AnomalyWarning` 객체)

### 예상 산출물
- `src/classifier/lab_test_parser.py` - 실내시험 파서
- `src/classifier/data_matcher.py` - 주상도-시험 매칭
- `src/classifier/uscs_classifier.py` - USCS/AASHTO 분류
- `src/classifier/rock_classifier.py` - RMR/SMR 산정
- `src/classifier/parameter_calculator.py` - 설계분야별 지반정수 산정
- `src/classifier/statistics.py` - 통계 집계 및 이상치 탐지
- `src/classifier/schemas.py` - LabTestResult, DesignParameters 데이터클래스
- `config/engineering_limits.yaml` - 지반정수 공학적 범위 기준값
- `config/empirical_formulas.yaml` - 경험식 계수 설정

### 테스트 기준
- USCS 분류: 알려진 샘플 20개 이상 정확도 95% 이상
- RMR 산정: 수동 계산 대비 오차 ±5% 이하
- 매칭 성공률: 샘플 데이터 기준 90% 이상
- `tests/test_classifier.py`: 분류·산정 단위 테스트 20개 이상

---

## Phase 3: AI Agent 파이프라인 + Tool-use (`src/agent/`, `src/tools/`)

### 목표
Claude API(또는 LangChain)를 기반으로 Tool-use Agent를 구성. 자연어 질의로 지반분석 워크플로를 자동 실행.

### 의존성
- Phase 1, 2 산출물
- anthropic SDK (Claude API) 또는 LangChain
- Phase 1, 2 모듈 (Tool로 래핑)

### 세부 태스크

#### 3.1 Tool 정의 (`src/tools/`)
아래 Tool을 각각 함수로 구현하고 스키마(JSON Schema) 정의:

- [ ] `parse_borehole_pdf(pdf_path: str) -> list[BoreholeLog]`
  - Phase 1 파서 래핑
- [ ] `match_lab_tests(borehole_logs: list, lab_pdf_path: str) -> MatchedDataset`
  - Phase 2 매칭 래핑
- [ ] `classify_soil(physical_props: dict) -> ClassificationResult`
  - USCS/AASHTO 분류 래핑
- [ ] `calculate_design_parameters(dataset: MatchedDataset, design_field: str) -> list[DesignParameters]`
  - 설계분야별 지반정수 산정 래핑
- [ ] `detect_anomalies(dataset: MatchedDataset) -> list[AnomalyWarning]`
  - 이상치 탐지 래핑
- [ ] `generate_n_distribution_chart(borehole_logs: list, output_path: str) -> str`
  - N치 분포 그래프 생성 래핑
- [ ] `generate_report(dataset: MatchedDataset, params: list[DesignParameters], output_path: str) -> str`
  - 보고서 생성 래핑

#### 3.2 프롬프트 템플릿 (`prompts/`)
- [ ] `system_prompt.md` - Agent 역할/전문성 정의 (지반공학 전문가 페르소나)
- [ ] `analysis_workflow.md` - 분석 워크플로 지시 프롬프트
- [ ] `parameter_interpretation.md` - 지반정수 해석 기준 프롬프트
- [ ] `anomaly_explanation.md` - 이상치 설명 생성 프롬프트
- [ ] `report_template.md` - 보고서 섹션별 작성 지시

#### 3.3 Agent 코어 (`src/agent/`)
- [ ] `GeotechnicalAgent` 클래스 구현
  - Claude API Tool-use 루프 구현 (tool_choice auto)
  - 최대 반복 횟수 설정 (무한루프 방지)
- [ ] 사용자 질의 파싱: "BH-1 주상도 분석해줘" → Tool 호출 시퀀스 결정
- [ ] 중간 결과 스트리밍 출력 지원
- [ ] 에러 복구 로직: Tool 실패 시 재시도/대안 경로

#### 3.4 워크플로 오케스트레이션
- [ ] 전체 파이프라인 자동 실행 모드: PDF 입력 → 보고서 출력까지 1-command
- [ ] 단계별 인터랙티브 모드: 각 단계 확인 후 진행
- [ ] 병렬 처리: 복수 시추공 동시 분석

#### 3.5 CLI 인터페이스
- [ ] `main.py` 또는 `cli.py` 구현 (argparse/click)
  ```
  python -m src.agent.cli analyze --pdf report.pdf --field slope_soil
  python -m src.agent.cli interactive
  ```

### 예상 산출물
- `src/tools/borehole_tools.py`
- `src/tools/classification_tools.py`
- `src/tools/parameter_tools.py`
- `src/tools/report_tools.py`
- `src/agent/geotechnical_agent.py` - Agent 코어
- `src/agent/tool_registry.py` - Tool 등록 및 스키마 관리
- `src/agent/cli.py` - CLI 진입점
- `prompts/system_prompt.md`
- `prompts/analysis_workflow.md`
- `prompts/parameter_interpretation.md`

### 테스트 기준
- Tool 단위 테스트: 각 Tool 함수 정상/오류 케이스
- Agent 통합 테스트: 샘플 PDF → 지반정수 산정까지 엔드투엔드 1회 이상 성공
- `tests/test_agent.py`, `tests/test_tools.py`

---

## Phase 4: 보고서 생성 + 그래프 (`src/reporter/`)

### 목표
분석 결과를 공학 보고서 양식(Word/PDF)과 표준 그래프로 자동 출력.

### 의존성
- Phase 1, 2, 3 산출물
- matplotlib, plotly (그래프)
- python-docx (Word 보고서)
- Jinja2 (템플릿 렌더링)
- openpyxl (Excel 요약표)

### 세부 태스크

#### 4.1 그래프 생성
- [ ] **N치 분포 그래프**: 시추공별 심도-N치 플롯 (X: N치, Y: 심도 역축)
- [ ] **과업 내 N치 통계 그래프**: 지층별 평균±표준편차 막대 그래프
- [ ] **e-log P 압밀 곡선**: 연약지반 압밀시험 결과 플롯
- [ ] **전단강도 특성 그래프**: Mohr-Coulomb 파괴선 플롯
- [ ] **소성도 차트(Plasticity Chart)**: LL-PI 플롯 + USCS 구분선
- [ ] **입도 분포 곡선**: 체가름/비중계 시험 결과 복합 곡선
- [ ] 그래프 스타일: 공학 보고서 기준 (흑백 인쇄 대응, 한글 폰트)

#### 4.2 요약표 생성
- [ ] **지층 요약표**: 지층명, 심도, 두께, 평균 N치, USCS
- [ ] **지반정수 요약표**: 설계분야별 채택 지반정수 (평균/설계값)
- [ ] **이상치 경고 목록**: 탐지된 이상값 및 처리 근거
- [ ] Excel 출력 (openpyxl): 시트별 데이터 정리

#### 4.3 Word 보고서 자동 생성
보고서 섹션 구조:
```
1. 과업 개요
2. 시추조사 결과
   2.1 지층 구성
   2.2 지하수위
   2.3 N치 분포 (그래프 삽입)
3. 실내시험 결과
   3.1 물리시험 (표 + 소성도 차트)
   3.2 역학시험 (표 + 전단강도 그래프)
   3.3 압밀시험 (e-log P 곡선, 연약지반만)
4. 지반 분류 결과 (USCS/AASHTO)
5. 지반정수 산정
   5.1 설계분야별 지반정수 요약표
   5.2 산정 근거
6. 이상치 탐지 결과 및 조치
```
- [ ] python-docx 기반 섹션별 자동 삽입
- [ ] 그래프 이미지 Word 삽입
- [ ] 표 자동 서식 (행 색상 교대, 헤더 볼드)
- [ ] 한글 양식 호환 (HWP 변환은 추후 검토)

#### 4.4 PDF 출력
- [ ] Word → PDF 변환 (LibreOffice CLI 또는 docx2pdf)

### 예상 산출물
- `src/reporter/chart_generator.py` - 그래프 생성 모듈
- `src/reporter/table_generator.py` - 요약표 생성
- `src/reporter/word_reporter.py` - Word 보고서 생성
- `src/reporter/excel_exporter.py` - Excel 출력
- `src/reporter/pdf_converter.py` - PDF 변환
- `prompts/report_template.md` - 보고서 작성 지시 프롬프트

### 테스트 기준
- 그래프 생성: 6종 그래프 정상 출력 (파일 존재 + 비어있지 않음 확인)
- Word 보고서: 6개 섹션 모두 포함 여부 확인
- Excel: 시트별 데이터 행 수 검증
- `tests/test_reporter.py`

---

## 공통 설정 파일

```
config/
├── column_aliases.yaml      # PDF 컬럼명 정규화 매핑
├── engineering_limits.yaml  # 지반정수 공학적 허용 범위
├── empirical_formulas.yaml  # 경험식 계수 (설계분야별)
└── design_standards.yaml   # 적용 기준 (KDS, AASHTO 등)
```

---

## 기술 스택 확정

| 역할 | 라이브러리 |
|------|-----------|
| PDF 파싱 (디지털) | pdfplumber, pdfminer.six |
| PDF 파싱 (스캔본) | pdf2image, pytesseract |
| 데이터 처리 | pandas, numpy, scipy |
| AI Agent | anthropic SDK (Claude API, Tool-use) |
| 그래프 | matplotlib, plotly |
| 보고서 (Word) | python-docx, Jinja2 |
| 보고서 (Excel) | openpyxl |
| PDF 변환 | docx2pdf 또는 LibreOffice CLI |
| 테스트 | pytest, pytest-cov |
| 타입 힌트 | typing, dataclasses |

---

## 확인 완료 사항

- [x] 입력 데이터 형식: PDF (디지털 + 스캔본 모두 대응)
- [x] 지반조사 종류: 시추조사 + SPT(표준관입시험) + 실내시험 (물리·역학·압밀)
- [x] 분석 기준: KDS, 구조물기초설계기준, AASHTO
- [x] 분류 체계: USCS 통일분류법, AASHTO 분류
- [x] Agent 의사결정 범위: 파싱·분류·지반정수 산정까지 (설계 추천은 판단 보조 수준)
- [x] LLM: Claude API (Tool-use) 우선 적용
- [x] 설계분야: 비탈면(토사/암반), 기초, 흙막이, 터널, 연약지반 6개 분야
- [x] 핵심 그래프: N치 분포, e-log P, 전단강도, 소성도, 입도분포 확인

## 미확인/추후 결정 사항

- [ ] HWP(한글) 파일 입력 지원 여부 (HWP → PDF 변환 전처리 필요)
- [ ] 물리탐사(탄성파, 전기비저항) 결과 연동 범위
- [ ] 웹 UI 개발 여부 (CLI 우선, FastAPI 기반 API 추후 검토)
- [ ] 온프레미스 배포 vs 클라우드 배포 (데이터 보안 정책 확인 필요)
- [ ] 기존 보고서 양식 템플릿 수집 (업체별 표준 양식 3종 이상 확보 필요)
- [ ] RMR 세부 항목 입력 방식 (절리 방향, 간격 등 PDF에서 자동 추출 가능성)

---

## 개발 순서 및 마일스톤

| Phase | 기간 | 완료 기준 |
|-------|------|----------|
| Phase 1 | 3주 | 샘플 PDF 3종 파싱 성공, 테스트 통과 |
| Phase 2 | 2주 | USCS 분류 95% 정확도, 지반정수 산정 검증 |
| Phase 3 | 2주 | CLI 엔드투엔드 실행 성공 |
| Phase 4 | 2주 | 6종 그래프 + Word 보고서 자동 생성 |
| 통합 테스트 | 1주 | 전체 파이프라인 KPI 달성 확인 |
