# 철도 최적 선형 대안 자동생성 Agent

## 1. 프로젝트 컨텍스트

### 목적
사업구상 및 기본계획 단계에서 일반철도/도시철도 노선계획을 지원하는 AI Agent.
시/종점 입력만으로 GIS 기반 지형·지장물 분석 → 설계기준 충족 노선 대안 자동 생성 → 개략 공사비 및 비교 보고서 산출까지 전 과정을 자동화한다.

### 범위 (두 기획서 통합)
- **철도1부**: 수치지도/위성 데이터로 지장물 자동 인식, 구조물 형식(개착/터널) 판정, 최적 노선 대안 생성, RDBIM/AutoCAD Civil 3D 연동
- **철도2부**: 국가공간정보체계 DB 연계, Physarum Algorithm 기반 코리더 탐색, 정거장 위치 추천, 환경·민원 제약 필터링, 개략 공사비 산출, 대안 비교 보고서/도면 자동 작성

### 상위 프로젝트
Transportation_AI (교통부문 AI 개발) > 03_railway_optimization

### KPI
- 노선 대안별 리스크 검토 시간 70% 이상 단축
- 기준 적합성 자동 체크 → 설계자 수작업 검토 최소화

---

## 2. 핵심 도메인 개념

### 평면선형 (Horizontal Alignment)
- **직선(Tangent)**: 기본 주행 구간
- **원곡선(Circular Curve)**: 최소 곡선반경(R_min) 이상 확보 필수
- **완화곡선(Transition Curve)**: 클로소이드 또는 3차 포물선, 직선-원곡선 접속부에 삽입
- **최소 곡선반경**: 설계속도에 따라 KDS/KR Code 기준 적용 (예: V=200km/h → R≥1800m)

### 종단선형 (Vertical Alignment)
- **종단구배(Gradient)**: 최대 구배 제한 (일반철도 25‰, 특수구간 35‰ 이하)
- **종단곡선(Vertical Curve)**: 볼록/오목 종단곡선, 최소 곡선길이 확보
- **DEM 기반 절토/성토량**: 지형 고도에 따라 공사비 결정 요소

### 지장물 (Obstacles)
자동 인식 대상: 민가, 도로, 철도, 학교, 병원, 아파트, 문화재, 광산, 환경규제구역, 군사시설
인식 방법: GIS 레이어 + 위성 영상 객체 탐지 (YOLOv8 등)

### 구조물 형식 판정
- **지표 구간**: 절토/성토 (토공)
- **개착(Open Cut)**: 도심 지하 구간, 토피 얕은 경우
- **터널(Tunnel)**: 산악 관통, 도심 심층
- 판정 기준: 토피고, 주변 지장물 밀도, 지반 조건 → Rule Engine 적용

### 주요 설계 파라미터
| 항목 | 파라미터명 | 단위 |
|------|-----------|------|
| 설계속도 | design_speed | km/h |
| 최소 곡선반경 | min_curve_radius | m |
| 최대 구배 | max_gradient | ‰ |
| 완화곡선 길이 | transition_length | m |
| 캔트 | cant | mm |
| 캔트 부족량 | cant_deficiency | mm |
| 슬랙 | slack | mm |

---

## 3. 모듈 구조

```
03_railway_optimization/
├── src/
│   ├── terrain/          # 지형 데이터 처리
│   ├── obstacles/        # 지장물 인지 모듈 (신규)
│   ├── alignment/        # 선형 설계 엔진
│   ├── optimizer/        # 최적화 알고리즘
│   ├── structure/        # 구조물 형식 판정 엔진 (신규)
│   ├── constraints/      # 설계 기준/제약조건
│   ├── cost_model/       # 개략 공사비 산정 모델
│   ├── station/          # 정거장 위치 추천 (신규)
│   ├── report/           # 대안 비교 보고서/도면 생성 (신규)
│   ├── integration/      # 외부 시스템 연동 (RDBIM, Civil 3D)
│   └── visualizer/       # 평면·종단면 시각화
├── config/
│   ├── design_standards.yaml   # 설계기준 파라미터
│   └── data_sources.yaml       # 데이터 소스 엔드포인트
├── data/
│   ├── raw/              # 원시 GIS/위성 데이터
│   └── processed/        # 전처리 완료 데이터
├── tests/
├── notebooks/            # 탐색/검증용 Jupyter 노트북
└── docs/
```

