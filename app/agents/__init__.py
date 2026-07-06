from .base_agent import BaseGeminiAgent
from .parser_agent import ParserAgent
from .pronunciation_agent import PronunciationAgent
from .tutor_agent import TutorAgent
from .preprocessor_agent import PreprocessorAgent

# Convenience instances
parser_agent = ParserAgent()
tutor_agent = TutorAgent()
pronunciation_agent = PronunciationAgent()
preprocessor_agent = PreprocessorAgent()

def configure_gemini(api_key=None):
    BaseGeminiAgent.get_client(api_key)
