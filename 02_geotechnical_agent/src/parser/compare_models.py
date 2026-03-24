"""시추주상도 PDF → 3개 AI 모델 비교 추출 스크립트

동일한 시추주상도 이미지를 Gemini, Claude, GPT-4o에 보내서
추출 결과를 비교합니다.

Usage:
    python src/parser/compare_models.py
"""

import os
import sys
import json
import base64
import time
from pathlib import Path
from dotenv import load_dotenv

# .env 로드
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

# ── 이미지 준비 ──
DOCS_DIR = Path(__file__).resolve().parents[2] / "docs" / "pdf_pages"
IMAGE_FILES = sorted(DOCS_DIR.glob("page_*.png"))  # page_1~4.png (NTB-24)

if not IMAGE_FILES:
    print("ERROR: docs/pdf_pages/page_*.png 파일이 없습니다.")
    sys.exit(1)

print(f"대상 이미지: {len(IMAGE_FILES)}장")
for f in IMAGE_FILES:
    print(f"  - {f.name}")

# ── 공통 프롬프트 ──
SYSTEM_PROMPT = """당신은 지반조사 전문가입니다.
입력된 시추주상도(Drill Log) 이미지에서 데이터를 정확하게 추출하여
정해진 JSON 형식으로 출력합니다.
심도(Depth)를 기준으로 데이터를 매핑하세요.
숫자는 반드시 숫자형으로, 미측정값은 null로 표기하세요."""

USER_PROMPT = """첨부된 시추주상도 이미지(전체 페이지)에서 다음 데이터를 추출하여
아래 JSON 형식으로 정리해주세요. 반드시 JSON만 출력하세요.

```json
{
  "basic_info": {
    "borehole_id": "시추공번",
    "project_name": "건명",
    "x_coord": 0.0,
    "y_coord": 0.0,
    "ground_elevation": 0.0,
    "total_depth": 0.0,
    "groundwater_level": 0.0,
    "drill_date": "YYYY-MM-DD",
    "drill_method": "시추방법",
    "drill_diameter": "공경"
  },
  "layers": [
    {
      "layer_name": "지층명",
      "soil_classification": "토질분류(USCS)",
      "depth_from": 0.0,
      "depth_to": 0.0,
      "thickness": 0.0,
      "color": "색상",
      "description": "상태설명"
    }
  ],
  "spt_records": [
    {
      "depth": 0.0,
      "n_value": 0,
      "penetration_cm": 30,
      "is_refusal": false,
      "layer_name": "해당지층"
    }
  ],
  "rock_core_records": [
    {
      "depth_from": 0.0,
      "depth_to": 0.0,
      "tcr_percent": 0.0,
      "rqd_percent": 0.0,
      "joint_sets": 0,
      "fracture_zone": "파쇄대 심도 또는 null",
      "remarks": "비고"
    }
  ],
  "tunnel_info": {
    "tunnel_start_depth": 0.0,
    "tunnel_start_elevation": 0.0,
    "tunnel_end_depth": 0.0
  }
}
```"""


def encode_image(path: Path) -> str:
    """이미지를 base64로 인코딩."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def extract_json_from_text(text: str) -> dict | None:
    """응답 텍스트에서 JSON 부분만 추출."""
    # ```json ... ``` 블록 추출
    import re
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # 전체가 JSON인 경우
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # { ... } 블록 추출
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ════════════════════════════════════════════════════════
#  1. Gemini API (google-genai)
# ════════════════════════════════════════════════════════

def run_gemini(model_id: str = "gemini-2.5-flash", model_label: str = "Gemini 2.5 Flash"):
    """Gemini 모델로 추출."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not found"}

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # 이미지 파트 구성
    image_parts = []
    for img_path in IMAGE_FILES:
        img_data = encode_image(img_path)
        image_parts.append(
            types.Part.from_bytes(
                data=base64.b64decode(img_data),
                mime_type="image/png"
            )
        )

    all_parts = image_parts + [types.Part.from_text(text=USER_PROMPT)]

    print(f"\n[{model_label}] 요청 중...")
    start = time.time()

    response = client.models.generate_content(
        model=model_id,
        contents=[types.Content(role="user", parts=all_parts)],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
        )
    )

    elapsed = time.time() - start
    text = response.text
    result = extract_json_from_text(text)

    print(f"[{model_label}] 완료 ({elapsed:.1f}초)")
    return {
        "model": model_label,
        "elapsed_sec": round(elapsed, 1),
        "raw_text": text,
        "parsed_json": result,
        "success": result is not None
    }


