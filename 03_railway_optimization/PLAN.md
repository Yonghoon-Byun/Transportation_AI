# 철도 선형 최적화 로직 - 상세 개발 계획

## 1. 프로젝트 개요

### 목적
사업구상/기본계획 단계에서 철도 노선의 평면/종단 선형을 자동으로 생성·최적화하는 AI 기반 시스템 구축.
시/종점 입력부터 최적 노선 대안 도출, 개략 공사비 산출, 기준 적합성 검토, 보고서 자동 작성까지
전 과정을 자동화하여 노선 검토 시간 70% 단축을 목표로 한다.

### 적용 대상
- 철도 종류: 일반철도 (KDS/KR Code), 도시철도
- 설계 단계: 사업구상 단계, 기본계획 단계
- 설계기준: KDS 47 (철도설계기준), KR Code, 필요시 TSI/EN/UIC 참조

### 두 기획서 통합 관점
| 구분 | 철도1부 | 철도2부 |
|------|---------|---------|
| 핵심 | 지장물 인지·회피, 구조물 자동 판정 | 코리더 탐색, 정거장 추천, 환경 필터링 |
| 출력 | RDBIM/Civil3D 데이터 변환 | 개략 공사비, 기준 적합성, 보고서/도면 |
| 알고리즘 | Rule Engine | Physarum + GA + Generative Design |
| 데이터 | 수치지도, 위성영상 | 국가공간정보, OSM, Open Railway Map, WDPA |

---

## 2. 시스템 아키텍처 개요

### 전체 파이프라인
```
[입력] 시/종점 좌표, 설계 조건
    |
    v
[Phase 1] 지형/공간 데이터 처리
  - DEM 로딩 및 전처리
  - 수치지도/위성영상 파싱
  - 지장물 탐지 (건물, 수계, 보호구역)
    |
    v
[Phase 2] 선형 설계 엔진
  - 코리더 탐색 (Physarum 기반)
  - 평면선형 생성 (직선/원곡선/완화곡선)
  - 종단선형 생성 (구배/종곡선)
    |
    v
[Phase 3] 제약조건 엔진
  - KDS/KR Code 룰 엔진
  - 설계기준 적합성 자동 검토
  - 위반 항목 피드백
    |
    v
[Phase 4] 비용 모델
  - 구조물 종류 자동 판정 (토공/교량/터널)
  - 공종별 물량 산출
  - 개략 공사비 산출
    |
    v
[Phase 5] 최적화 알고리즘
  - 다목적 최적화 (비용/환경/운행시간)
  - 대안 노선 생성 및 비교
    |
    v
[Phase 6] 시각화 및 출력
  - 평면도/종단면도 생성
  - 3D 시각화
  - 비교표, 기준 검토표, 보고서 자동 작성
    |
    v
[Phase 7] 외부 연동
  - RDBIM 데이터 변환
  - Civil3D 호환 출력
  - LLM Agent 연동 (보고서 서술)
```

