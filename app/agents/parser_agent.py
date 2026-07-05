import os
import json
from google.genai import types
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result
from app.agents.base_agent import BaseGeminiAgent, is_error_result

class ParserAgent(BaseGeminiAgent):
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "source_language": {
                "type": "string",
                "description": "추출된 본문의 원본 언어 코드를 ISO 639-1 형식(예: 'en', 'ja', 'zh', 'ko', 'es' 등)으로 반환하세요."
            },
            "target_language": {
                "type": "string",
                "description": "본문을 번역한 목표 언어 코드를 ISO 639-1 형식(예: 'ko', 'en' 등)으로 반환하세요."
            },
            "title": {"type": "string", "description": "지문의 핵심 주제나 제목을 해당 외국어(혹은 원어)로 요약 (최대 5단어)"},
            "type": {"type": "string", "description": "'reading' 또는 'dialogue' 중 하나"},
            "contents": {
                "type": "array",
                "description": "본문의 문장 단위 분할 데이터",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_text": {"type": "string", "description": "원문 문장"},
                        "target_text": {"type": "string", "description": "해당 문장의 목표 언어 번역 (원문과 목표 언어가 같다면 자연스럽게 다듬은 문장)"},
                        "speaker_gender": {"type": "string", "description": "문장의 화자 성별 ('male', 'female', 'neutral' 중 하나)"},
                        "speaker_name": {"type": "string", "description": "대화문(dialogue)인 경우 화자의 이름 (예: 'A', 'B', 'John' 등). 대화문이 아니라면 빈 문자열"}
                    },
                    "required": ["source_text", "target_text", "speaker_gender", "speaker_name"]
                }
            },
            "vocabulary": {
                "type": "array",
                "description": "핵심 단어 5개",
                "items": {
                    "type": "object",
                    "properties": {
                        "word": {"type": "string", "description": "원문 언어의 단어"},
                        "meaning": {"type": "string", "description": "목표 언어로 된 뜻"}
                    },
                    "required": ["word", "meaning"]
                }
            },
            "original_questions": {
                "type": "array",
                "description": "이미지나 텍스트 원본에 포함되어 있던 기존 문제들 (없으면 빈 배열 반환)",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_number": {"type": "string", "description": "문제 번호 (예: '1', '2-1')"},
                        "question_text": {"type": "string", "description": "문제 지문"}
                    },
                    "required": ["question_number", "question_text"]
                }
            },
            "tutor_feedback": {
                "type": "string",
                "description": "학생의 필기나 오답 체크가 있을 경우, 왜 틀렸는지 친절하게 해설하는 튜터 피드백. 필기/문제가 없으면 빈 문자열."
            }
        },
        "required": ["source_language", "target_language", "title", "type", "contents", "vocabulary", "original_questions", "tutor_feedback"]
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_result(is_error_result))
    def parse_from_text(self, text: str, extract_original_questions: bool = True, student_level: str = "중학교 1학년", target_language: str = "한국어", translation_style: str = "자연스러운 번역 (의역)", translation_tone: str = "경어체 (~해요)") -> Dict[str, Any]:
        original_questions_instruction = (
            "본문 하단이나 주변에 연습문제, 객관식 보기, 혹은 학습용 과제(Task)가 있다면 이를 찾아 'original_questions' 배열에 추출하세요.\n"
            "       **[주의]** 만약 하나의 공통 지시문 아래에 여러 하위 문제가 있다면, 절대로 하나로 뭉뚱그리지 말고 **각각의 하위 문제를 개별적인 배열 객체(독립된 문제)로 분리**하세요."
            if extract_original_questions else
            "'original_questions' 배열은 빈 배열([])로 반환하세요. 이미지 내에 연습문제가 있어도 무시하세요."
        )
        style_instruction = (
            "**[자연스러운 번역]** 번역 시 AI 특유의 기계적이고 딱딱한 번역투를 절대 사용하지 마세요. 마치 원어민이 일상에서 대화하듯 매우 자연스럽고 생동감 넘치는 어휘와 표현으로 번역하세요."
            if "자연스러운" in translation_style else
            "**[문법 중심 직역]** 학생이 외국어 문장 구조와 문법을 명확히 파악할 수 있도록, 의역을 배제하고 원래의 어순과 뼈대를 최대한 살려 직역하세요."
        )
        tone_instruction = (
            "**[경어체 사용]** 전체적인 문맥이나 해설, 일반 독해 지문 번역 시 '~해요', '~습니다' 등 친절하고 다정한 존댓말을 기본으로 사용하세요."
            if "경어체" in translation_tone else
            "**[평어체 사용]** 전체적인 문맥이나 해설, 일반 독해 지문 번역 시 '~한다', '~이다' 등 교과서나 일기장처럼 평범한 반말을 기본으로 사용하세요."
        )
        
        prompt = f"""
        당신은 엘리트 외국어 선생님입니다. 
        현재 지도하는 학생의 수준은 '{student_level}'입니다.
        제공된 텍스트를 분석하세요.
        1. 원본 본문(Reading)이나 대화문(Dialogue) 부분만 추출하여 문장 단위로 분할(contents)하고 '{target_language}'(으)로 번역하세요. 만약 원본과 '{target_language}'이(가) 동일하다면 번역 대신 원문을 문맥에 맞게 다듬어 제공하세요. 페이지 번호 등은 무시하세요.
           {style_instruction}
           {tone_instruction}
           **[대화문 어조 예외 처리]** 대화문일 경우, 전체 문맥을 먼저 파악하여 화자와 청자의 최종적인 관계(예: 친구, 사제지간, 어른과 아이 등) 파악하세요. 각 등장인물별로 상대방에게 쓰는 어조(존댓말 또는 반말)를 관계에 맞게 결정하고 일관성을 유지하세요. 이 경우에는 위의 [경어체/평어체] 기본 설정보다 **등장인물 간의 관계**를 무조건 최우선으로 반영해야 합니다.
           화자를 분석하여 'speaker_gender'를 'male', 'female', 'neutral'(해설자 등) 중 하나로 정확히 매핑하세요.
        2. {original_questions_instruction}
        3. 중요 어휘 5개를 추출하세요. 추출 시 반드시 '{student_level}' 수준에 맞는 어휘를 우선적으로 타겟팅하세요.
        
        출력은 반드시 제공된 JSON Schema를 엄격하게 따르는 유효한 JSON 형식이어야 합니다.
        """
        client = self.get_client()
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[text, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=self.RESPONSE_SCHEMA,
                    temperature=0.2,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e), "raw_response": getattr(response, 'text', '') if 'response' in locals() else ''}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_result(is_error_result))
    def parse_from_image(self, image_part, extract_original_questions: bool = True, student_level: str = "중학교 1학년", target_language: str = "한국어", translation_style: str = "자연스러운 번역 (의역)", translation_tone: str = "경어체 (~해요)") -> Dict[str, Any]:
        original_questions_instruction = (
            "본문 하단이나 주변에 연습문제, 객관식 보기, 혹은 학습용 과제(Task)가 있다면 이를 찾아 'original_questions' 배열에 추출하세요.\n"
            "       **[주의]** 만약 하나의 공통 지시문 아래에 여러 하위 문제가 있다면, 절대로 하나로 뭉뚱그리지 말고 **각각의 하위 문제를 개별적인 배열 객체(독립된 문제)로 분리**하세요."
            if extract_original_questions else
            "'original_questions' 배열은 빈 배열([])로 반환하세요. 이미지 내에 연습문제가 있어도 무시하세요."
        )
        style_instruction = (
            "**[자연스러운 번역]** 번역 시 AI 특유의 기계적이고 딱딱한 번역투를 절대 사용하지 마세요. 마치 원어민이 일상에서 대화하듯 매우 자연스럽고 생동감 넘치는 어휘와 표현으로 번역하세요."
            if "자연스러운" in translation_style else
            "**[문법 중심 직역]** 학생이 외국어 문장 구조와 문법을 명확히 파악할 수 있도록, 의역을 배제하고 원래의 어순과 뼈대를 최대한 살려 직역하세요."
        )
        tone_instruction = (
            "**[경어체 사용]** 전체적인 문맥이나 해설, 일반 독해 지문 번역 시 '~해요', '~습니다' 등 친절하고 다정한 존댓말을 기본으로 사용하세요."
            if "경어체" in translation_tone else
            "**[평어체 사용]** 전체적인 문맥이나 해설, 일반 독해 지문 번역 시 '~한다', '~이다' 등 교과서나 일기장처럼 평범한 반말을 기본으로 사용하세요."
        )
        
        prompt = f"""
        당신은 엘리트 외국어 선생님입니다. 
        현재 지도하는 학생의 수준은 '{student_level}'입니다.
        제공된 교재 이미지를 분석하세요.
        1. 원본 본문(Reading)이나 대화문(Dialogue) 부분만 추출하여 문장 단위로 분할(contents)하고 '{target_language}'(으)로 번역하세요. 만약 원본과 '{target_language}'이(가) 동일하다면 번역 대신 원문을 문맥에 맞게 다듬어 제공하세요. 페이지 번호 등은 무시하세요.
           {style_instruction}
           {tone_instruction}
           **[대화문 어조 예외 처리]** 대화문일 경우, 전체 문맥을 먼저 파악하여 화자와 청자의 최종적인 관계(예: 친구, 사제지간, 어른과 아이 등) 파악하세요. 각 등장인물별로 상대방에게 쓰는 어조(존댓말 또는 반말)를 관계에 맞게 결정하고 일관성을 유지하세요. 이 경우에는 위의 [경어체/평어체] 기본 설정보다 **등장인물 간의 관계**를 무조건 최우선으로 반영해야 합니다.
           화자를 분석하여 'speaker_gender'를 'male', 'female', 'neutral'(해설자 등) 중 하나로 정확히 매핑하세요.
        2. {original_questions_instruction}
        3. 중요 어휘 5개를 추출하세요. 추출 시 반드시 '{student_level}' 수준에 맞는 어휘를 우선적으로 타겟팅하세요.
        4. **[필기 및 맥락(Crop) 분석 - 핵심 임무]** 
           - 이미지에 **학생의 손글씨(필기)나 오답 체크 표시**가 있다면, 이를 반드시 인식하여 학생이 왜 틀렸는지 그 맥락을 분석하고 `tutor_feedback` 필드에 교정 피드백을 작성하세요.
           - 이미지가 문서 전체가 아니라 **특정 문장이나 문제만 부분 캡처(Crop)**된 것이라면, 학생이 그 부분을 몰라서 묻는 의도로 간주하고 `tutor_feedback`에 해당 구문의 핵심 문법이나 문제 풀이 전략을 과외 선생님처럼 친절하게 해설해주세요. 해설의 깊이와 문법 용어는 반드시 '{student_level}'이(가) 쉽게 이해할 수 있는 수준으로 맞추세요.
        
        출력은 반드시 제공된 JSON Schema를 엄격하게 따르는 유효한 JSON 형식이어야 합니다.
        """
        client = self.get_client()
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[image_part, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=self.RESPONSE_SCHEMA,
                    temperature=0.2,
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e), "raw_response": getattr(response, 'text', '') if 'response' in locals() else ''}
