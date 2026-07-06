"""
테스트 3: AI 에이전트 로직 검증
- 프롬프트 구성 (텍스트/입력 분리, XML 태그)
- JSON 스키마 정합성
- TTS 음성 매핑
- 에러 핸들링 및 retry 데코레이터
"""
import pytest
import json
import os
import sys
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestParserAgentPromptConstruction:
    """파서 에이전트의 프롬프트가 올바르게 구성되는지 검증"""

    def test_text_prompt_uses_xml_tags(self):
        """텍스트 분석 시 입력이 <INPUT_TEXT> 태그로 감싸지는지 검증
        (프롬프트 인젝션/할루시네이션 방지)"""
        from app.agents.parser_agent import ParserAgent
        import inspect
        source = inspect.getsource(ParserAgent.parse_from_text)
        assert "<INPUT_TEXT>" in source, \
            "텍스트 파서가 <INPUT_TEXT> 태그를 사용하지 않으면 AI가 프롬프트를 본문으로 오인할 수 있습니다!"
        assert "</INPUT_TEXT>" in source

    def test_text_prompt_does_not_pass_as_separate_content(self):
        """contents=[text, prompt] 형태가 아닌 단일 프롬프트로 전달하는지 검증"""
        from app.agents.parser_agent import ParserAgent
        import inspect
        source = inspect.getsource(ParserAgent.parse_from_text)
        assert "contents=[text, prompt]" not in source, \
            "텍스트와 프롬프트를 별도 contents로 넘기면 AI가 혼동합니다!"

    def test_image_prompt_passes_image_separately(self):
        """이미지 분석 시에는 이미지가 별도 content로 전달되어야 함"""
        from app.agents.parser_agent import ParserAgent
        import inspect
        source = inspect.getsource(ParserAgent.parse_from_image)
        assert "[image_part, prompt]" in source or "image_part" in source


class TestParserAgentSchema:
    """파서 JSON 스키마 정합성"""

    def test_response_schema_has_required_fields(self):
        from app.agents.parser_agent import ParserAgent
        schema = ParserAgent.RESPONSE_SCHEMA
        required = schema['required']
        expected = ["source_language", "target_language", "title", "type",
                    "contents", "vocabulary", "original_questions", "tutor_feedback"]
        for field in expected:
            assert field in required, f"필수 필드 '{field}'가 스키마에 없습니다"

    def test_contents_schema_has_source_and_target(self):
        from app.agents.parser_agent import ParserAgent
        schema = ParserAgent.RESPONSE_SCHEMA
        content_props = schema['properties']['contents']['items']['properties']
        assert "source_text" in content_props
        assert "target_text" in content_props
        assert "speaker_gender" in content_props
        assert "speaker_name" in content_props

    def test_vocabulary_schema(self):
        from app.agents.parser_agent import ParserAgent
        schema = ParserAgent.RESPONSE_SCHEMA
        vocab_props = schema['properties']['vocabulary']['items']['properties']
        assert "word" in vocab_props
        assert "meaning" in vocab_props


class TestPronunciationAgentSchema:
    """발음 에이전트 스키마"""

    def test_schema_fields(self):
        from app.agents.pronunciation_agent import PronunciationAgent
        schema = PronunciationAgent.SCHEMA
        assert "transcription" in schema['properties']
        assert "score" in schema['properties']
        assert "feedback" in schema['properties']
        assert schema['properties']['score']['type'] == 'integer'


class TestParsedDataIntegrity:
    """AI 결과 데이터가 UI에서 사용될 때 필요한 키들이 모두 존재하는지"""

    def test_sample_data_has_all_keys(self, sample_parsed_data):
        required_keys = ["source_language", "target_language", "title", "type",
                         "contents", "vocabulary", "original_questions", "tutor_feedback"]
        for key in required_keys:
            assert key in sample_parsed_data, f"샘플 데이터에 '{key}' 키가 없습니다"

    def test_contents_items_have_required_keys(self, sample_parsed_data):
        for i, content in enumerate(sample_parsed_data['contents']):
            assert "source_text" in content, f"contents[{i}]에 'source_text' 없음"
            assert "target_text" in content, f"contents[{i}]에 'target_text' 없음"
            assert "speaker_gender" in content, f"contents[{i}]에 'speaker_gender' 없음"
            assert "speaker_name" in content, f"contents[{i}]에 'speaker_name' 없음"

    def test_dialogue_data_has_speaker_names(self, sample_dialogue_data):
        for content in sample_dialogue_data['contents']:
            assert content['speaker_name'] != "", \
                "대화문 타입인데 speaker_name이 빈 문자열입니다"

    def test_vocabulary_items_structure(self, sample_parsed_data):
        for v in sample_parsed_data['vocabulary']:
            assert "word" in v
            assert "meaning" in v
            assert len(v['word']) > 0
            assert len(v['meaning']) > 0


class TestTTSEngine:
    """TTS 엔진 음성 매핑 로직"""

    def test_english_male_voice(self):
        from app.core.tts_engine import get_voice_for_language
        voice = get_voice_for_language("en", "male")
        assert "en-US" in voice
        assert "Guy" in voice or "Neural" in voice

    def test_english_female_voice(self):
        from app.core.tts_engine import get_voice_for_language
        voice = get_voice_for_language("en", "female")
        assert "en-US" in voice
        assert "Aria" in voice

    def test_japanese_voice(self):
        from app.core.tts_engine import get_voice_for_language
        voice = get_voice_for_language("ja", "male")
        assert "ja-JP" in voice

    def test_korean_voice(self):
        from app.core.tts_engine import get_voice_for_language
        voice = get_voice_for_language("ko", "female")
        assert "ko-KR" in voice

    def test_unknown_language_falls_back_to_english(self):
        from app.core.tts_engine import get_voice_for_language
        voice = get_voice_for_language("xx", "male")
        assert "en-US" in voice, "알 수 없는 언어 코드에 대해 영어 음성이 폴백되어야 합니다"

    def test_language_code_with_region(self):
        """'en-US' 같은 긴 코드도 처리 가능한지"""
        from app.core.tts_engine import get_voice_for_language
        voice = get_voice_for_language("en-US", "male")
        assert "en-US" in voice

    def test_unknown_gender_falls_back_to_male(self):
        from app.core.tts_engine import get_voice_for_language
        voice = get_voice_for_language("en", "unknown_gender")
        assert voice == get_voice_for_language("en", "male")


class TestDashboardViewDataContract:
    """dashboard_view.py가 DB에서 가져온 데이터의 컬럼명을 올바르게 참조하는지"""

    def test_passage_list_uses_type_not_p_type(self):
        """dashboard_view.py가 p['type']을 사용하는지 (p['p_type'] 아님)"""
        import inspect
        from app.ui.views import dashboard_view
        source = inspect.getsource(dashboard_view)
        assert "p['p_type']" not in source, \
            "dashboard_view에서 p['p_type']을 사용하면 KeyError가 발생합니다! p['type'] 또는 p.get('type')을 사용하세요."

    def test_passage_list_uses_safe_get(self):
        """KeyError 방지를 위한 .get() 사용 확인"""
        import inspect
        from app.ui.views import library_view
        source = inspect.getsource(library_view)
        # p.get('title' 또는 p.get('type' 등이 있는지 확인
        assert "p.get(" in source, \
            "library_view는 dict[key] 대신 dict.get(key, default)를 사용하여 KeyError를 방지해야 합니다"