# ════════════════════════════════════════════════════════
#  2. Claude API (anthropic)
# ════════════════════════════════════════════════════════

def run_claude():
    """Claude Sonnet 4로 추출."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not found"}

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    # 이미지 콘텐츠 구성
    content = []
    for img_path in IMAGE_FILES:
        img_data = encode_image(img_path)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": img_data
            }
        })
    content.append({"type": "text", "text": USER_PROMPT})

    print("\n[Claude Sonnet 4] 요청 중...")
    start = time.time()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
        temperature=0.1,
    )

    elapsed = time.time() - start
    text = response.content[0].text
    result = extract_json_from_text(text)

    print(f"[Claude Sonnet 4] 완료 ({elapsed:.1f}초)")
    return {
        "model": "Claude Sonnet 4",
        "elapsed_sec": round(elapsed, 1),
        "raw_text": text,
        "parsed_json": result,
        "success": result is not None,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


# ════════════════════════════════════════════════════════
#  3. GPT-4o API (openai)
# ════════════════════════════════════════════════════════

def run_gpt4o():
    """GPT-4o로 추출."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not found"}

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    # 이미지 콘텐츠 구성
    content = []
    for img_path in IMAGE_FILES:
        img_data = encode_image(img_path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_data}",
                "detail": "high"
            }
        })
    content.append({"type": "text", "text": USER_PROMPT})

    print("\n[GPT-4o] 요청 중...")
    start = time.time()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ],
        max_tokens=8192,
        temperature=0.1,
    )

    elapsed = time.time() - start
    text = response.choices[0].message.content
    result = extract_json_from_text(text)

    print(f"[GPT-4o] 완료 ({elapsed:.1f}초)")
    return {
        "model": "GPT-4o",
        "elapsed_sec": round(elapsed, 1),
        "raw_text": text,
        "parsed_json": result,
        "success": result is not None,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
    }


# ════════════════════════════════════════════════════════
#  비교 분석
# ════════════════════════════════════════════════════════

def compare_results(results: list[dict]):
    """3개 모델 결과를 비교 테이블로 출력."""
    print("\n" + "=" * 80)
    print("  시추주상도 NTB-24 — 3개 AI 모델 추출 결과 비교")
    print("=" * 80)

    # 기본 성능
    print(f"\n{'모델':<20} {'소요시간':>10} {'JSON파싱':>10} {'입력토큰':>10} {'출력토큰':>10}")
    print("-" * 65)
    for r in results:
        if "error" in r:
            print(f"{r.get('model', '?'):<20} {'ERROR':>10}")
            continue
        inp = r.get("input_tokens", "-")
        out = r.get("output_tokens", "-")
        print(f"{r['model']:<20} {r['elapsed_sec']:>8.1f}s {'성공' if r['success'] else '실패':>10} {str(inp):>10} {str(out):>10}")

    # 추출 데이터 비교
    print(f"\n{'항목':<25}", end="")
    for r in results:
        if "error" not in r:
            print(f" {r['model']:<22}", end="")
    print()
    print("-" * (25 + 23 * len([r for r in results if "error" not in r])))

    # basic_info 비교
    fields = [
        ("시추공번", "basic_info.borehole_id"),
        ("X좌표", "basic_info.x_coord"),
        ("Y좌표", "basic_info.y_coord"),
        ("시추표고", "basic_info.ground_elevation"),
        ("시추심도", "basic_info.total_depth"),
        ("지하수위", "basic_info.groundwater_level"),
    ]

    for label, path in fields:
        print(f"{label:<25}", end="")
        for r in results:
            if "error" in r or not r.get("parsed_json"):
                print(f" {'N/A':<22}", end="")
                continue
            keys = path.split(".")
            val = r["parsed_json"]
            for k in keys:
                val = val.get(k, "N/A") if isinstance(val, dict) else "N/A"
            print(f" {str(val):<22}", end="")
        print()

    # 지층 수
    print(f"{'지층 수':<25}", end="")
    for r in results:
        if "error" in r or not r.get("parsed_json"):
            print(f" {'N/A':<22}", end="")
            continue
        layers = r["parsed_json"].get("layers", [])
        print(f" {len(layers):<22}", end="")
    print()

    # SPT 수
    print(f"{'SPT N치 측정점 수':<25}", end="")
    for r in results:
        if "error" in r or not r.get("parsed_json"):
            print(f" {'N/A':<22}", end="")
            continue
        spt = r["parsed_json"].get("spt_records", [])
        print(f" {len(spt):<22}", end="")
    print()

    # TCR/RQD 수
    print(f"{'TCR/RQD 런 수':<25}", end="")
    for r in results:
        if "error" in r or not r.get("parsed_json"):
            print(f" {'N/A':<22}", end="")
            continue
        rock = r["parsed_json"].get("rock_core_records", [])
        print(f" {len(rock):<22}", end="")
    print()

    # 터널 정보
    print(f"{'터널 시점 심도':<25}", end="")
    for r in results:
        if "error" in r or not r.get("parsed_json"):
            print(f" {'N/A':<22}", end="")
            continue
        ti = r["parsed_json"].get("tunnel_info", {})
        val = ti.get("tunnel_start_depth", "N/A")
        print(f" {str(val):<22}", end="")
    print()

    print("\n" + "=" * 80)