### 폴더 구조
```
03_railway_optimization/
├── src/
│   ├── terrain/            # Phase 1: 지형/공간 데이터 처리
│   │   ├── dem_loader.py
│   │   ├── gis_parser.py
│   │   ├── obstacle_detector.py
│   │   └── spatial_index.py
│   ├── alignment/          # Phase 2: 선형 설계 엔진
│   │   ├── corridor.py
│   │   ├── horizontal.py   # 평면선형
│   │   ├── vertical.py     # 종단선형
│   │   └── alignment_model.py
│   ├── constraints/        # Phase 3: 제약조건 엔진
│   │   ├── rule_engine.py
│   │   ├── kds_rules.py
│   │   ├── checker.py
│   │   └── compliance_report.py
│   ├── cost_model/         # Phase 4: 비용 모델
│   │   ├── structure_classifier.py
│   │   ├── quantity_calculator.py
│   │   ├── unit_cost.py
│   │   └── cost_estimator.py
│   ├── optimizer/          # Phase 5: 최적화 알고리즘
│   │   ├── physarum.py
│   │   ├── genetic.py
│   │   ├── pso.py
│   │   └── multi_objective.py
│   ├── visualizer/         # Phase 6: 시각화/출력
│   │   ├── plan_view.py
│   │   ├── profile_view.py
│   │   ├── viewer_3d.py
│   │   └── report_generator.py
│   └── export/             # Phase 7: 외부 연동
│       ├── rdbim_exporter.py
│       ├── civil3d_exporter.py
│       └── ifc_exporter.py
├── data/                   # 지형 데이터 (gitignore)
│   ├── dem/
│   ├── gis/
│   └── satellite/
├── notebooks/              # 탐색적 분석, 실험
├── tests/                  # pytest 단위/통합 테스트
├── config/
│   ├── design_standards.yaml   # 철도설계기준 파라미터
│   └── unit_costs.yaml         # 공종별 단가 DB
├── requirements.txt
├── CLAUDE.md
└── PLAN.md
```

---

## 3. Phase별 상세 구현 계획

### Phase 1: 지형/공간 데이터 처리
**목표**: 수치지도·DEM·위성영상을 로드하고 지장물 레이어를 생성한다.

#### 태스크
| # | 태스크 | 우선순위 |
|---|--------|---------|
| 1.1 | DEM 로딩·전처리 (rasterio, GDAL) | 필수 |
| 1.2 | 수치지도 파싱 (SHP/GeoJSON → GeoDataFrame) | 필수 |
| 1.3 | 지장물 레이어 구축 (건물, 수계, 보호구역, 도로) | 필수 |
| 1.4 | 공간 인덱스 구축 (rtree/STRtree) | 필수 |
| 1.5 | 위성영상 기반 지장물 인식 (이미지 분류) | 선택 |
| 1.6 | OSM 데이터 연동 | 선택 |

#### 입출력
- 입력: GeoTIFF (DEM), SHP/GeoJSON (수치지도), 시/종점 좌표 (WGS84 or EPSG:5186)
- 출력: `TerrainModel` 객체, `ObstacleLayer` 객체

#### 핵심 클래스/함수 명세
```python
# src/terrain/dem_loader.py
class DEMLoader:
    def load(self, path: str, crs: str = "EPSG:5186") -> DEMData
    def resample(self, resolution_m: float) -> DEMData
    def get_elevation(self, x: float, y: float) -> float
    def get_slope(self, x: float, y: float) -> tuple[float, float]  # (경사도, 방위각)

# src/terrain/gis_parser.py
class GISParser:
    def load_shapefile(self, path: str) -> gpd.GeoDataFrame
    def load_geojson(self, path: str) -> gpd.GeoDataFrame
    def classify_obstacles(self, gdf: gpd.GeoDataFrame) -> ObstacleLayer

# src/terrain/obstacle_detector.py
class ObstacleDetector:
    CATEGORIES = ["building", "water", "protected_area", "road", "quiet_zone"]
    def detect(self, layer: ObstacleLayer, corridor: Polygon) -> list[Obstacle]
    def get_buffer_distance(self, category: str, railway_class: str) -> float
    # 정온시설 이격거리: 주거지역 200m (KDS 기준)
```

#### 테스트
- `tests/test_terrain.py`: DEM 로딩 정확도, 좌표계 변환, 지장물 탐지 유효성

---

### Phase 2: 선형 설계 엔진
**목표**: 코리더 탐색 후 철도 기하 기준에 맞는 평면/종단 선형을 생성한다.

