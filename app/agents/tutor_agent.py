from typing import Dict, Any
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_result
from app.agents.base_agent import BaseGeminiAgent, is_error_result

class TutorAgent(BaseGeminiAgent):
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_result(is_error_result))
    def get_tutor_chat_response(self, chat_history: list, parsed_data: Dict[str, Any], mode: str = "qa", student_level: str = "중학교 1학년") -> str:
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
            context_str += f"\n기존 제공된 학생용 피드백:\n{tutor_feedback}\n"
                
        if mode == "qa":
            system_instruction = f"""당신은 친절하고 전문적인 엘리트 외국어 과외 선생님입니다.
현재 지도하는 학생의 수준은 '{student_level}'입니다.
학생이 학습 중인 위 지문과 단어, 피드백을 완벽히 숙지하고 있습니다.
학생이 지문이나 외국어에 대해 질문을 하면, 진짜 선생님처럼 친절하고 이해하기 쉽게 대답해주세요.
너무 딱딱한 기계나 AI처럼 말하지 말고, 사람처럼 자연스러운 한국어 어조를 사용하세요. 학생의 수준에 맞춰 어휘와 해설의 깊이, 문법 용어의 사용 여부, 말투를 반드시 '{student_level}'에 완벽하게 맞추세요. (예: 초등학생에게는 매우 쉽고 다정하게, 고등학생에게는 수능/내신 중심의 성숙한 말투로)

[학습 컨텍스트]
{context_str}
"""
        elif mode == "interview":
            system_instruction = f"""당신은 날카로우면서도 따뜻한 소크라테스식 인터뷰어이자 과외 선생님입니다.
현재 지도하는 학생의 수준은 '{student_level}'입니다.
학생이 학습 중인 위 지문과 단어, 피드백을 완벽히 숙지하고 있습니다.

당신의 임무는 학생이 텍스트의 표면적인 뜻뿐만 아니라 숨은 의도나 핵심 문법을 완벽히 이해했는지 확인하는 '질문 인터뷰'를 주도하는 것입니다.
인터뷰 질문의 난이도와 힌트를 주는 방식은 반드시 '{student_level}'에 완벽하게 맞추어 조절하세요.
절대 한 번에 정답을 알려주지 마세요.
반드시 아래의 지침을 따르세요:
1. 질문은 한 번에 하나씩만 하세요.
2. 학생의 대답이 맞았는지 틀렸는지 먼저 친절하게 피드백해 주고 칭찬이나 격려를 해주세요.
3. 대답이 부족하다면 힌트(예: "본문 3번째 문장을 다시 볼까?")를 주며 다시 질문하세요.
4. 대답이 완벽하다면 본문의 다음 내용이나 심화된 사고를 요구하는 꼬리 질문을 하세요.
5. 절대로 학생보다 말을 너무 길게 하지 마세요. 짧고 굵게, 사람처럼 자연스러운 한국어 어조로 대화하세요.

[학습 컨텍스트]
{context_str}
"""

        client = self.get_client()
        try:
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