### 각 모듈 역할 상세

#### `src/terrain/`
- DEM(수치표고모델) 로드 및 전처리: GDAL/rasterio 활용
- 종단 지형 프로파일 추출: 노선 후보선 따라 고도값 샘플링
- 절토/성토 볼륨 계산: 시단면법 또는 평균단면법
- 경사(slope), 향(aspect), 기복도(roughness) 분석

#### `src/obstacles/`
- GIS 레이어(SHP/GeoJSON) 기반 지장물 폴리곤 로드
- 위성 영상 객체 탐지 연동 (외부 모델 결과 수신)
- 지장물 버퍼 생성: 회피 경계 영역 설정
- 민감도 분류: 회피 필수(문화재, 환경규제) / 비용 증가(민가, 아파트) / 협의 필요(도로, 철도)

#### `src/alignment/`
- 평면선형 생성: 직선 + 원곡선 + 완화곡선 조합
- 종단선형 생성: 구배 구간 + 종단곡선 조합
- 기하 검증: 최소 곡선반경, 최대 구배, 완화곡선 길이 등 기준 충족 여부
- IP(교각점) 좌표 기반 선형 정의

#### `src/optimizer/`
- **Physarum Algorithm**: 점액곰팡이 최적화 — 복수 출발점에서 시/종점 연결 경로 탐색
- **Generative Design (Rule-based)**: 설계 조건 기반 노선 대안 생성
- **Genetic Algorithm / A***: 보조 최적화 알고리즘
- 목적함수: 건설비 최소화 + 환경 영향 최소화 + 이동 시간 최소화 (가중합)
- 제약: 지장물 회피, 설계기준 충족, 연계 시스템 접속점 위치

#### `src/structure/`
- 구간별 구조물 형식 자동 판정: 토공 / 교량 / 개착 / 터널
- 판정 Rule Engine: 토피고, 지장물 밀도, 경사도, 도심 여부
- 공사비 단가 연계: 구조물 형식별 m당 공사비 적용

#### `src/constraints/`
- 설계기준 파라미터 로드 및 관리 (config/design_standards.yaml)
- 기준 적합성 자동 체크 함수 제공
- 규정 소스: KDS(한국설계기준), KR Code(철도설계기준), TSI, EN, UIC

#### `src/cost_model/`
- 개략 공사비 산출: 토공 + 구조물 + 궤도 + 전기/신호/통신
- 공시지가 연계: 용지보상비 산출
- 대안별 비용 비교 테이블 생성

#### `src/station/`
- 정거장 위치 후보 추천: 수요 밀집지역, 환승 편의, 도시계획 용도지역 분석
- 정거장 간격 기준 적용 (도시철도: 1~1.5km, 일반철도: 수 km)

#### `src/report/`
- 대안별 비교 보고서 자동 작성 (PDF/Excel)
- 평면도/종단면도 자동 생성
- LLM Agent 연계: 서술형 분석 텍스트 생성

#### `src/integration/`
- RDBIM 데이터 변환/송출
- AutoCAD Civil 3D API 연동 (노선 좌표 내보내기)
- Dynamo 스크립트 연계

#### `src/visualizer/`
- 평면 노선도: folium / plotly 기반 인터랙티브 지도
- 종단면도: matplotlib 기반 고도 프로파일 + 구조물 구간 표시
- 3D 시각화: pyvista 또는 plotly 3D

---

## 4. 설계기준 참조

### 국내 기준
| 기준명 | 적용 내용 |
|--------|----------|
| KDS 47 (철도설계기준) | 평면·종단선형, 궤도, 구조물 일반 |
| KR Code (한국철도표준) | 속도별 최소 곡선반경, 최대 구배, 캔트 |
| 철도의 건설기준에 관한 규정 | 법적 최소 기준, 안전 규정 |