#### 태스크
| # | 태스크 | 우선순위 |
|---|--------|---------|
| 2.1 | 코리더 탐색 (격자 기반 가중치 맵 생성) | 필수 |
| 2.2 | 평면선형 - 직선(Tangent) 계산 | 필수 |
| 2.3 | 평면선형 - 원곡선(Circular Curve) 계산 | 필수 |
| 2.4 | 평면선형 - 완화곡선(Clothoid, 3차 포물선) | 필수 |
| 2.5 | 종단선형 - 구배(Gradient) 최적 배치 | 필수 |
| 2.6 | 종단선형 - 종곡선(Vertical Curve) 계산 | 필수 |
| 2.7 | 선형 연속성/접속 검증 | 필수 |
| 2.8 | 정거장 위치 자동 추천 | 선택 |

#### 입출력
- 입력: `TerrainModel`, `ObstacleLayer`, 시/종점, `DesignStandards`
- 출력: `AlignmentModel` (평면선형 + 종단선형 통합 객체)

#### 핵심 클래스/함수 명세
```python
# src/alignment/horizontal.py
class HorizontalAlignment:
    """평면선형: IP(교각점) 기반 설계"""
    def add_tangent(self, start: Point, end: Point) -> Tangent
    def add_circular_curve(self, radius: float, delta: float) -> CircularCurve
    def add_clothoid(self, A: float) -> Clothoid
    # 클로소이드 파라미터 A = sqrt(R * L)
    def compute_chainages(self) -> list[float]  # 누가거리 계산
    def get_point_at(self, chainage: float) -> Point
    def validate(self, standards: DesignStandards) -> list[Violation]

# src/alignment/vertical.py
class VerticalAlignment:
    """종단선형: VIP(종단교점) 기반 설계"""
    def add_grade(self, start_ch: float, end_ch: float, grade: float) -> Grade
    def add_vertical_curve(self, vip: float, length: float) -> VerticalCurve
    def get_elevation_at(self, chainage: float) -> float
    def validate(self, standards: DesignStandards) -> list[Violation]

# src/alignment/corridor.py
class CorridorSearcher:
    """코리더 탐색: 가중치 격자 + 최단경로"""
    def build_cost_grid(self, terrain: TerrainModel,
                        obstacles: ObstacleLayer) -> np.ndarray
    def search(self, start: Point, end: Point,
               method: str = "physarum") -> list[Point]
    # method: "physarum" | "astar" | "dijkstra"

# src/alignment/alignment_model.py
@dataclass
class AlignmentModel:
    horizontal: HorizontalAlignment
    vertical: VerticalAlignment
    design_speed: float          # km/h
    railway_class: str           # "일반철도" | "도시철도"
    total_length: float          # m
    def to_geojson(self) -> dict
    def to_dataframe(self) -> pd.DataFrame
```

#### 테스트
- `tests/test_alignment.py`: 클로소이드 좌표 수치 검증, 종곡선 최고점/최저점, 누가거리 연속성

---

### Phase 3: 제약조건 엔진
**목표**: KDS/KR Code 설계기준을 룰 엔진으로 구현하고 선형의 기준 적합성을 자동 검토한다.

#### 태스크
| # | 태스크 | 우선순위 |
|---|--------|---------|
| 3.1 | `design_standards.yaml` 파라미터 정의 | 필수 |
| 3.2 | 평면선형 제약 룰 구현 | 필수 |
| 3.3 | 종단선형 제약 룰 구현 | 필수 |
| 3.4 | 이격거리 제약 룰 구현 | 필수 |
| 3.5 | 위반 항목 보고서 생성 | 필수 |
| 3.6 | 룰 엔진 확장 구조 (TSI/EN 추가 대응) | 선택 |

