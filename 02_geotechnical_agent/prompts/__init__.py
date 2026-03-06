# prompts 패키지
# 지반조사결과 분석 AI Agent 프롬프트 템플릿 모음

from prompts.system_prompt import SYSTEM_PROMPT
from prompts.borehole_analysis import BOREHOLE_EXTRACTION_PROMPT
from prompts.data_integration import DATA_MATCHING_PROMPT, STATISTICS_PROMPT
from prompts.outlier_detection import OUTLIER_CHECK_PROMPT
from prompts.parameter_estimation import PARAMETER_ESTIMATION_PROMPT
from prompts.report_generation import REPORT_PROMPT

__all__ = [
    "SYSTEM_PROMPT",
    "BOREHOLE_EXTRACTION_PROMPT",
    "DATA_MATCHING_PROMPT",
    "STATISTICS_PROMPT",
    "OUTLIER_CHECK_PROMPT",
    "PARAMETER_ESTIMATION_PROMPT",
    "REPORT_PROMPT",
]
