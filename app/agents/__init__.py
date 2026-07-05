from .base_agent import BaseGeminiAgent
from .parser_agent import ParserAgent
from .pronunciation_agent import PronunciationAgent
from .tutor_agent import TutorAgent

# Convenience instances
parser_agent = ParserAgent()
tutor_agent = TutorAgent()
pronunciation_agent = PronunciationAgent()

def configure_gemini(api_key=None):
    BaseGeminiAgent.get_client(api_key)