#### 핵심 설계기준 파라미터 (design_standards.yaml 초안)
```yaml
# 일반철도 (설계속도별)
일반철도:
  설계속도:
    - 200: { 최소곡선반경: 1800, 최대구배: 15, 완화곡선최소길이: 130 }
    - 150: { 최소곡선반경: 1000, 최대구배: 20, 완화곡선최소길이: 90 }
    - 120: { 최소곡선반경: 600,  최대구배: 25, 완화곡선최소길이: 70 }
    - 100: { 최소곡선반경: 400,  최대구배: 25, 완화곡선최소길이: 55 }
  # 단위: 반경(m), 구배(‰), 완화곡선(m)
  정온시설_이격거리:
    주거지역: 200    # m
    학교: 300        # m
    병원: 300        # m

도시철도:
  설계속도:
    - 100: { 최소곡선반경: 300, 최대구배: 35, 완화곡선최소길이: 55 }
    - 80:  { 최소곡선반경: 200, 최대구배: 40, 완화곡선최소길이: 40 }
```

#### 핵심 클래스/함수 명세
```python
# src/constraints/rule_engine.py
class RuleEngine:
    def __init__(self, standard_path: str, railway_class: str,
                 design_speed: float): ...
    def load_rules(self) -> list[Rule]
    def check(self, alignment: AlignmentModel) -> ComplianceResult

# src/constraints/kds_rules.py
class MinCurveRadiusRule(Rule):
    def check(self, curve: CircularCurve, speed: float) -> Violation | None

class MaxGradientRule(Rule):
    def check(self, grade: Grade, speed: float) -> Violation | None

class TransitionCurveLengthRule(Rule):
    def check(self, clothoid: Clothoid, speed: float) -> Violation | None

class QuietZoneBufferRule(Rule):
    def check(self, alignment: AlignmentModel,
              obstacles: ObstacleLayer) -> list[Violation]

# src/constraints/compliance_report.py
@dataclass
class ComplianceResult:
    is_compliant: bool
    violations: list[Violation]
    warnings: list[Warning]
    def to_markdown(self) -> str
    def to_dataframe(self) -> pd.DataFrame
```

#### 테스트
- `tests/test_constraints.py`: 각 룰별 경계값 테스트 (위반/통과 경계)

---

### Phase 4: 비용 모델
**목표**: 구조물 종류를 자동 판정하고 공종별 물량 및 개략 공사비를 산출한다.

#### 태스크
| # | 태스크 | 우선순위 |
|---|--------|---------|
| 4.1 | 구조물 자동 판정 (토공/교량/터널) | 필수 |
| 4.2 | 공종별 물량 산출 | 필수 |
| 4.3 | 단가 DB 구축 (unit_costs.yaml) | 필수 |
| 4.4 | 개략 공사비 산출 및 집계 | 필수 |
| 4.5 | 용지보상비 산출 (지가 레이어 연동) | 선택 |

#### 구조물 판정 기준
| 조건 | 판정 |
|------|------|
| 절토고 < 6m, 성토고 < 5m | 토공 |
| 절토고 >= 6m 또는 성토고 >= 5m | 개착(토공 심화 검토) |
| 계곡, 수계 횡단 | 교량 |
| 성토고 >= 10m 이상 지속 | 교량 검토 |
| 산지 관통 (경사 > 30%) | 터널 |

#### 핵심 클래스/함수 명세
```python
# src/cost_model/structure_classifier.py
class StructureClassifier:
    """선형 구간별 구조물 종류 자동 판정"""
    def classify(self, alignment: AlignmentModel,
                 terrain: TerrainModel) -> list[StructureSegment]
    # 반환: [(시점ch, 종점ch, 구조물종류, 절토고, 성토고), ...]

# src/cost_model/quantity_calculator.py
class QuantityCalculator:
    def calc_earthwork(self, segment: StructureSegment) -> dict  # 절토/성토량
    def calc_bridge(self, segment: StructureSegment) -> dict     # 연장, 교폭
    def calc_tunnel(self, segment: StructureSegment) -> dict     # 연장, 단면적

# src/cost_model/unit_cost.py
# unit_costs.yaml 초안
# 토공: 절토 2,000원/m³, 성토 3,500원/m³
# 교량: 600만원/m (단선), 900만원/m (복선)
# 터널: 800만원/m (단선), 1,200만원/m (복선)
# 궤도: 5억원/km (자갈도상), 8억원/km (콘크리트도상)
# 전철전력: 3억원/km

# src/cost_model/cost_estimator.py
class CostEstimator:
    def estimate(self, alignment: AlignmentModel,
                 terrain: TerrainModel) -> CostSummary
    def compare(self, alternatives: list[AlignmentModel]) -> pd.DataFrame

@dataclass
class CostSummary:
    total_cost: float                  # 원
    breakdown: dict[str, float]        # 공종별 세부
    cost_per_km: float
    structure_ratio: dict[str, float]  # 토공/교량/터널 비율
```

