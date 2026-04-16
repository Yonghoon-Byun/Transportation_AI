# KTDB 통합 분석 에이전트 (v2 - Google Sheets 기반)

## 프로젝트 개요
KTDB(국가교통DB) 데이터를 Google Sheets에서 읽어와 Gemini AI로 자연어 분석하는 Streamlit 웹 애플리케이션.
사용자가 자연어로 질문하면 AI가 적합한 시트를 자동 선택하고, 데이터 분석 결과를 표+텍스트로 반환한다.

원본 레포: `https://github.com/transoksun/KTDB_report_agent`
상위 프로젝트: `Transportation_AI` (교통부문 AI 개발)
이전 버전: `01_ktdb/` (PostgreSQL DB 기반)

## 핵심 기능
1. **Google Sheets 데이터 연동**: gspread + 서비스 계정 인증으로 4종 시트 실시간 조회
2. **AI 시트 자동 선택**: 사용자 질문을 분석하여 적합한 시트/탭 자동 라우팅
3. **자연어 분석**: Gemini 1.5 Flash로 질문 → 분석 요약 + CSV 표 생성
4. **연도 보간**: 배포 연도 외 입력 시 선형보간법 자동 적용
5. **지역 필터링**: 시도/시군구 단위 필터 지원
6. **CSV 다운로드**: 분석 결과를 CSV로 즉시 내려받기

## 데이터 소스 (Google Sheets)

| 데이터 | 시트 키 | URL |
|--------|---------|-----|
| 사회경제지표 | `SHEET_URL_SOCIO` | https://docs.google.com/spreadsheets/d/1pWLPhj2uz8auxsNIEuT2ovaD-xT7lzYkdgwN3i8Y4Wg/edit |
| 목적OD | `SHEET_URL_OBJ_OD` | https://docs.google.com/spreadsheets/d/1du90sQtkdm5OyIx92XhmYAEhb_wpt07elm2jOSZP5Qk/edit |
| 주수단OD | `SHEET_URL_MAIN_OD` | https://docs.google.com/spreadsheets/d/1E5tZKWv970J2soQ2n3K8jgz_RPgNPOpHXcuzhbBd3u0/edit |
| 접근수단OD | `SHEET_URL_ACC_OD` | https://docs.google.com/spreadsheets/d/1lHAuh2sHE2vcbNCW-eajBF60gqy4Yy6yy-zQOnD1uhQ/edit |

### 시트별 탭 구성

| 시트 | 탭 코드 | 설명 |
|------|---------|------|
| 사회경제지표 | ZONE | 존체계(행정구역) |
| | POP_TOT | 총 인구수 |
| | POP_YNG | 5-24세 인구수 |
| | POP_15P | 15세이상 인구수 |
| | EMP | 취업자수 |
| | STU | 수용학생수 |
| | WORK_TOT | 종사자수 |
| 목적OD | PUR_{연도} | 목적OD (2023/2025/2030/2035/2040/2045/2050년) |
| 주수단OD | MOD_{연도} | 주수단OD (2023/2025/2030/2035/2040/2045/2050년) |
| 접근수단OD | ATTMOD_2023 | 접근수단OD (2023년) |

### 배포 연도
`2023, 2025, 2030, 2035, 2040, 2045, 2050` (7개 연도)

### 데이터 단위
- 사회경제지표: 명
- 목적OD / 주수단OD / 접근수단OD: 통행/일

## 시스템 아키텍처
```
[Google Sheets 4종]
       |
   [gspread + 서비스계정 인증]
       |
   [Streamlit App]
       |
   ┌───┴───┐
   |       |
[사이드바]  [채팅 UI]
 시도/시군구   질문 입력
 연도 선택       |
 시트 선택   [AI 라우팅] ← Gemini (시트 자동 선택)
       |       |
   [데이터 로드 + 전처리]
   · 지역 필터링
   · 숫자 변환
   · 연도 보간
       |
   [Gemini 분석]
   · SYSTEM_PROMPT 기반
   · 데이터 150행 샘플 전달
       |
   [결과 출력]
   · 요약 텍스트 + CSV 표
   · CSV 다운로드 버튼
```

## 파일 구조
```
04_ktdb_new/
├── CLAUDE.md              # 프로젝트 문서 (본 파일)
├── streamlit_app.py       # 메인 앱 (단일 파일)
├── requirements.txt       # Python 의존성
└── .streamlit/
    └── secrets.toml       # API 키, 시트 URL, GCP 서비스 계정 (gitignore 대상)
```

## 기술 스택
- **언어**: Python 3.11+
- **프론트엔드**: Streamlit
- **AI/LLM**: Google Gemini 1.5 Flash (`google-generativeai`)
- **데이터**: Google Sheets (`gspread`, `st-gsheets-connection`)
- **인증**: GCP 서비스 계정 (OAuth2)
- **데이터 처리**: pandas

## 설정 (secrets.toml)
```toml
GEMINI_API_KEY = "..."

SHEET_URL_SOCIO   = "https://docs.google.com/spreadsheets/d/..."
SHEET_URL_OBJ_OD  = "https://docs.google.com/spreadsheets/d/..."
SHEET_URL_MAIN_OD = "https://docs.google.com/spreadsheets/d/..."
SHEET_URL_ACC_OD  = "https://docs.google.com/spreadsheets/d/..."

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

## 실행 방법
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 컬럼 매핑 (영문 코드 → 한글)

| 코드 | 한글 | 비고 |
|------|------|------|
| SIDO | 시도 | |
| SIGU | 시군구 | |
| ZONE | 존번호 | |
| ORGN | 발생존 | OD 데이터 |
| DEST | 도착존 | OD 데이터 |
| WORK | 출근 | 목적 |
| SCHO | 등교 | 목적 |
| BUSI | 업무 | 목적 |
| HOME | 귀가 | 목적 |
| OTHE | 기타 | 목적 |
| AUTO | 승용차 | 수단 |
| OBUS | 버스 | 수단 |
| SUBW | 지하철 | 수단 |
| RAIL | 일반철도 | 수단 |
| ERAI | 고속철도 | 수단 |

## 개발 규칙
- secrets.toml은 절대 커밋하지 않음 (.gitignore 대상)
- 데이터 단위(명, 통행/일)를 항상 표에 명시
- AI 프롬프트에서 실제 데이터에 없는 수치를 생성하지 않도록 제어
- 보간 연도는 `*(보간)` 주석 표기

## 01_ktdb와의 관계
| 구분 | 01_ktdb (이전) | 04_ktdb_new (현재) |
|------|---------------|-------------------|
| 데이터 저장소 | PostgreSQL (Azure) | Google Sheets |
| 데이터 규모 | ~9,300만 행 | 250존 기준 요약 데이터 |
| AI 모델 | OpenAI (Text-to-SQL) | Gemini 1.5 Flash |
| 분석 방식 | SQL 쿼리 생성 | 데이터 직접 전달 + 분석 |
| 인프라 | DB 서버 필요 | 서버리스 (Sheets + Streamlit) |
| 적합 용도 | 대용량 정밀 분석 | 경량 빠른 프로토타입 |