def save_results(results: list[dict]):
    """결과를 JSON 및 마크다운 파일로 저장."""
    output_dir = Path(__file__).resolve().parents[2] / "docs"

    # JSON 저장 (raw_text 제외한 요약)
    summary = []
    for r in results:
        entry = {k: v for k, v in r.items() if k != "raw_text"}
        summary.append(entry)

    json_path = output_dir / "model_comparison_result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nJSON 저장: {json_path}")

    # 마크다운 비교 보고서 저장
    md_lines = [
        "# 시추주상도 NTB-24 — AI 모델별 추출 결과 비교\n",
        "| 항목 | 내용 |",
        "|---|---|",
        "| 대상 | NTB-24 시추주상도 (4페이지) |",
        f"| 비교일 | {time.strftime('%Y-%m-%d')} |",
        "| 비교 모델 | " + ", ".join(r["model"] for r in results if "error" not in r) + " |",
        "",
        "---",
        "",
        "## 1. 성능 비교",
        "",
        "| 모델 | 소요시간 | JSON 파싱 | 입력 토큰 | 출력 토큰 |",
        "|---|---|---|---|---|",
    ]

    for r in results:
        if "error" in r:
            md_lines.append(f"| {r.get('model', '?')} | ERROR | - | - | - |")
            continue
        inp = r.get("input_tokens", "-")
        out = r.get("output_tokens", "-")
        md_lines.append(
            f"| {r['model']} | {r['elapsed_sec']}초 | "
            f"{'성공' if r['success'] else '실패'} | {inp} | {out} |"
        )

    md_lines += ["", "---", "", "## 2. 추출 데이터 비교", ""]

    # 기본정보 비교표
    md_lines += [
        "### 2.1 기본정보",
        "",
        "| 항목 | " + " | ".join(r["model"] for r in results if "error" not in r) + " |",
        "|---" + "|---" * len([r for r in results if "error" not in r]) + "|",
    ]

    fields = [
        ("시추공번", "basic_info.borehole_id"),
        ("X좌표", "basic_info.x_coord"),
        ("Y좌표", "basic_info.y_coord"),
        ("시추표고(m)", "basic_info.ground_elevation"),
        ("시추심도(m)", "basic_info.total_depth"),
        ("지하수위(m)", "basic_info.groundwater_level"),
        ("조사일", "basic_info.drill_date"),
    ]

    for label, path in fields:
        row = f"| {label} "
        for r in results:
            if "error" in r or not r.get("parsed_json"):
                row += "| N/A "
                continue
            keys = path.split(".")
            val = r["parsed_json"]
            for k in keys:
                val = val.get(k, "N/A") if isinstance(val, dict) else "N/A"
            row += f"| {val} "
        row += "|"
        md_lines.append(row)

    # 지층 비교
    md_lines += ["", "### 2.2 지층 구성", ""]
    for r in results:
        if "error" in r or not r.get("parsed_json"):
            continue
        md_lines.append(f"**{r['model']}:**")
        md_lines.append("")
        md_lines.append("| 지층명 | 심도 상단(m) | 심도 하단(m) | 두께(m) | 토질분류 |")
        md_lines.append("|---|---|---|---|---|")
        for layer in r["parsed_json"].get("layers", []):
            md_lines.append(
                f"| {layer.get('layer_name', '')} "
                f"| {layer.get('depth_from', '')} "
                f"| {layer.get('depth_to', '')} "
                f"| {layer.get('thickness', '')} "
                f"| {layer.get('soil_classification', '')} |"
            )
        md_lines.append("")

    # SPT N치 비교
    md_lines += ["### 2.3 SPT N치", ""]
    for r in results:
        if "error" in r or not r.get("parsed_json"):
            continue
        md_lines.append(f"**{r['model']}:**")
        md_lines.append("")
        md_lines.append("| 심도(m) | N치 | 관입량(cm) | 반발 | 지층 |")
        md_lines.append("|---|---|---|---|---|")
        for spt in r["parsed_json"].get("spt_records", []):
            md_lines.append(
                f"| {spt.get('depth', '')} "
                f"| {spt.get('n_value', '')} "
                f"| {spt.get('penetration_cm', '')} "
                f"| {'반발' if spt.get('is_refusal') else '-'} "
                f"| {spt.get('layer_name', '')} |"
            )
        md_lines.append("")

    # TCR/RQD 비교
    md_lines += ["### 2.4 TCR/RQD (암반구간)", ""]
    for r in results:
        if "error" in r or not r.get("parsed_json"):
            continue
        md_lines.append(f"**{r['model']}:**")
        md_lines.append("")
        md_lines.append("| 구간 상단(m) | 구간 하단(m) | TCR(%) | RQD(%) | 절리세트 | 파쇄대 |")
        md_lines.append("|---|---|---|---|---|---|")
        for rc in r["parsed_json"].get("rock_core_records", []):
            md_lines.append(
                f"| {rc.get('depth_from', '')} "
                f"| {rc.get('depth_to', '')} "
                f"| {rc.get('tcr_percent', '')} "
                f"| {rc.get('rqd_percent', '')} "
                f"| {rc.get('joint_sets', '')} "
                f"| {rc.get('fracture_zone', '') or '-'} |"
            )
        md_lines.append("")

    # 터널 정보
    md_lines += ["### 2.5 터널구간", ""]
    md_lines.append("| 항목 | " + " | ".join(r["model"] for r in results if "error" not in r) + " |")
    md_lines.append("|---" + "|---" * len([r for r in results if "error" not in r]) + "|")

    for label, key in [("시점 심도(m)", "tunnel_start_depth"), ("시점 표고(m)", "tunnel_start_elevation"), ("종점 심도(m)", "tunnel_end_depth")]:
        row = f"| {label} "
        for r in results:
            if "error" in r or not r.get("parsed_json"):
                row += "| N/A "
                continue
            ti = r["parsed_json"].get("tunnel_info", {})
            row += f"| {ti.get(key, 'N/A')} "
        row += "|"
        md_lines.append(row)

    md_lines += ["", "---", "", "*본 비교는 동일 프롬프트·동일 이미지로 수행되었습니다.*"]

    md_path = output_dir / "모델별_추출결과_비교.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"마크다운 저장: {md_path}")

    # 각 모델 raw_text도 개별 저장
    for r in results:
        if "error" in r:
            continue
        name = r["model"].replace(" ", "_").replace(".", "")
        raw_path = output_dir / f"raw_{name}.txt"
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(r.get("raw_text", ""))
        print(f"원본 응답 저장: {raw_path}")