#### 테스트
- `tests/test_cost_model.py`: 단순 직선 노선 수치 검증, 구조물 판정 경계값

---

### Phase 5: 최적화 알고리즘
**목표**: 다목적 최적화로 비용·환경·설계기준을 동시에 고려한 최적 노선 대안을 생성한다.

#### 태스크
| # | 태스크 | 우선순위 |
|---|--------|---------|
| 5.1 | Physarum 알고리즘 구현 (코리더 탐색) | 필수 |
| 5.2 | 유전 알고리즘 (GA) - 선형 파라미터 최적화 | 필수 |
| 5.3 | 다목적 최적화 프레임워크 (pymoo NSGA-II) | 필수 |
| 5.4 | 목적함수 정의 (비용, 환경, 운행시간) | 필수 |
| 5.5 | PSO (Particle Swarm Optimization) | 선택 |
| 5.6 | 대안 노선 생성 및 Pareto Front 분석 | 필수 |

#### 목적함수 설계
```
목적함수 1: minimize 총공사비 (CostEstimator 결과)
목적함수 2: minimize 환경영향 (보호구역 교차 길이 + 생태축 교란 지수)
목적함수 3: minimize 표정속도 기반 운행시간 (선택, 향후 TPS 연계)
제약조건:  ComplianceResult.is_compliant == True
```

#### 핵심 클래스/함수 명세
```python
# src/optimizer/physarum.py
class PhysarumOptimizer:
    """점균류(Physarum) 알고리즘: 네트워크 탐색"""
    def __init__(self, cost_grid: np.ndarray, n_agents: int = 100): ...
    def run(self, start: tuple, end: tuple,
            iterations: int = 500) -> list[Point]
    def _update_conductance(self): ...

# src/optimizer/genetic.py
class GeneticAlgorithm:
    """GA: IP 좌표(x,y) 및 반경 파라미터 진화"""
    def __init__(self, population_size: int = 50,
                 mutation_rate: float = 0.1): ...
    def encode(self, alignment: AlignmentModel) -> np.ndarray  # 염색체
    def decode(self, chromosome: np.ndarray) -> AlignmentModel
    def evolve(self, generations: int = 200) -> AlignmentModel

# src/optimizer/multi_objective.py
class MultiObjectiveOptimizer:
    """pymoo NSGA-II 래퍼"""
    def __init__(self, objectives: list[Callable],
                 constraints: list[Callable]): ...
    def optimize(self, n_gen: int = 100) -> ParetoResult

@dataclass
class ParetoResult:
    pareto_front: list[AlignmentModel]
    objective_values: np.ndarray   # (n_solutions, n_objectives)
    def get_best_by_weight(self, weights: list[float]) -> AlignmentModel
    def summary_table(self) -> pd.DataFrame
```

#### 테스트
- `tests/test_optimizer.py`: Physarum 수렴 검증, GA 염색체 인코딩/디코딩, Pareto Front 비지배 검증

---

### Phase 6: 시각화 및 출력
**목표**: 평면도·종단면도·3D 시각화 및 자동 보고서를 생성한다.

