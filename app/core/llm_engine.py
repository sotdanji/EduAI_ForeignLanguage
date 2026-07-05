import os
import json
from google import genai
from google.genai import types
from typing import Optional, Dict, Any

# 설정: 환경변수에서 API 키 로드
client = None

def configure_gemini(api_key: Optional[str] = None):
    global client
    if api_key:
        client = genai.Client(api_key=api_key)
    else:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

# 응답 강제를 위한 JSON 스키마
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
                    "question_text": {"type": "string", "description": "원본 문제의 발문 (예: 다음 글의 주제로 가장 적절한 것은?)"},
                    "options": {"type": "array", "items": {"type": "string"}, "description": "원본 문제의 보기들"},
                    "answer": {"type": "integer", "description": "지문을 바탕으로 AI가 추론한 정답의 보기 인덱스(0부터 시작). 주관식이나 정답을 도저히 알 수 없는 경우 0"}
                },
                "required": ["question_text", "options", "answer"]
            }
        },
        "tutor_feedback": {
            "type": "string",
            "description": "학생의 필기(손글씨) 오답 흔적이 있거나, 부분 캡처(Crop)된 특정 문장/문제에 대해 묻는 의도가 파악될 경우, 해당 부분에 대한 엘리트 과외 선생님의 맞춤형 해설과 문법/오답 피드백을 목표 언어(또는 주로 사용하는 언어)로 친절하게 제공합니다. 필기나 특별한 캡처 의도가 없다면 빈 문자열을 반환하세요."
        }
    },
    "required": ["source_language", "target_language", "title", "type", "contents", "vocabulary", "original_questions", "tutor_feedback"]
}

def get_parsed_content_from_text(text: str, extract_original_questions: bool = True, student_level: str = "중학교 1학년", target_language: str = "한국어") -> Dict[str, Any]:
    """텍스트를 입력받아 파싱된 JSON 객체를 반환합니다."""
    
    original_questions_instruction = (
        """텍스트 내에 기존 한국어 문제 지시문이나 보기(예: 수능/내신 문제, Activity 등)가 있다면 지우지 말고 'original_questions' 배열에 원형 그대로 추출하세요. 객관식일 경우 보기를 options에 배열로 넣고, 지문을 바탕으로 정답을 유추하여 'answer' 필드에 0부터 시작하는 인덱스를 넣으세요. T/F 문제라면 options를 ["T", "F"]로 만들고 해당하는 인덱스를 고르세요. 
       **[주의]** 만약 하나의 공통 지시문(예: '일치하면 T, 아니면 F') 아래에 1번, 2번, 3번 등 여러 개의 하위 문제가 딸려 있다면, 절대로 하나로 뭉뚱그리지 말고 **각각의 하위 문제를 개별적인 배열 객체(독립된 문제)로 분리**하세요. 이때 각 개별 문제의 `question_text`에는 '공통 지시문'과 '해당 하위 문제의 예문'을 결합해서 작성해야 합니다. (예: "다음 문장이 일치하면 T, 아니면 F: In-ho wants to be a scientist.") 만약 문제가 없다면 빈 배열([])을 반환하세요."""
        if extract_original_questions else
        "'original_questions' 배열은 빈 배열([])로 반환하세요. 텍스트 내에 연습문제가 있어도 무시하세요."
    )
    
    prompt = f"""
    당신은 엘리트 외국어 선생님입니다. 
    현재 지도하는 학생의 수준은 '{student_level}'입니다.
    아래 텍스트를 분석하세요.
    1. '원본 텍스트'만 추출하여 문장 단위로 분할(contents)하고, '{target_language}'(으)로 자연스럽게 번역하세요. 만약 원본과 '{target_language}'이(가) 동일하다면 번역 대신 원문을 문맥에 맞게 다듬어 제공하세요.
       **[I'm not AI 번역 스킬 적용]** 번역 시 AI 특유의 기계적이고 딱딱한 번역투를 절대 사용하지 마세요. 마치 원어민이 일상에서 대화하듯 매우 자연스럽고 생동감 넘치는 어휘와 표현으로 번역하세요.
       **[어조 일관성 유지]** 대화문일 경우, 전체 문맥을 먼저 파악하여 화자와 청자의 최종적인 관계(예: 친구, 사제지간, 어른과 아이 등)를 파악하세요. 각 등장인물별로 상대방에게 쓰는 어조(존댓말 또는 반말)를 관계에 맞게 결정하고, 해당 인물이 그 상대방에게 말할 때는 처음부터 끝까지 일관된 어조를 유지하세요. 예를 들어 어른은 아이에게 반말, 아이는 어른에게 존댓말을 쓰며, 서로 또래 친구라면 둘 다 처음부터 끝까지 반말로 번역해야 합니다. 대화 도중 정체를 깨닫거나 상황이 변하더라도 처음 선택한 각 화자의 어조를 절대 바꾸지 마세요.
       화자를 분석하여 'speaker_gender'를 'male', 'female', 'neutral'(해설자 등) 중 하나로 정확히 매핑하세요. 대화문일 경우 인물의 이름이나 문맥을 통해 성별을 추론하세요.
    2. {original_questions_instruction}
    3. 중요 어휘 5개를 추출하세요. 추출 시 반드시 '{student_level}' 수준에 맞는 어휘를 우선적으로 타겟팅하세요.
    
    출력은 반드시 제공된 JSON Schema를 엄격하게 따르는 유효한 JSON 형식이어야 합니다.
    
    [입력 텍스트]
    {text}
    """
    
    if client is None:
        configure_gemini()
        
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                temperature=0.2,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e), "raw_response": getattr(response, 'text', '') if 'response' in locals() else ''}

