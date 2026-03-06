PARAMETER_ESTIMATION_PROMPT = """지층별 통계 데이터와 시험 결과를 바탕으로 적용 분야별 설계지반정수를 산정하세요.

## 입력 데이터

### 지층별 통계
{layer_statistics}

### 이상치 처리 결과
{outlier_results}

### 적용 분야
{application_type}

## 설계지반정수 산정 원칙

### 대표값 선정 방법
- **평균값**: 파괴확률이 낮은 설계 (50% 신뢰수준)
- **평균 - 1σ**: 일반 설계 (84% 신뢰수준, 권장)
- **평균 - 2σ**: 중요 구조물 (97.7% 신뢰수준)
- COV > 30%인 경우 보수적 값(평균 - 1.5σ) 적용

### N치로부터 지반정수 추정 경험식

**내부마찰각 φ (모래, 자갈)**
- Meyerhof(1956): φ = 28° + N/5 (N ≤ 10), φ = 30° + N/10 (10 < N ≤ 30)
- Peck et al.(1974): φ = 28.5° + 12.2log(N) (사질토)
- Dunham(1954): φ = √(12N) + 15° (모래)

**비배수 전단강도 Su (점성토)**
- Terzaghi & Peck: Su = N/8 (kPa) [N: 타격횟수/30cm]
- Hara et al.(1974): Su = 29N^0.72 (kPa)

**탄성계수 E (MPa)**
- 모래: E = 0.5~1.0 × N (MPa)
- 점토: E = 3~8 × qu (kPa → MPa)

**허용지지력 qa (kPa)**
- 모래: qa = 12N (얕은기초, 침하량 25mm 기준)
- 점토: qa = qu/3 (kPa)

## 적용 분야별 필요 정수 목록

### 1. 비탈면 안정 해석
```
필요 정수:
- 단위중량 γt (kN/m³): 전체 단위중량
- 점착력 c' (kPa): 유효응력 기준
- 내부마찰각 φ' (°): 유효응력 기준
- 비배수 전단강도 Su (kPa): 점성토, 단기 안정 검토
- 잔류 전단강도 cr', φr': 기존 활동면 재활동 검토
```

### 2. 기초 설계 (얕은기초)
```
필요 정수:
- 단위중량 γt (kN/m³)
- 점착력 c (kPa)
- 내부마찰각 φ (°)
- 탄성계수 E (MPa): 침하량 계산
- 포아송비 ν: 침하량 계산
- 압밀 관련 정수 (점성토): Cc, Cs, Pc'
```

### 3. 깊은기초 (말뚝)
```
필요 정수:
- N치 분포: 선단지지력 계산
- 단위주면마찰력 fs (kPa): 지층별
- 단위선단지지력 qp (kPa)
- 비배수 전단강도 Su (kPa): 점성토
```

### 4. 흙막이 구조물
```
필요 정수:
- 단위중량 γt (kN/m³)
- 점착력 c (kPa)
- 내부마찰각 φ (°)
- 정지토압계수 K0
- 탄성계수 E (MPa): 지반반력계수 계산
- 지반반력계수 kh (kN/m³)
```

### 5. 터널 (NATM)
```
필요 정수:
- 탄성계수 E (MPa) 또는 변형계수 Em
- 포아송비 ν
- 단위중량 γt (kN/m³)
- 점착력 c (kPa), 내부마찰각 φ (°)
- RMR, Q값: 지보 패턴 결정
- 지반반력계수
```

### 6. 연약지반 처리
```
필요 정수:
- 비배수 전단강도 Su (kPa): 초기 안정 검토
- 압밀 관련: Cc, Cs, Cv, Pc'
- 투수계수 k (m/s)
- 선행압밀압력 Pc' (kPa)
- 과압밀비 OCR
```

## 출력 형식 (JSON)
```json
{{
  "design_parameters": [
    {{
      "layer_name": "풍화토",
      "uscs_symbol": "SM",
      "depth_range_m": [5.0, 12.5],
      "application": "{application_type}",
      "parameters": {{
        "unit_weight_kNm3": {{
          "recommended": 19.0,
          "range": [18.0, 20.0],
          "basis": "시험값 평균 18.8 kN/m³, 안전측 적용",
          "reliability_level": "84%"
        }},
        "cohesion_kPa": {{
          "recommended": 5.0,
          "range": [0.0, 10.0],
          "basis": "삼축압축시험(UU) 평균 5.0 kPa, COV=30% → 평균값 적용",
          "reliability_level": "50%"
        }},
        "friction_angle_deg": {{
          "recommended": 30.0,
          "range": [27.0, 33.0],
          "basis": "삼축압축시험(UU) 평균 31.2° - 1.0σ(2.8°) = 28.4° → 절삭 30°",
          "reliability_level": "84%",
          "estimation_formula": "실험값 기준"
        }},
        "elastic_modulus_MPa": {{
          "recommended": 18.5,
          "range": [10.0, 30.0],
          "basis": "N평균=18.5 → E = 1.0 × N = 18.5 MPa (Bowles, 1996)",
          "reliability_level": "추정값"
        }}
      }},
      "data_adequacy": "적정 (n=12, COV<35%)",
      "special_notes": "COV 상대적으로 높아 설계 시 보수적 값 적용 권장"
    }}
  ],
  "estimation_summary": {{
    "application_type": "비탈면 안정",
    "design_standard": "KDS 11 70 05",
    "analysis_method": "평균 - 1σ (84% 신뢰수준)",
    "outlier_handling": "BH-3 7.5m N=38 제외 후 통계 적용",
    "limitations": [
      "역학시험 데이터 부족 (n<5): 일부 지층 경험식 추정",
      "연약층 압밀 데이터 없음 → 장기침하 검토 불가"
    ],
    "recommendations": [
      "풍화토 구간 추가 삼축압축시험 실시 권장",
      "중요 비탈면 구간 역해석을 통한 강도정수 검증"
    ]
  }}
}}
```

## 산정 시 유의사항
1. 경험식 적용 시 사용된 식과 출처를 반드시 basis 필드에 명시
2. 데이터 수 n < 5인 경우 통계적 신뢰성 낮음을 명시
3. 중요 구조물(1등급 도로, 장대터널 등)은 higher reliability level 적용
4. 적용 분야가 여러 개인 경우 각각 별도 산정
"""
