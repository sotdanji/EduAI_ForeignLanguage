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
           - 줄바꿈과 문단 형태를 최대한 보존하세요.
        3. 표(Table) 인식: 원본 이미지에 표가 있다면, 절대로 무시하지 말고 Markdown 표 형식(|---|---|)으로 완벽하게 변환하여 텍스트에 포함하세요.
        4. 그림/사진(Image) 인식: 원본 이미지에 시각적 요소(사진, 삽화, 그래프 등)가 있다면, 해당 위치에 `[그림/사진 묘사: (그림이 나타내는 상황이나 내용에 대한 상세한 한국어 묘사)]` 라는 텍스트 태그를 대신 삽입하여 시각 자료가 존재함을 알려주세요.
        5. 다단(Multi-column) 편집 문서 인식: 2단 또는 다단으로 편집된 시험지나 유인물의 경우, 절대로 가로로 가로질러(좌우를 섞어서) 읽지 마세요! 반드시 왼쪽 단(Column)의 텍스트를 위에서 아래로 끝까지 다 읽은 후에, 오른쪽 단(Column)의 텍스트를 위에서 아래로 읽어나가는 순서(Top-to-Bottom, Left-to-Right by column)로 추출하세요. 문제 번호와 보기의 흐름이 끊기지 않게 논리적인 순서를 유지해야 합니다.
        
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