### 국제 기준
| 기준명 | 적용 내용 |
|--------|----------|
| TSI (Technical Specifications for Interoperability) | 유럽 철도 상호운용 기술기준 |
| EN (European Norms) | 유럽 표준 — 궤간, 하중, 선형 등 |
| UIC (International Union of Railways) | 국제 철도 설계 권고 기준 |

### config/design_standards.yaml 구조 예시
```yaml
general_railway:
  design_speeds: [100, 150, 200, 250, 300]  # km/h
  min_curve_radius:
    100: 600    # m
    150: 1200
    200: 1800
    250: 2800
    300: 4000
  max_gradient:
    normal: 25   # permille
    special: 35
  cant_max: 180  # mm
  cant_deficiency_max: 130  # mm

urban_railway:
  design_speeds: [80, 100, 120]
  min_curve_radius:
    80: 300
    100: 500
    120: 800
  max_gradient:
    normal: 35
    special: 40
```

---

## 5. 데이터 소스

### 국내 공간정보
| 소스 | 데이터 종류 | 접근 방법 |
|------|-----------|----------|
| 국토지리정보원 | 수치지형도(1:5000), DEM | WMS/WFS API |
| 국가공간정보체계(NSDI) | 지적, 용도지역, 도시계획 | Open API |
| 문화재청 | 문화재 보호구역 | SHP 다운로드 |
| 환경부 | 환경규제구역, 생태자연도 | 환경공간정보서비스 |
| 국토교통부 공시지가 | 표준지 공시지가 | REST API |
| 도시계획 포털 | 도시기본계획, 개발계획 | API/SHP |

### 국제/위성 데이터
| 소스 | 데이터 종류 |
|------|-----------|
| OpenStreetMap (OSM) | 도로, 철도, 건물, 토지이용 |
| Open Railway Map | 기존 철도망 |
| SRTM / Copernicus DEM | 전 세계 수치표고모델 |
| WDPA (World Database on Protected Areas) | 보호지역 (국립공원 등) |
| Sentinel-2 / Landsat | 위성 다중분광 영상 |
| GeoNetwork | 공간정보 메타데이터 카탈로그 |

### 교통 DB
- 기존 도로/철도 구축망 DB
- 수요 데이터: OD(기종점) 행렬

---

## 6. 기술 스택

### 언어 및 런타임
- Python 3.11+
- (향후) C3D API 연동 시 Dynamo/IronPython 스크립트 병행

### 핵심 라이브러리

#### 공간 데이터
```
geopandas       # 벡터 공간 데이터 처리 (SHP, GeoJSON, GeoPackage)
shapely         # 기하 연산 (버퍼, 교차, 합집합)
pyproj          # 좌표계 변환 (WGS84 ↔ EPSG:5186 등)
rasterio        # 래스터 데이터 (DEM, 위성 영상)
gdal            # 저수준 GIS 데이터 입출력
fiona           # 벡터 파일 입출력
```

#### 수치 계산
```
numpy           # 행렬 연산, 수치 계산
scipy           # 최적화(minimize, linprog), 보간, 통계
networkx        # 그래프 기반 경로 탐색 (A* 등)
```

#### 최적화 / AI
```
scikit-learn    # 분류(구조물 형식 판정), 클러스터링(정거장 위치)
optuna          # 하이퍼파라미터/파라미터 최적화
deap            # 유전 알고리즘 (Genetic Algorithm)
```

#### 시각화
```
matplotlib      # 종단면도, 정적 차트
plotly          # 인터랙티브 평면·3D 시각화
folium          # 웹 기반 지도 오버레이
pyvista         # 3D 지형 + 노선 시각화 (선택적)
```

#### 보고서 생성
```
openpyxl        # Excel 보고서 작성
reportlab       # PDF 보고서 생성
jinja2          # 보고서 템플릿 렌더링
```

