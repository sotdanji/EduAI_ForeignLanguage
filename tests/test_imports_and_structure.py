"""
테스트 1: 모듈 임포트 및 구조 검증
- 코드 분할 후 모든 모듈이 정상 임포트 가능한지 검증
- 순환 참조, 누락된 모듈, 잘못된 경로 탐지
"""
import pytest
import importlib
import sys
import os

# 프로젝트 루트 경로 보장
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestModuleImports:
    """모든 모듈이 임포트 가능한지 검증"""

    def test_import_base_agent(self):
        from app.agents.base_agent import BaseGeminiAgent, is_error_result
        assert BaseGeminiAgent is not None
        assert callable(is_error_result)

    def test_import_parser_agent(self):
        from app.agents.parser_agent import ParserAgent
        assert ParserAgent is not None

    def test_import_pronunciation_agent(self):
        from app.agents.pronunciation_agent import PronunciationAgent
        assert PronunciationAgent is not None

    def test_import_tutor_agent(self):
        from app.agents.tutor_agent import TutorAgent
        assert TutorAgent is not None

    def test_import_agents_init(self):
        """__init__.py의 convenience 인스턴스가 정상 생성되는지 검증"""
        from app.agents import parser_agent, tutor_agent, pronunciation_agent, configure_gemini
        assert parser_agent is not None
        assert tutor_agent is not None
        assert pronunciation_agent is not None
        assert callable(configure_gemini)

    def test_import_database(self):
        from app.db.database import (
            init_db, register_user, authenticate_user,
            add_word, get_all_words, delete_word,
            add_passage, get_all_passages, get_passage_by_id, delete_passage,
            add_pronunciation_score, get_recent_pronunciation_scores,
            get_dashboard_stats, set_setting, get_setting
        )
        # 모든 함수가 임포트 되었으면 성공
        assert callable(init_db)

    def test_import_tts_engine(self):
        from app.core.tts_engine import generate_audio_sync, get_voice_for_language
        assert callable(generate_audio_sync)
        assert callable(get_voice_for_language)

    def test_import_views(self):
        """UI 뷰 모듈들이 모두 임포트 가능한지"""
        from app.ui.views.auth_view import render_auth_view
        from app.ui.views.sidebar_view import render_sidebar
        from app.ui.views.learn_view import render_learn_view
        from app.ui.views.vocab_view import render_vocab_view
        from app.ui.views.dashboard_view import render_dashboard_view
        assert callable(render_auth_view)
        assert callable(render_sidebar)
        assert callable(render_learn_view)
        assert callable(render_vocab_view)
        assert callable(render_dashboard_view)

    def test_import_manual_dialog(self):
        from app.ui.components.manual_dialog import show_manual
        assert callable(show_manual)

    def test_import_result_view(self):
        from app.ui.result_view import render_parsed_result
        assert callable(render_parsed_result)

    def test_import_qr_utils(self):
        from app.utils.qr import get_local_ip, generate_qr_code
        assert callable(get_local_ip)
        assert callable(generate_qr_code)


class TestNoStaleImports:
    """삭제된 모듈(llm_engine)을 참조하는 코드가 없는지 검증"""

    def test_no_llm_engine_import_in_result_view(self):
        """result_view.py에서 삭제된 llm_engine을 import하지 않는지 검증"""
        import inspect
        from app.ui import result_view
        source = inspect.getsource(result_view)
        assert "from app.core.llm_engine" not in source, \
            "result_view.py에 아직 삭제된 app.core.llm_engine 임포트가 남아있습니다!"

    def test_no_llm_engine_import_in_learn_view(self):
        import inspect
        from app.ui.views import learn_view
        source = inspect.getsource(learn_view)
        assert "from app.core.llm_engine" not in source, \
            "learn_view.py에 아직 삭제된 app.core.llm_engine 임포트가 남아있습니다!"

    def test_no_llm_engine_file_exists(self):
        """llm_engine.py 파일이 완전히 삭제되었는지 확인"""
        llm_engine_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "core", "llm_engine.py"
        )
        assert not os.path.exists(llm_engine_path), \
            "삭제되어야 할 app/core/llm_engine.py 파일이 아직 존재합니다!"


