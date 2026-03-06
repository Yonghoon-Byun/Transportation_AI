# Transportation AI - 교통부문 AI 개발

교통부문 AI 개발 프로젝트 모노레포. 3개 서브 프로젝트를 병렬로 개발합니다.

## 서브 프로젝트

| # | 프로젝트 | 폴더 | 설명 |
|---|---------|------|------|
| 1 | KTDB 교통데이터 분석 | `01_ktdb/` | 국가교통DB 데이터 수집/분석/시각화 |
| 2 | 도로부 지반조사 분석 Agent | `02_geotechnical_agent/` | 지반조사결과 자동 분석 AI Agent |
| 3 | 철도 선형 최적화 | `03_railway_optimization/` | 철도 노선 선형 최적화 로직 개발 |

## 개발 환경

- Python 3.11+
- 각 서브 프로젝트는 독립적인 가상환경 사용
- 각 폴더에서 병렬 Claude Code 세션으로 개발

## 프로젝트 구조

```
Transportation_AI/
├── 01_ktdb/                    # KTDB 교통데이터 분석
├── 02_geotechnical_agent/      # 도로부 지반조사 분석 Agent
├── 03_railway_optimization/    # 철도 선형 최적화
├── shared/                     # 공통 유틸리티
└── docs/                       # 전체 프로젝트 문서
```
