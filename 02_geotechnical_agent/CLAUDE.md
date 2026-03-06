# 도로부 지반조사결과 분석 AI Agent

## 프로젝트 컨텍스트

**상위 프로젝트**: Transportation_AI (교통부문 AI 개발 모노레포)
- 위치: `../` (Transportation_AI/)
- 형제 프로젝트: `01_ktdb/` (국가교통DB), `03_railway_optimization/` (철도 선형 최적화)

**개발 목적**: 비정형 지반조사 데이터(주상도, 시험성과표)의 정형화 및 공학적 분석 자동화를 통해 설계 품질 표준화 및 업무 효율성 제고.
- KPI: 데이터 추출 정확도 95% 이상, 지반정수 산정 소요 시간 70% 단축

**적용 설계 분야**: 비탈면(토사/암반), 기초(말뚝/얕은기초), 흙막이(가시설), 터널, 연약지반

**설계기준**: KDS, 구조물기초설계기준, AASHTO, USCS 통일분류법, AASHTO 분류 체계

---

## 처리 파이프라인

```
[원천 데이터 (PDF)]
        |
        v
[1. 구조 분석 및 OCR]          src/parser/
        |
        v
[2. 데이터 정형화]              src/parser/ + src/matcher/
        |
        v
[3. 지반정수 산정 알고리즘]     src/analyzer/ + src/classifier/
        |
        v
[4. 이상치 탐지 및 검증]        src/analyzer/
        |
        v
[5. 최종 성과품 생성]           src/reporter/
   - 정형화된 엑셀 데이터
   - 물성치 산정 결과
   - 분석 그래프 (e-log P, 전단강도 등)
```

---

## 4대 핵심 모듈

### 1. 주상도 해석 모듈 (Borehole Log Parser) — `src/parser/`
PDF 형식 주상도에서 지반 데이터를 구조적으로 추출.

| 추출 항목 | 설명 |
|---|---|
| 지층명 | 매립토, 퇴적토, 풍화토, 풍화암, 연암 등 (토질분류) |
| 심도 (Depth) | 지층 상단/하단 심도 (m) |
| N치 (N-Value) | 표준관입시험(SPT) 타격 횟수 (정수형, 1m 또는 1.5m 간격) |
| 지하수위 | 지하수면 심도 (m) |
| 암질분류 | RQD (암질지수, %), TCR (코어회수율, %) — 암반층(풍화암 이하)에서만 |
| 시추공 번호 | BH-1, BH-2 등 |

### 2. 데이터 통합 모듈 (Data Matcher) — `src/tools/data_matcher.py`
시추공 번호(Hole No.) + 채취심도(Depth) 기준으로 물리시험/역학시험 데이터를 매칭.
매칭 허용 오차: ±0.5m.

| 데이터 유형 | 항목 |
|---|---|
| 물리시험 | Wn (함수비), Gs (비중), LL/PL/PI (액성한계/소성한계/소성지수), 입도분포 |
| 역학시험 | qu (일축압축강도), c (점착력), φ (내부마찰각) |
| 압밀시험 | Cc (압축지수), Cr (재압축지수), Cv (압밀계수), Pc (선행압밀하중), e₀ (초기간극비) |

### 3. 지반정수 산정/그래프 모듈 — `src/tools/parameter_estimator.py` + `src/reporter/graph_generator.py`
설계분야별 공학적 분석 알고리즘 및 자동 그래프 생성.

- 연약지반 압밀 곡선 (e-log P 그래프)
- 전단강도 포락선 (Mohr-Coulomb)
- USCS/AASHTO 분류 자동 판정 (`src/classifier/`)
- 설계 지반정수 산정 (c, φ, N값 통계처리)
- N치 분포 그래프 + 지층별 평균±표준편차
- 소성도 차트 (Plasticity Chart)
- 입도 분포 곡선

### 4. 이상치 탐지 모듈 — `src/classifier/outlier_detector.py`
공학적 범위를 벗어난 시험 데이터 자동 필터링 및 경고 생성.

- N치 범위 검증 (지층별 기대 범위)
- 물성치 상관관계 검증 (Wn vs LL, qu vs c 등)
- 심도 단조증가 검증, 층 두께 합산 검증
- 경고 레벨: WARNING / ERROR / CRITICAL

---

## 폴더 구조