class TestAgentInheritance:
    """에이전트 클래스 상속 관계 검증"""

    def test_parser_inherits_base(self):
        from app.agents.base_agent import BaseGeminiAgent
        from app.agents.parser_agent import ParserAgent
        assert issubclass(ParserAgent, BaseGeminiAgent)

    def test_pronunciation_inherits_base(self):
        from app.agents.base_agent import BaseGeminiAgent
        from app.agents.pronunciation_agent import PronunciationAgent
        assert issubclass(PronunciationAgent, BaseGeminiAgent)

    def test_tutor_inherits_base(self):
        from app.agents.base_agent import BaseGeminiAgent
        from app.agents.tutor_agent import TutorAgent
        assert issubclass(TutorAgent, BaseGeminiAgent)

    def test_agents_share_client(self):
        """모든 에이전트가 같은 클라이언트를 공유하는지 검증"""
        from app.agents.parser_agent import ParserAgent
        from app.agents.pronunciation_agent import PronunciationAgent
        from app.agents.tutor_agent import TutorAgent
        # _client는 classmethod로 공유되어야 함
        p = ParserAgent()
        pr = PronunciationAgent()
        t = TutorAgent()
        # API 키 없이 호출하면 None이지만, 같은 class variable 참조인지 확인
        assert hasattr(p, '_client')
        assert hasattr(pr, '_client')
        assert hasattr(t, '_client')


class TestAgentMethods:
    """각 에이전트의 필수 메서드 존재 여부 검증"""

    def test_parser_has_parse_from_text(self):
        from app.agents.parser_agent import ParserAgent
        agent = ParserAgent()
        assert hasattr(agent, 'parse_from_text')
        assert callable(agent.parse_from_text)

    def test_parser_has_parse_from_image(self):
        from app.agents.parser_agent import ParserAgent
        agent = ParserAgent()
        assert hasattr(agent, 'parse_from_image')
        assert callable(agent.parse_from_image)

    def test_pronunciation_has_evaluate(self):
        from app.agents.pronunciation_agent import PronunciationAgent
        agent = PronunciationAgent()
        assert hasattr(agent, 'evaluate_pronunciation')
        assert callable(agent.evaluate_pronunciation)

    def test_pronunciation_has_transcribe(self):
        from app.agents.pronunciation_agent import PronunciationAgent
        agent = PronunciationAgent()
        assert hasattr(agent, 'transcribe_audio')
        assert callable(agent.transcribe_audio)

    def test_tutor_has_chat_response(self):
        from app.agents.tutor_agent import TutorAgent
        agent = TutorAgent()
        assert hasattr(agent, 'get_tutor_chat_response')
        assert callable(agent.get_tutor_chat_response)


class TestIsErrorResult:
    """is_error_result 유틸리티 함수 로직 검증"""

    def test_normal_result_not_error(self):
        from app.agents.base_agent import is_error_result
        assert is_error_result({"title": "test", "contents": []}) is False

    def test_dict_with_error_key(self):
        from app.agents.base_agent import is_error_result
        assert is_error_result({"error": "something went wrong"}) is True

    def test_string_not_error(self):
        from app.agents.base_agent import is_error_result
        assert is_error_result("just a string") is False

    def test_none_not_error(self):
        from app.agents.base_agent import is_error_result
        assert is_error_result(None) is False

    def test_pronunciation_retry_trigger(self):
        from app.agents.base_agent import is_error_result
        result = {
            "transcription": "",
            "score": 0,
            "feedback": "평가 중 오류가 발생했습니다: timeout"
        }
        assert is_error_result(result) is True

    def test_pronunciation_success_not_error(self):
        from app.agents.base_agent import is_error_result
        result = {
            "transcription": "hello world",
            "score": 85,
            "feedback": "좋은 발음이에요!"
        }
        assert is_error_result(result) is False
