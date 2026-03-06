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
| 지층명 | 점토, 모래, 자갈, 풍화토, 연암, 경암 등 |
| 심도 (Depth) | 지층 상단/하단 심도 (m) |
| N치 (N-Value) | 표준관입시험(SPT) 타격 횟수 |
| 지하수위 | 지하수면 심도 (m) |
| 암질분류 | RQD (암질지수, %), TCR (코어회수율, %) |
| 시추공 번호 | BH-1, BH-2 등 |

### 2. 데이터 통합 모듈 (Data Matcher) — `src/matcher/`
시추공 번호 + 심도를 기준으로 물리시험/역학시험 데이터를 매칭.

| 데이터 유형 | 항목 |
|---|---|
| 물리시험 | Wn (함수비), Gs (비중), LL/PI (액성한계/소성지수), 입도분포 |
| 역학시험 | qu (일축압축강도), c (점착력), φ (내부마찰각) |
| 압밀시험 | Cc (압축지수), Cv (압밀계수), Pc (선행압밀하중) |

### 3. 지반정수 산정/그래프 모듈 — `src/analyzer/`
공학적 분석 알고리즘 및 자동 그래프 생성.

- 연약지반 압밀 곡선 (e-log P 그래프)
- 전단강도 포락선 (Mohr-Coulomb)
- USCS/AASHTO 분류 자동 판정
- 설계 지반정수 산정 (c, φ, N값 통계처리)

### 4. 이상치 탐지 모듈 — `src/analyzer/outlier.py`
공학적 범위를 벗어난 시험 데이터 자동 필터링 및 경고 생성.

- N치 범위 검증 (지층별 기대 범위)
- 물성치 상관관계 검증 (Wn vs LL, qu vs c 등)
- 경고 레벨: WARNING / ERROR / CRITICAL

---

## 폴더 구조

```
02_geotechnical_agent/
├── CLAUDE.md                   # 프로젝트 지침 (현재 파일)
├── README.md
├── pyproject.toml              # 의존성 관리
├── .env.example                # API 키 템플릿
│
├── src/
│   ├── parser/                 # 주상도 해석 모듈
│   │   ├── borehole_parser.py  # PDF 주상도 파싱
│   │   ├── ocr_engine.py       # OCR 처리
│   │   └── table_extractor.py  # 표 데이터 추출
│   ├── matcher/                # 데이터 통합 모듈
│   │   └── data_matcher.py     # 시추공+심도 기준 매칭
│   ├── analyzer/               # 지반정수 산정/이상치 탐지
│   │   ├── geotechnical_calc.py
│   │   ├── graph_generator.py
│   │   └── outlier.py
│   ├── classifier/             # 지반 분류 엔진 (USCS/AASHTO)
│   │   └── soil_classifier.py
│   ├── agent/                  # AI Agent 코어 (Claude API)
│   │   ├── agent.py
│   │   └── tools.py
│   ├── reporter/               # 성과품 생성
│   │   ├── excel_reporter.py   # openpyxl 기반 엑셀 출력
│   │   └── report_generator.py # Jinja2/python-docx 기반
│   └── tools/                  # Agent 도구 함수
│
├── prompts/                    # 프롬프트 템플릿 (분리 관리 필수)
│   ├── borehole_extraction.txt
│   ├── soil_classification.txt
│   └── outlier_detection.txt
│
├── tests/                      # pytest 테스트
│   ├── test_parser.py
│   ├── test_matcher.py
│   ├── test_analyzer.py
│   └── fixtures/               # 테스트용 샘플 PDF/데이터
│
├── data/
│   ├── raw/                    # 원천 PDF 보고서
│   ├── processed/              # 정형화된 중간 데이터
│   └── output/                 # 최종 성과품 (엑셀, 그래프)
│
├── config/
│   └── settings.py             # 환경 설정, 임계값 정의
│
└── notebooks/                  # 탐색적 분석, 프로토타이핑
    └── exploration.ipynb
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
