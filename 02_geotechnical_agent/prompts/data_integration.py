DATA_MATCHING_PROMPT = """물리시험 결과와 역학시험 결과를 시추공 번호(Hole No.)와 심도(Depth)를 기준으로 매칭하여 통합 데이터셋을 생성하세요.

## 입력 데이터

### 시추주상도 지층 정보
{borehole_layers}

### 물리시험 결과 (입도분석, Atterberg 한계, 비중)
{physical_test_data}

### 역학시험 결과 (일축압축, 삼축압축, 직접전단, 압밀)
{mechanical_test_data}

## 매칭 규칙
1. **1차 매칭 기준**: Hole No. 완전 일치
2. **2차 매칭 기준**: 시료 채취 심도가 해당 지층의 심도 범위 내에 포함될 것
   - 허용 오차: ±0.5m (주상도와 시험 심도 불일치 시)
3. **지층 귀속**: 매칭된 지층 번호(layer_no)와 지층명을 부여
4. **미매칭 처리**: 매칭 불가 데이터는 unmatched 목록으로 분리하여 기술

## 출력 형식 (JSON)
```json
{{
  "integrated_data": [
    {{
      "hole_no": "BH-1",
      "sample_depth_m": 3.0,
      "layer_no": 2,
      "soil_name": "퇴적층",
      "uscs_symbol": "CL",
      "physical_tests": {{
        "gravel_percent": 2.0,
        "sand_percent": 25.0,
        "silt_percent": 45.0,
        "clay_percent": 28.0,
        "d50_mm": 0.05,
        "liquid_limit_percent": 42.0,
        "plastic_limit_percent": 22.0,
        "plasticity_index": 20.0,
        "specific_gravity": 2.70,
        "natural_water_content_percent": 35.0,
        "unit_weight_kNm3": 18.5
      }},
      "mechanical_tests": {{
        "ucs_kPa": null,
        "cohesion_kPa": 18.0,
        "friction_angle_deg": 24.0,
        "test_type": "삼축압축(UU)",
        "compression_index_Cc": 0.35,
        "recompression_index_Cs": 0.04,
        "preconsolidation_pressure_kPa": 85.0,
        "coefficient_of_consolidation_cm2s": 2.1e-4
      }},
      "spt_n_value": 8,
      "match_quality": "exact"
    }}
  ],
  "unmatched": [
    {{
      "source": "mechanical_test",
      "hole_no": "BH-3",
      "depth_m": 7.5,
      "reason": "해당 심도에 시추공 BH-3 주상도 없음"
    }}
  ],
  "matching_summary": {{
    "total_physical_tests": 25,
    "total_mechanical_tests": 18,
    "matched_count": 38,
    "unmatched_count": 5,
    "match_rate_percent": 88.4
  }}
}}
```

## 주의사항
- 동일 심도에 복수의 시험 결과가 있을 경우 모두 포함하고 test_type으로 구분
- match_quality: "exact"(오차 0), "approximate"(±0.5m 이내), "manual"(수동 검토 필요)
- 시험 항목이 없는 경우 해당 필드는 null로 표시
"""

STATISTICS_PROMPT = """통합된 지반조사 데이터에서 지층별 통계량을 계산하세요.

## 입력 데이터
{integrated_data}

## 계산 항목

### 지층별 필수 통계
각 지층(soil_name + uscs_symbol 기준)에 대해 다음을 계산합니다:

**물리적 특성**
- 자연함수비 (wn, %): 평균, 표준편차, 최소, 최대, 데이터 수
- 단위중량 (γt, kN/m³): 평균, 표준편차, 최소, 최대
- 액성한계 (LL, %): 평균, 표준편차 (세립토만 해당)
- 소성지수 (PI, %): 평균, 표준편차 (세립토만 해당)
- 입도 (모래/실트/점토 비율, %): 평균

**역학적 특성**
- N치: 평균, 표준편차, 최소, 최대, 데이터 수, COV(변동계수, %)
- 일축압축강도 (qu, kPa): 평균, 표준편차 (세립토/암반)
- 점착력 (c, kPa): 평균, 표준편차
- 내부마찰각 (φ, °): 평균, 표준편차
- 압축지수 (Cc): 평균 (점성토만)
- 압밀계수 (cv, cm²/s): 평균 (점성토만)

## 출력 형식 (JSON)
```json
{{
  "layer_statistics": [
    {{
      "soil_name": "풍화토",
      "uscs_symbol": "SM",
      "sample_count": 12,
      "depth_range_m": [5.0, 12.5],
      "physical": {{
        "water_content": {{"mean": 22.5, "std": 4.2, "min": 15.0, "max": 31.0, "n": 12}},
        "unit_weight": {{"mean": 18.8, "std": 0.8, "min": 17.5, "max": 20.2, "n": 10}},
        "liquid_limit": null,
        "plasticity_index": null
      }},
      "mechanical": {{
        "spt_n": {{"mean": 18.5, "std": 7.2, "min": 8, "max": 35, "n": 24, "cov_percent": 38.9}},
        "cohesion_kPa": {{"mean": 5.0, "std": 2.5, "min": 0.0, "max": 10.0, "n": 6}},
        "friction_angle_deg": {{"mean": 31.2, "std": 2.8, "min": 27.0, "max": 36.0, "n": 6}},
        "ucs_kPa": null,
        "compression_index": null,
        "consolidation_coeff": null
      }},
      "remarks": "COV > 30%로 데이터 산포 큼. 이상치 검토 권장."
    }}
  ],
  "overall_summary": {{
    "total_boreholes": 10,
    "total_samples": 85,
    "identified_layers": 5,
    "analysis_date": "{analysis_date}"
  }}
}}
```

## 통계 계산 주의사항
- 데이터 수(n) 3개 미만인 경우 통계적 대표성 부족 경고 표시
- COV > 30%: 데이터 산포 과다로 이상치 검토 필요 표시
- null 값은 통계 계산에서 제외
- 암반 지층은 RQD, TCR 통계도 추가로 계산
"""
