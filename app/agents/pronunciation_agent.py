import json
from typing import Dict, Any
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result
from app.agents.base_agent import BaseGeminiAgent, is_error_result

class PronunciationAgent(BaseGeminiAgent):
    SCHEMA = {
        "type": "object",
        "properties": {
            "transcription": {"type": "string", "description": "학생이 실제로 발음한 것으로 인식된 문장 텍스트"},
            "score": {"type": "integer", "description": "0~100점 사이의 종합 발음/억양 점수"},
            "feedback": {"type": "string", "description": "어느 부분의 강세나 발음이 어색했는지 친절하게 알려주는 한국어 피드백"}
        },
        "required": ["transcription", "score", "feedback"]
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_result(is_error_result), retry_error_callback=lambda rs: rs.outcome.result())
    def evaluate_pronunciation(self, audio_bytes: bytes, target_sentence: str, target_language: str, mime_type: str = "audio/wav") -> Dict[str, Any]:
        prompt = f"""
        당신은 언어를 가르치는 외국어 과외 선생님입니다.
        다음 오디오를 듣고 학생의 발음을 평가하세요.
        목표 언어: {target_language}
        목표 문장: "{target_sentence}"
        
        학생이 목표 문장을 얼마나 정확하게 발음했는지 평가하고 점수와 피드백을 제공하세요.
        학생이 전혀 엉뚱한 말을 했다면 점수를 낮게 주고 다시 시도하라고 피드백하세요.
        """
        client = self.get_client()
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=self.SCHEMA,
                    temperature=0.2
                )
            )
            return json.loads(response.text)
        except Exception as e:
            return {"transcription": "", "score": 0, "feedback": f"평가 중 오류가 발생했습니다: {str(e)}"}

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """사용자의 음성을 텍스트로 변환합니다."""
        client = self.get_client()
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    "이 오디오에 담긴 사람의 말을 텍스트로 정확하게 받아적기. 다른 말은 덧붙이지 말고 오직 받아적은 텍스트만 출력해."
                ],
                config=types.GenerateContentConfig(
                    temperature=0.0
                )
            )
            return response.text.strip()
        except Exception as e:
            return f"[음성 인식 실패: {str(e)}]"
