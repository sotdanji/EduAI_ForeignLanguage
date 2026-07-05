"""
테스트 4: UI 계층 코드 검증 (Streamlit 의존성 없이)
- result_view에서 삭제된 모듈 참조 잔존 검사
- learn_view의 st.rerun() 호출 존재 확인
- 뷰 모듈 간 의존성 그래프 검증
"""
import pytest
import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestResultViewIntegrity:
    """result_view.py 소스코드 정적 분석"""

    def test_no_bare_evaluate_pronunciation_calls(self):
        """evaluate_pronunciation()이 pronunciation_agent.evaluate_pronunciation()으로 호출되는지"""
        from app.ui import result_view
        source = inspect.getsource(result_view)
        # "pronunciation_agent.evaluate_pronunciation" 이 아닌 단독 "evaluate_pronunciation(" 패턴 검색
        lines = source.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if 'evaluate_pronunciation(' in stripped and \
               'pronunciation_agent.evaluate_pronunciation(' not in stripped and \
               'def evaluate_pronunciation' not in stripped and \
               '#' not in stripped.split('evaluate_pronunciation')[0]:
                pytest.fail(
                    f"result_view.py 라인 {i+1}: 단독 evaluate_pronunciation() 호출 발견. "
                    f"pronunciation_agent.evaluate_pronunciation()로 수정 필요\n  → {stripped}"
                )

    def test_no_bare_transcribe_audio_calls(self):
        """transcribe_audio()가 pronunciation_agent.transcribe_audio()로 호출되는지"""
        from app.ui import result_view
        source = inspect.getsource(result_view)
        lines = source.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if 'transcribe_audio(' in stripped and \
               'pronunciation_agent.transcribe_audio(' not in stripped and \
               'def transcribe_audio' not in stripped and \
               '#' not in stripped.split('transcribe_audio')[0]:
                pytest.fail(
                    f"result_view.py 라인 {i+1}: 단독 transcribe_audio() 호출 발견. "
                    f"pronunciation_agent.transcribe_audio()로 수정 필요\n  → {stripped}"
                )

    def test_no_bare_get_tutor_chat_response_calls(self):
        """get_tutor_chat_response()가 tutor_agent.get_tutor_chat_response()로 호출되는지"""
        from app.ui import result_view
        source = inspect.getsource(result_view)
        lines = source.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if 'get_tutor_chat_response(' in stripped and \
               'tutor_agent.get_tutor_chat_response(' not in stripped and \
               'def get_tutor_chat_response' not in stripped and \
               '#' not in stripped.split('get_tutor_chat_response')[0]:
                pytest.fail(
                    f"result_view.py 라인 {i+1}: 단독 get_tutor_chat_response() 호출 발견. "
                    f"tutor_agent.get_tutor_chat_response()로 수정 필요\n  → {stripped}"
                )


class TestLearnViewTransitions:
    """learn_view.py 화면 전환 로직 검증"""

    def test_rerun_after_text_parse(self):
        """텍스트 분석 후 st.rerun()이 호출되는지"""
        from app.ui.views import learn_view
        source = inspect.getsource(learn_view)
        # parse_from_text 호출 이후 같은 블록에 st.rerun()이 있는지
        assert "st.rerun()" in source, \
            "learn_view.py에 st.rerun()이 없으면 분석 완료 후 화면이 전환되지 않습니다!"

    def test_rerun_count_matches_parse_count(self):
        """분석 버튼(btn_img, btn_cam, btn_txt) 수만큼 st.rerun()이 있어야 함"""
        from app.ui.views import learn_view
        source = inspect.getsource(learn_view)
        
        # 3개의 분석 경로 존재
        parse_buttons = source.count("parse_from_")
        rerun_calls = source.count("st.rerun()")
        
        # 최소 parse 경로 수만큼 rerun이 있어야 함 (+ 돌아가기 버튼의 rerun)
        assert rerun_calls >= parse_buttons, \
            f"분석 경로 {parse_buttons}개에 대해 st.rerun()이 {rerun_calls}개뿐입니다. 화면 전환 누락 가능성!"


class TestStreamlitAppEntryPoint:
    """streamlit_app.py 진입점 검증"""

    def test_importlib_reload_covers_new_modules(self):
        """새로 분리한 모듈들이 importlib.reload에 포함되어 있는지"""
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "streamlit_app.py"), "r", encoding="utf-8") as f:
            source = f.read()
        
        modules_to_reload = [
            "app.ui.views.auth_view",
            "app.ui.views.sidebar_view",
            "app.ui.components.manual_dialog",
        ]
        for mod in modules_to_reload:
            assert mod in source, \
                f"streamlit_app.py에서 '{mod}'의 importlib.reload가 누락되었습니다"

    def test_all_view_imports_present(self):
        """필요한 모든 뷰 함수가 import 되어 있는지"""
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "streamlit_app.py"), "r", encoding="utf-8") as f:
            source = f.read()

        required_imports = [
            "render_auth_view",
            "render_sidebar",
            "render_learn_view",
            "render_vocab_view",
            "render_dashboard_view",
        ]
        for imp in required_imports:
            assert imp in source, f"streamlit_app.py에서 '{imp}' import가 누락되었습니다"


class TestManualDialogPath:
    """사용 설명서 파일 경로 검증"""

    def test_manual_file_exists(self):
        manual_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "user_manual.md"
        )
        assert os.path.exists(manual_path), "user_manual.md 파일이 프로젝트 루트에 없습니다!"

    def test_manual_dialog_path_resolves_correctly(self):
        """manual_dialog.py의 경로 계산이 실제 파일을 가리키는지"""
        dialog_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "ui", "components", "manual_dialog.py"
        )
        # dialog_file 위치에서 "../../../user_manual.md"를 계산
        manual_from_dialog = os.path.normpath(
            os.path.join(os.path.dirname(dialog_file), "../../../user_manual.md")
        )
        assert os.path.exists(manual_from_dialog), \
            f"manual_dialog.py에서 계산한 경로 '{manual_from_dialog}'에 user_manual.md가 없습니다!"


class TestRequirementsFile:
    """requirements.txt 검증"""

    def test_edge_tts_in_requirements(self):
        req_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "requirements.txt"
        )
        with open(req_path, "r") as f:
            content = f.read()
        assert "edge-tts" in content, "requirements.txt에 edge-tts가 없습니다!"

    def test_tenacity_in_requirements(self):
        req_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "requirements.txt"
        )
        with open(req_path, "r") as f:
            content = f.read()
        assert "tenacity" in content, "requirements.txt에 tenacity가 없습니다!"

    def test_google_genai_in_requirements(self):
        req_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "requirements.txt"
        )
        with open(req_path, "r") as f:
            content = f.read()
        assert "google-genai" in content, "requirements.txt에 google-genai가 없습니다!"