# ════════════════════════════════════════════════════════
#  메인 실행
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  시추주상도 NTB-24 — 3개 AI 모델 비교 추출")
    print("  Gemini 2.5 Flash / Claude Sonnet 4 / GPT-4o")
    print("=" * 60)

    results = []

    # 1. Gemini Flash
    try:
        results.append(run_gemini("gemini-2.5-flash", "Gemini 2.5 Flash"))
    except Exception as e:
        print(f"[Gemini Flash] 오류: {e}")
        results.append({"model": "Gemini 2.5 Flash", "error": str(e)})

    # 1b. Gemini Pro
    try:
        results.append(run_gemini("gemini-2.5-pro", "Gemini 2.5 Pro"))
    except Exception as e:
        print(f"[Gemini Pro] 오류: {e}")
        results.append({"model": "Gemini 2.5 Pro", "error": str(e)})

    # 2. Claude
    try:
        results.append(run_claude())
    except Exception as e:
        print(f"[Claude] 오류: {e}")
        results.append({"model": "Claude Sonnet 4", "error": str(e)})

    # 3. GPT-4o
    try:
        results.append(run_gpt4o())
    except Exception as e:
        print(f"[GPT-4o] 오류: {e}")
        results.append({"model": "GPT-4o", "error": str(e)})

    # 비교 출력
    compare_results(results)

    # 결과 저장
    save_results(results)

    print("\n완료!")