```
02_geotechnical_agent/
├── CLAUDE.md                   # 프로젝트 지침 (현재 파일)
├── PLAN.md                     # 상세 개발 계획
├── requirements.txt            # 의존성 관리
│
├── src/
│   ├── models/                 # 데이터 스키마 (dataclass)
│   │   └── schemas.py          # BoreholeLog, SoilLayer, SPTRecord,
│   │                           # PhysicalProperties, MechanicalProperties,
│   │                           # ConsolidationResult, LabTestResult,
│   │                           # DesignParameter, AnomalyWarning
│   ├── parser/                 # Module 1: 주상도 해석 모듈
│   │   ├── pdf_extractor.py    # PDF 구조 분석 (텍스트/표/이미지)
│   │   ├── borehole_log_parser.py  # 주상도 파싱 → BoreholeLog
│   │   └── lab_test_parser.py  # 실내시험 성과표 파싱
│   ├── classifier/             # 지반 분류 + 이상치 탐지
│   │   ├── soil_classifier.py  # USCS/AASHTO 분류 엔진
│   │   ├── rock_classifier.py  # RMR/SMR 암반 분류
│   │   └── outlier_detector.py # 통계적+공학적 이상치 탐지
│   ├── tools/                  # Module 2: 데이터 통합 + 정수 산정
│   │   ├── data_matcher.py     # Hole No.+Depth 기준 매칭 (±0.5m)
│   │   ├── parameter_estimator.py  # 설계분야별 지반정수 산정
│   │   └── statistics.py       # 지층별 기술통계 산출
│   ├── agent/                  # Module 3: AI Agent 코어 (Claude API)
│   │   ├── geotechnical_agent.py   # Tool-use Agent
│   │   └── pipeline.py         # 분석 파이프라인 오케스트레이션
│   └── reporter/               # Module 4: 성과품 생성
│       ├── excel_reporter.py   # openpyxl 기반 엑셀 출력
│       ├── graph_generator.py  # matplotlib 그래프 (6종)
│       └── report_builder.py   # python-docx 기반 보고서
│
├── prompts/                    # 프롬프트 템플릿 (분리 관리 필수)
│   ├── system_prompt.py        # Agent 역할/전문성 정의
│   ├── borehole_analysis.py    # 주상도 추출 프롬프트
│   ├── data_integration.py     # 데이터 매칭/통계 프롬프트
│   ├── outlier_detection.py    # 이상치 탐지 프롬프트
│   ├── parameter_estimation.py # 지반정수 산정 프롬프트
│   └── report_generation.py    # 보고서 작성 프롬프트
│
├── config/                     # 설정 파일
│   ├── design_standards.yaml   # 적용 기준 (KDS, AASHTO 등)
│   ├── column_aliases.yaml     # 업체별 컬럼명 정규화 매핑
│   ├── engineering_limits.yaml # 지반정수 공학적 허용 범위
│   └── empirical_formulas.yaml # 경험식 계수 (설계분야별)
│
├── tests/                      # pytest 테스트
├── data/                       # 데이터 (gitignore)
├── docs/                       # 기획서 PDF
└── notebooks/                  # 탐색적 분석
```

---

## 기술 스택

| 분류 | 라이브러리 |
|---|---|
| Python | 3.11+ |
| AI/Agent | Claude API (Anthropic), anthropic SDK |
| PDF 파싱 | pdfplumber, tabula-py |
| OCR | pytesseract 또는 Claude Vision |
| 데이터 처리 | pandas, numpy |
| 지반 분류 | scikit-learn |
| 엑셀 출력 | openpyxl |
| 문서 생성 | Jinja2, python-docx |
| 그래프 | matplotlib |
| 테스트 | pytest |

---

## 핵심 도메인 용어

| 용어 | 영문/약어 | 설명 |
|---|---|---|
| 주상도 | Borehole Log | 지층 구성을 시각적으로 표현한 도표 |
| 표준관입시험 | SPT | 해머로 타격하여 지반 강도 측정, N치(타격횟수) 산출 |
| N치 | N-Value | SPT 타격횟수, 지반 경도 지표 |
| 심도 | Depth | 지표면으로부터의 깊이 (m) |
| 지하수위 | GWL (Ground Water Level) | 지하수가 존재하는 심도 |
| 암질지수 | RQD (Rock Quality Designation) | 코어 샘플 중 10cm 이상 조각의 비율 (%) |
| 코어회수율 | TCR (Total Core Recovery) | 전체 회수된 코어의 비율 (%) |
| 함수비 | Wn (Natural Water Content) | 흙 속 물의 비율 (%) |
| 비중 | Gs (Specific Gravity) | 흙 입자의 비중 |
| 액성한계 | LL (Liquid Limit) | 흙이 소성상태에서 액성상태로 변하는 함수비 |
| 소성지수 | PI (Plasticity Index) | LL - PL, 흙의 소성 범위 |
| 일축압축강도 | qu (Unconfined Compressive Strength) | 구속압 없이 측정한 압축강도 (kPa) |
| 점착력 | c (Cohesion) | 흙 입자 간 결합력 (kPa) |
| 내부마찰각 | φ (Friction Angle) | 흙의 전단저항각 (°) |
| 압축지수 | Cc (Compression Index) | e-log P 곡선의 기울기 |
| 압밀계수 | Cv (Coefficient of Consolidation) | 압밀 속도 관련 계수 |
| 선행압밀하중 | Pc (Preconsolidation Pressure) | 과거 최대 유효응력 |
| USCS | Unified Soil Classification System | 통일분류법 (GW, GP, GM, GC, SW, SP, SM, SC, ML, CL 등) |

---

## 코딩 컨벤션 및 규칙

### 필수 규칙
- Python 3.11+ 문법 사용
- 모든 함수/클래스에 타입 힌트 필수
- Docstring은 Google 스타일 사용
- 프롬프트는 반드시 `prompts/` 폴더에 `.txt` 파일로 분리 관리 (코드 내 하드코딩 금지)
- 테스트는 `tests/` 폴더에 pytest로 작성, 함수명 `test_*` 패턴 준수
- 환경변수(API 키 등)는 `.env` 파일로 관리, 코드에 직접 삽입 금지

### 데이터 스키마 규칙
- 시추공 식별자: `borehole_id` (str, 예: "BH-1")
- 심도 단위: 미터(m), float 타입
- N치: int 타입, 미측정 시 `None`
- 물성치 미측정: `None` (0 사용 금지 - 공학적 의미 혼동 방지)
- 지층명은 KDS 기준 표준 명칭 사용

### Agent 프레임워크
- Claude API (Anthropic) 직접 사용 우선
- 필요 시 LangChain 도입 검토
- Tool use 패턴으로 모듈 호출

### 품질 기준
- 데이터 추출 정확도 목표: 95% 이상
- 단위 테스트 커버리지 목표: 80% 이상
- 모든 공학 계산식에 출처(설계기준 조항) 주석 명시