def get_parsed_content_from_image(image_part, extract_original_questions: bool = True, student_level: str = "중학교 1학년", target_language: str = "한국어") -> Dict[str, Any]:
    """이미지 객체를 입력받아 파싱된 JSON 객체를 반환합니다."""
    
    original_questions_instruction = (
        """이미지 내에 학원 시험지나 교과서의 기존 한국어 문제(지시문, 보기 등, Activity 등)가 포함되어 있다면, 절대 무시하지 말고 'original_questions' 배열에 원형 그대로 추출하세요. 객관식일 경우 보기를 options에 배열로 넣고, 지문을 바탕으로 정답을 유추하여 'answer' 필드에 0부터 시작하는 인덱스를 넣으세요. T/F 문제라면 options를 ["T", "F"]로 만들고 해당하는 인덱스를 고르세요. 
       **[주의]** 만약 하나의 공통 지시문 아래에 여러 하위 문제가 있다면, 절대로 하나로 뭉뚱그리지 말고 **각각의 하위 문제를 개별적인 배열 객체(독립된 문제)로 분리**하세요."""
        if extract_original_questions else
        "'original_questions' 배열은 빈 배열([])로 반환하세요. 이미지 내에 연습문제가 있어도 무시하세요."
    )
    
    prompt = f"""
    당신은 엘리트 외국어 선생님입니다. 
    현재 지도하는 학생의 수준은 '{student_level}'입니다.
    제공된 교재 이미지를 분석하세요.
    1. 원본 본문(Reading)이나 대화문(Dialogue) 부분만 추출하여 문장 단위로 분할(contents)하고 '{target_language}'(으)로 번역하세요. 만약 원본과 '{target_language}'이(가) 동일하다면 번역 대신 원문을 문맥에 맞게 다듬어 제공하세요. 페이지 번호 등은 무시하세요.
       **[I'm not AI 번역 스킬 적용]** 번역 시 AI 특유의 기계적이고 딱딱한 번역투를 절대 사용하지 마세요. 마치 원어민이 일상에서 대화하듯 매우 자연스럽고 생동감 넘치는 어휘와 표현으로 번역하세요.
       **[어조 일관성 유지]** 대화문일 경우, 전체 문맥을 먼저 파악하여 화자와 청자의 최종적인 관계(예: 친구, 사제지간, 어른과 아이 등) 파악하세요. 각 등장인물별로 상대방에게 쓰는 어조(존댓말 또는 반말)를 관계에 맞게 결정하고, 해당 인물이 그 상대방에게 말할 때는 처음부터 끝까지 일관된 어조를 유지하세요.
       화자를 분석하여 'speaker_gender'를 'male', 'female', 'neutral'(해설자 등) 중 하나로 정확히 매핑하세요.
    2. {original_questions_instruction}
    3. 중요 어휘 5개를 추출하세요. 추출 시 반드시 '{student_level}' 수준에 맞는 어휘를 우선적으로 타겟팅하세요.
    4. **[필기 및 맥락(Crop) 분석 - 핵심 임무]** 
       - 이미지에 **학생의 손글씨(필기)나 오답 체크 표시**가 있다면, 이를 반드시 인식하여 학생이 왜 틀렸는지 그 맥락을 분석하고 `tutor_feedback` 필드에 교정 피드백을 작성하세요.
       - 이미지가 문서 전체가 아니라 **특정 문장이나 문제만 부분 캡처(Crop)**된 것이라면, 학생이 그 부분을 몰라서 묻는 의도로 간주하고 `tutor_feedback`에 해당 구문의 핵심 문법이나 문제 풀이 전략을 과외 선생님처럼 친절하게 해설해주세요. 해설의 깊이와 문법 용어는 반드시 '{student_level}'이(가) 쉽게 이해할 수 있는 수준으로 맞추세요.
    
    출력은 반드시 제공된 JSON Schema를 엄격하게 따르는 유효한 JSON 형식이어야 합니다.
    """
    
    if client is None:
        configure_gemini()
        
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                temperature=0.2,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e), "raw_response": getattr(response, 'text', '') if 'response' in locals() else ''}

