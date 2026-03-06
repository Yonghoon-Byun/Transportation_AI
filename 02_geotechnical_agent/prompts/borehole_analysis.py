BOREHOLE_EXTRACTION_PROMPT = """다음 시추주상도 데이터에서 지반정보를 추출하여 JSON 형식으로 반환하세요.

## 입력 데이터
{input_data}

## 추출 항목

### 기본 정보
- 시추공 번호 (Hole No.)
- 시추 위치 (좌표 또는 측점)
- 시추 심도 (m)
- 조사 일자
- 지하수위 (GL-m)

### 지층 정보 (층별 반복)
- 지층명 (한국어)
- 토질 분류 기호 (USCS)
- 색상
- 상단 심도 (m)
- 하단 심도 (m)
- 두께 (m)

### 표준관입시험 (SPT) 데이터
- 시험 심도 (m)
- N치 (횟수/30cm)
- 관입량 (cm)
- 타격 횟수 분할 (예: 5/8/10)

### 암반 코어 데이터 (해당 시 포함)
- 심도 구간 (m)
- 암종
- 풍화도 (신선암/보통풍화/심한풍화/완전풍화)
- TCR (Total Core Recovery, %)
- RQD (Rock Quality Designation, %)
- 균열 간격 (cm)

## 출력 형식 (JSON)
```json
{{
  "hole_info": {{
    "hole_no": "BH-1",
    "location": "STA. 1+500",
    "total_depth_m": 20.0,
    "survey_date": "2024-01-15",
    "groundwater_level_m": 3.5,
    "ground_elevation_m": 45.2
  }},
  "layers": [
    {{
      "layer_no": 1,
      "soil_name": "매립층",
      "uscs_symbol": "SM",
      "color": "암갈색",
      "top_depth_m": 0.0,
      "bottom_depth_m": 1.5,
      "thickness_m": 1.5,
      "description": "모래 섞인 실트, 느슨한"
    }}
  ],
  "spt_data": [
    {{
      "depth_m": 1.5,
      "n_value": 8,
      "penetration_cm": 30,
      "blow_counts": "3/4/4",
      "layer_no": 1
    }}
  ],
  "core_data": [
    {{
      "top_depth_m": 10.0,
      "bottom_depth_m": 11.5,
      "rock_type": "화강암",
      "weathering_grade": "보통풍화",
      "tcr_percent": 75.0,
      "rqd_percent": 45.0,
      "fracture_spacing_cm": 15.0
    }}
  ],
  "extraction_notes": "추출 시 특이사항 또는 불명확한 항목 기술"
}}
```

## 주의사항
- N치가 50 이상이면 50/n (n=실제 관입량cm)으로 표기 가능: 예) "50/15cm"
- 지하수위가 시추 중 변동된 경우 최저 수위를 기준으로 기록
- 불명확한 데이터는 null로 표시하고 extraction_notes에 기술
- 암반부는 spt_data 대신 core_data에 기록
"""
