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
            "document_type": {
                "type": "string",
                "description": "문서의 성격 분류. 다음 중 하나여야 함: 'reading' (일반 독해 지문), 'test_paper' (시험지, 문제 포함), 'handout' (해설이나 문법 설명이 포함된 유인물), 'ambiguous' (판단하기 모호함), 'irrelevant' (학습과 무관한 사진이나 의미없는 텍스트)"
            },
            "is_meaningful_content": {
                "type": "boolean",
                "description": "학습에 사용 가능한 의미 있는 외국어 자료인지 여부. 낙서, 단순 풍경 사진, 의미 없는 문자열 등은 false."
            },
            "reasoning": {
                "type": "string",
                "description": "왜 이렇게 분류했는지에 대한 짧은 판단 이유."
            }
        },
        "required": ["title", "document_type", "is_meaningful_content", "reasoning"]
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_result(is_error_result))
    def analyze_document_intent(self, input_data: Union[str, Any], input_type: str = "image") -> Dict[str, Any]:
        prompt = """
        당신은 AI 외국어 학습 시스템의 데이터를 1차적으로 검증하는 '분석 전처리관(Gatekeeper)'입니다.
        주어진 입력 자료(텍스트 또는 이미지)를 빠르게 스캔하여 문서의 성격을 분류하세요.
        
        [판단 기준]
        1. 학습 자료로서의 가치 (is_meaningful_content): 아무 의미 없는 텍스트(예: "ㅁㄴㅇㄹ", "aaaa")나 외국어 학습과 전혀 무관한 사진인 경우 false를 반환하세요.
        2. 문서 종류 (document_type):
           - reading: 단순한 외국어 독해 지문이나 대화문
           - test_paper: 문제 번호, 객관식 보기, 서술형 문항 등이 포함된 시험지
           - handout: 독해 지문뿐만 아니라, 선생님의 한글 해설, 문법 설명, 빈칸 뚫기 등이 섞인 학습 유인물
           - irrelevant: 학습과 무관한 쓰레기값 (is_meaningful_content가 false일 때)
           - ambiguous: 위 기준 중 어느 것인지 명확히 판단하기 어려울 때
        3. 문서 제목 (title): 문서 상단이나 눈에 띄는 제목(단원명, 시험 이름 등)이 있다면 그대로 추출하세요. 지문 내의 소제목이 아니라 전체 프린트물의 제목을 뜻합니다. 없으면 빈 문자열을 반환하세요.
        
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