def get_tutor_chat_response(chat_history: list, parsed_data: Dict[str, Any], mode: str = "qa", student_level: str = "중학교 1학년") -> str:
    """사용자의 질문에 대해 본문 문맥(parsed_data)을 기반으로 AI 튜터가 답변을 생성합니다."""
    
    # 1. 컨텍스트 구성
    context_str = "다음은 현재 학생이 학습 중인 외국어 본문과 관련 데이터입니다:\n\n"
    
    title = parsed_data.get("title", "")
    if title:
        context_str += f"제목: {title}\n"
    
    contents = parsed_data.get("contents", [])
    if contents:
        context_str += "본문:\n"
        for i, line in enumerate(contents):
            context_str += f"[{i+1}] {line.get('source_text', '')} ({line.get('target_text', '')})\n"
            
    vocab = parsed_data.get("vocabulary", [])
    if vocab:
        context_str += "\n단어:\n"
        for v in vocab:
            context_str += f"- {v.get('word', '')}: {v.get('meaning', '')}\n"
            
    tutor_feedback = parsed_data.get("tutor_feedback", "")
    if tutor_feedback:
        context_str += f"\n기존 제공된 선생님 피드백:\n{tutor_feedback}\n"
            
    if mode == "qa":
        system_instruction = f"""당신은 친절하고 전문적인 엘리트 외국어 과외 선생님입니다.
현재 지도하는 학생의 수준은 '{student_level}'입니다.
학생이 학습 중인 위 지문과 단어, 피드백을 완벽히 숙지하고 있습니다.
학생이 지문이나 외국어에 대해 질문을 하면, 진짜 선생님처럼 다정하고 이해하기 쉽게 답변해주세요.
절대 딱딱한 기계나 AI처럼 말하지 말고, 사람처럼 자연스러운 한국어(해요체/합쇼체)로 답변하세요. 해설의 깊이, 문법 용어의 사용 여부, 어투는 반드시 '{student_level}'에 완벽하게 맞추세요. (예: 초등학생에게는 매우 쉽고 다정하게, 고등학생에게는 수능/내신 중심의 성숙한 어투로)

[학습 컨텍스트]
{context_str}
"""
    elif mode == "interview":
        system_instruction = f"""당신은 날카롭지만 따뜻한 소크라테스식 인터뷰어이자 과외 선생님입니다.
현재 지도하는 학생의 수준은 '{student_level}'입니다.
학생이 학습 중인 위 지문과 단어, 피드백을 완벽히 숙지하고 있습니다.

당신의 임무는 학생이 텍스트의 표면적 의미뿐만 아니라 숨은 의도나 핵심 문법을 완벽히 이해했는지 확인하는 '역방향 인터뷰'를 주도하는 것입니다.
인터뷰 질문의 난이도와 힌트를 주는 방식은 반드시 '{student_level}'에 완벽하게 맞추어 조절하세요.
절대 한 번에 정답을 다 알려주지 마세요.
반드시 아래의 지침을 따르세요:
1. 질문은 한 번에 하나씩만 던지세요.
2. 학생의 답변을 들으면, 맞았는지 틀렸는지 먼저 친절하게 피드백해 주고 칭찬이나 격려를 해주세요.
3. 답변이 부족하다면 힌트(예: "본문 3번째 문장을 다시 볼까요?")를 주며 다시 질문하세요.
4. 답변이 완벽하다면, 본문의 다음 내용이나 더 심화된 사고를 요구하는 꼬리 질문을 던지세요.
5. 절대로 학생보다 말을 너무 길게 하지 마세요. 짧고 굵게, 사람처럼 자연스러운 한국어(해요체)로 대화하세요.

[학습 컨텍스트]
{context_str}
"""

    
    if client is None:
        configure_gemini()
        
    try:
        # 대화 기록 변환 (Streamlit 형식 -> Gemini 형식)
        gemini_contents = []
        for msg in chat_history:
            role = 'user' if msg['role'] == 'user' else 'model'
            gemini_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg['content'])]))
            
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=gemini_contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
        )
        return response.text
    except Exception as e:
        return f"죄송합니다. 오류가 발생했습니다: {str(e)}"