#### 태스크
| # | 태스크 | 우선순위 |
|---|--------|---------|
| 6.1 | 평면도 생성 (matplotlib + geopandas) | 필수 |
| 6.2 | 종단면도 생성 (matplotlib) | 필수 |
| 6.3 | 3D 시각화 (pyvista 또는 plotly) | 선택 |
| 6.4 | 대안 비교표 생성 (DataFrame → HTML/Excel) | 필수 |
| 6.5 | 기준 검토표 자동 생성 | 필수 |
| 6.6 | 보고서 자동 작성 (LLM Agent 연동) | 선택 |

#### 핵심 클래스/함수 명세
```python
# src/visualizer/plan_view.py
class PlanViewGenerator:
    def plot(self, alignment: AlignmentModel,
             terrain: TerrainModel,
             obstacles: ObstacleLayer,
             alternatives: list[AlignmentModel] = None) -> plt.Figure
    def export_geojson(self, alignment: AlignmentModel, path: str)

# src/visualizer/profile_view.py
class ProfileViewGenerator:
    """종단면도: 지반고, 계획고, 구조물 구간 표시"""
    def plot(self, alignment: AlignmentModel,
             terrain: TerrainModel) -> plt.Figure
    def annotate_structures(self, segments: list[StructureSegment])

# src/visualizer/report_generator.py
class ReportGenerator:
    def generate_comparison_table(self,
                                  alternatives: list[AlignmentModel],
                                  costs: list[CostSummary]) -> pd.DataFrame
    def generate_compliance_table(self,
                                  results: list[ComplianceResult]) -> pd.DataFrame
    def export_excel(self, path: str)
    def export_markdown(self, path: str)
    # LLM 연동: 표 데이터를 컨텍스트로 보고서 서술 생성 (향후)
```

---

### Phase 7: 외부 연동
**목표**: 설계 결과를 RDBIM/Civil3D/IFC 등 외부 도구와 호환 가능한 형식으로 변환한다.

#### 태스크
| # | 태스크 | 우선순위 |
|---|--------|---------|
| 7.1 | Civil3D LandXML 형식 출력 | 선택 |
| 7.2 | RDBIM 호환 포맷 분석 및 변환기 구현 | 선택 |
| 7.3 | IFC 4.x Rail 스키마 출력 | 선택 |
| 7.4 | Open Railway Map 호환 출력 | 선택 |

#### 핵심 클래스/함수 명세
```python
# src/export/civil3d_exporter.py
class Civil3DExporter:
    """LandXML 형식으로 평면/종단선형 출력"""
    def export(self, alignment: AlignmentModel, path: str) -> None
    def _alignment_to_landxml(self, ha: HorizontalAlignment) -> ET.Element
    def _profile_to_landxml(self, va: VerticalAlignment) -> ET.Element

# src/export/rdbim_exporter.py
class RDBIMExporter:
    """RDBIM 데이터 스키마 변환 (포맷 확인 후 구현)"""
    def export(self, alignment: AlignmentModel,
               structures: list[StructureSegment], path: str) -> None
```

---

## 4. 데이터 흐름도

```
입력 데이터                처리 모듈               중간 산출물
─────────────            ──────────────          ──────────────
GeoTIFF (DEM)     ──►  DEMLoader          ──►  DEMData
SHP/GeoJSON       ──►  GISParser          ──►  ObstacleLayer
시/종점 좌표       ──►  CorridorSearcher   ──►  후보 경로 집합
설계기준 YAML      ──►  RuleEngine         ──►  Rule 객체 목록

후보 경로          ──►  HorizontalAlignment ──►  평면선형
DEMData           ──►  VerticalAlignment   ──►  종단선형
평면+종단          ──►  AlignmentModel     ──►  통합 선형 모델

AlignmentModel    ──►  RuleEngine.check   ──►  ComplianceResult
AlignmentModel    ──►  CostEstimator      ──►  CostSummary
AlignmentModel    ──►  MultiObjectiveOpt  ──►  ParetoResult

ParetoResult      ──►  PlanViewGenerator  ──►  평면도 (PNG/SVG)
                  ──►  ProfileViewGenerator ─►  종단면도
                  ──►  ReportGenerator    ──►  비교표/보고서
                  ──►  Civil3DExporter    ──►  LandXML
```