#### 데이터 처리
```
pandas          # 테이블형 데이터 처리
pyyaml          # config YAML 파일 읽기/쓰기
requests        # REST API 호출 (공간정보, 공시지가 등)
owslib          # OGC WMS/WFS 서비스 클라이언트
```

#### LLM 연계 (보고서 텍스트 생성)
```
anthropic       # Claude API 연동
langchain       # LLM Agent 프레임워크 (선택적)
```

---

## 7. 코딩 규칙

### 기본
- Python 3.11+ 문법만 사용
- 모든 함수/메서드에 타입 힌트 필수
- 모든 public 함수에 docstring 작성 (Google 스타일)
- 라인 길이 최대 100자

### 설계기준 파라미터
- 하드코딩 금지: 모든 수치 기준은 `config/design_standards.yaml`에 정의
- 코드에서는 `DesignStandards` 클래스를 통해 참조

### 공간 데이터
- 좌표계: 내부 처리는 EPSG:5186 (한국 중부 좌표계) 통일
- 입출력 시 좌표계 명시 필수: `gdf.crs` 확인 후 변환
- 거리 단위: 미터(m), 각도 단위: 도(degree) 또는 라디안 명시

### 오류 처리
- 사용자 입력 좌표 유효성 검사 (한반도 범위 내 여부 등)
- 데이터 소스 연결 실패 시 fallback 처리 및 로깅
- 설계기준 위반 시 예외(DesignConstraintViolation) 발생 후 상위 처리

### 로깅
- `logging` 모듈 사용, 모듈별 logger 생성
- 레벨: DEBUG(계산 세부), INFO(단계 진행), WARNING(기준 경계), ERROR(실패)

### 파일/경로
- `pathlib.Path` 사용, 문자열 경로 직접 사용 금지
- 데이터 경로는 config 또는 환경변수로 관리

---

## 8. 연동 시스템

### RDBIM
- 노선 좌표 및 구조물 정보를 RDBIM 포맷으로 변환/송출
- `src/integration/rdbim_exporter.py` 담당

### AutoCAD Civil 3D
- Civil 3D API 또는 LandXML 포맷으로 노선 데이터 내보내기
- 평면선형(HAL), 종단선형(VAL), 횡단면 데이터 포함
- `src/integration/civil3d_exporter.py` 담당

### Dynamo
- Civil 3D Dynamo 스크립트 연계: 파라메트릭 노선 모델 자동 생성
- `src/integration/dynamo_bridge.py` 담당

### LandXML
- 국제 표준 노선 데이터 교환 포맷
- 입력(기존 노선 가져오기) 및 출력(타 시스템 송출) 모두 지원

### 향후 연계 (TPS)
- 열차운행 시뮬레이션(TPS) 데이터 연계
- 표정속도, 운행시간 산정 결과 피드백

---

## 9. 테스트 규칙

### 구조
```
tests/
├── unit/
│   ├── test_terrain.py
│   ├── test_obstacles.py
│   ├── test_alignment.py
│   ├── test_optimizer.py
│   ├── test_structure.py
│   ├── test_constraints.py
│   └── test_cost_model.py
├── integration/
│   ├── test_pipeline_end_to_end.py
│   └── test_data_sources.py
└── fixtures/
    ├── sample_dem.tif
    ├── sample_obstacles.geojson
    └── sample_alignment.yaml
```

### 규칙
- 프레임워크: pytest
- 커버리지 목표: 80% 이상 (핵심 계산 모듈 100%)
- 설계기준 검증 테스트: 모든 속도 등급별 경계값 테스트 포함
- GIS 테스트: 실제 데이터 대신 fixture의 소규모 샘플 사용
- 외부 API 호출: `unittest.mock` 또는 `responses` 라이브러리로 모킹
- 테스트 네이밍: `test_<기능>_<조건>_<기대결과>` 형식

### CI 체크 항목
1. `pytest tests/unit/` — 단위 테스트 전체
2. `pytest tests/integration/` — 통합 테스트
3. `mypy src/` — 타입 체크
4. `ruff check src/` — 린트
