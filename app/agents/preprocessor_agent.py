import os
import json
from google.genai import types
from typing import Dict, Any, Union
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result
from app.agents.base_agent import BaseGeminiAgent, is_error_result

class PreprocessorAgent(BaseGeminiAgent):
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "문서의 상단이나 핵심 텍스트를 파악하여 추출한 문서 제목 (예: '2023학년도 1학기 중간고사 영어', 'Chapter 1. Hello World'). 찾을 수 없으면 빈 문자열 반환."
            },
            "raw_text": {
                "type": "string",
                "description": "자료에 포함된 순수 원본 텍스트. [중요] 한글로 된 지시문, 문제 번호, 보기 등도 절대 삭제하지 말고 보이는 글자 그대로 모두 추출하세요. 문단 바꿈(엔터)도 최대한 유지하세요."
            }
        },
        "required": ["title", "raw_text"]
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_result(is_error_result), retry_error_callback=lambda rs: rs.outcome.result())
    def analyze_document_intent(self, input_data: Union[str, Any], input_type: str = "image") -> Dict[str, Any]:
        prompt = """
        당신은 AI 외국어 학습 시스템의 텍스트 추출을 담당하는 '전처리관(Preprocessor)'입니다.
        주어진 텍스트나 이미지를 스캔하여 모든 글자를 빠짐없이 그대로 추출하세요.
        
        [수행 지침]
        1. 문서 제목 (title): 문서 상단이나 눈에 띄는 제목(단원명, 시험 이름 등)이 있다면 추출. (없으면 빈 문자열)
        2. 원문 추출 (raw_text): 자료에 포함된 '모든 글자'를 번역이나 요약 없이 원본 그대로 추출하세요.
           - [가장 중요] 시험지의 한글 지시문("다음 문장 중 어법상 틀린 것은?"), 보기 번호(①, ②), 선택지 등도 외국어가 아니라고 무시하지 말고 무조건 원본 그대로 포함해서 추출하세요!
           - [멀티모달 인식] 지문 중간에 **그림, 사진, 도표** 등이 포함되어 있다면 무시하지 마세요. 해당 위치에 `[그림: (그림에 대한 간단하고 명확한 한글 묘사)]` 형식으로 삽입하세요. (예: `[그림: 웃고 있는 두 학생의 사진]`)
           - [표 데이터] **표(Table)** 가 포함된 경우, 각 행과 열의 정보를 읽기 쉬운 줄글이나 '항목: 내용' 형식으로 풀어서 추출하세요. (복잡한 마크다운 표 형식은 피해주세요)
           - 줄바꿈과 문단 형태를 최대한 보존하세요.
        
        결과는 반드시 제공된 JSON Schema에 맞게 반환해야 합니다.
        """
        
        client = self.get_client()
        try:
            if input_type == "text":
                contents = [f"입력 텍스트: {input_data}", prompt]
            else:
                contents = [input_data, prompt]
                
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=self.RESPONSE_SCHEMA,
                    temperature=0.1,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e), "raw_response": getattr(response, 'text', '') if 'response' in locals() else ''}
