import os
from google import genai
from typing import Optional

def is_error_result(result):
    if not isinstance(result, dict):
        return False
    if "error" in result:
        return True
    if "transcription" in result and result.get("score") == 0 and "오류가 발생했습니다" in result.get("feedback", ""):
        return True
    return False

class BaseGeminiAgent:
    _client = None

    @classmethod
    def get_client(cls, api_key: Optional[str] = None):
        if cls._client is None:
            key = api_key or os.environ.get("GEMINI_API_KEY", "")
            if key:
                cls._client = genai.Client(api_key=key)
        return cls._client