---

## 5. 기술 스택

| 분류 | 라이브러리 | 용도 |
|------|-----------|------|
| 지형/공간 | rasterio, GDAL, geopandas, shapely | DEM, GIS 처리 |
| 수치계산 | numpy, scipy | 선형 기하, 최적화 |
| 최적화 | pymoo, deap | 다목적 GA, NSGA-II |
| 시각화 | matplotlib, plotly, pyvista | 평면도, 종단도, 3D |
| 데이터 | pandas, openpyxl | 결과 집계, 엑셀 출력 |
| 설정 | pyyaml | design_standards.yaml |
| 테스트 | pytest, pytest-cov | 단위/통합 테스트 |
| XML | lxml | LandXML 출력 |
| LLM (선택) | anthropic SDK 또는 LangChain | 보고서 자동 서술 |

---

## 6. 개발 단계별 일정 (안)

| Phase | 내용 | 예상 기간 | 의존성 |
|-------|------|-----------|--------|
| 1 | 지형/공간 데이터 처리 | 2주 | - |
| 2 | 선형 설계 엔진 | 3주 | Phase 1 |
| 3 | 제약조건 엔진 | 2주 | Phase 2 |
| 4 | 비용 모델 | 2주 | Phase 2, 3 |
| 5 | 최적화 알고리즘 | 3주 | Phase 2, 3, 4 |
| 6 | 시각화 및 출력 | 2주 | Phase 5 |
| 7 | 외부 연동 | 2주 | Phase 6 |

---

## 7. 확인 필요 사항 (미결정)

- [ ] **설계속도 범위**: 최우선 대상 설계속도 (120km/h, 150km/h, 200km/h 중 선택)
- [ ] **복선/단선 기본값**: 물량 산출 기준 (단선 1면 vs 복선 2면)
- [ ] **DEM 해상도**: 확보 가능한 수치고도모델 해상도 (5m, 1m 등)
- [ ] **입력 좌표계**: 기본 좌표계 (EPSG:5186 중부원점 TM 또는 WGS84)
- [ ] **단가 DB 출처**: 건설공사 표준품셈 기준년도, 기본설계 개략 단가 출처
- [ ] **RDBIM 스키마**: RDBIM 데이터 포맷 상세 스펙 문서 확인 필요
- [ ] **환경 영향 지수**: 생태축/WDPA 교차 시 페널티 계량화 방법
- [ ] **TPS 연계 범위**: 표정속도/운행시간 산정을 Phase 내 포함할지 별도 모듈로 분리할지
- [ ] **보고서 언어**: 자동 생성 보고서 한국어 전용 여부
- [ ] **Dynamo/C3D API**: Dynamo 연동은 Phase 7 포함 여부 (라이선스 의존)

---

## 8. 리스크 및 의존성

| 리스크 | 영향 | 대응 |
|--------|------|------|
| GDAL/rasterio Windows 설치 이슈 | 개발 지연 | conda 환경 사용, 사전 환경 구성 문서화 |
| 실제 DEM 데이터 미확보 | Phase 1 테스트 불가 | 공개 SRTM 1arc (30m) 또는 국토지리정보원 샘플 사용 |
| 설계기준 파라미터 오류 | 검토 결과 신뢰성 저하 | 각 룰에 KDS 조항 번호 주석 필수화 |
| Physarum 수렴 불안정 | 탐색 실패 | A* 폴백 경로 병행 구현 |
| pymoo API 변경 | 최적화 모듈 오류 | pymoo==0.6.x 버전 고정 |
| Civil3D/RDBIM 스펙 미확보 | Phase 7 지연 | LandXML 표준(ISO 19141) 먼저 구현 후 대기 |
| LLM 보고서 품질 | 서술 오류 | 사람 검수 단계 명시, 선택 기능으로 분류 |