def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """사용자의 음성을 텍스트로 변환합니다."""
    if client is None:
        configure_gemini()
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                "이 오디오에 담긴 사람의 말을 텍스트로 정확하게 받아쓰기 해. 다른 말은 덧붙이지 말고 오직 받아쓴 텍스트만 출력해."
            ],
            config=types.GenerateContentConfig(
                temperature=0.0
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"[음성 인식 실패: {str(e)}]"

def evaluate_pronunciation(audio_bytes: bytes, target_sentence: str, target_language: str, mime_type: str = "audio/wav") -> Dict[str, Any]:
    """사용자의 음성을 평가하여 발음 정확도와 피드백을 반환합니다."""
    if client is None:
        configure_gemini()
        
    schema = {
        "type": "object",
        "properties": {
            "transcription": {"type": "string", "description": "학생이 실제로 발음한 대로 인식된 문장 텍스트"},
            "score": {"type": "integer", "description": "0~100점 사이의 종합 발음/억양 점수"},
            "feedback": {"type": "string", "description": "어느 부분의 강세나 발음이 어색했는지 친절하게 알려주는 한국어 피드백"}
        },
        "required": ["transcription", "score", "feedback"]
    }
    
    prompt = f"""
    당신은 원어민 수준의 외국어 과외 선생님입니다.
    다음 오디오를 듣고 학생의 발음을 평가하세요.
    목표 언어: {target_language}
    목표 문장: "{target_sentence}"
    
    학생이 목표 문장을 얼마나 정확하게 발음했는지 평가하고 점수와 피드백을 제공하세요.
    학생이 전혀 엉뚱한 말을 했다면 점수를 낮게 주고 다시 시도하라고 피드백하세요.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {"transcription": "", "score": 0, "feedback": f"평가 중 오류가 발생했습니다: {str(e)}"}
