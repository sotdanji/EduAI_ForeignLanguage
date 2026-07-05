"""
EduAI 테스트 공통 Fixtures
"""
import os
import sys
import json
import pytest
import sqlite3

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트 시 DB_TYPE을 sqlite로 고정
os.environ["DB_TYPE"] = "sqlite"


@pytest.fixture
def test_db(tmp_path):
    """격리된 SQLite DB 생성 (각 테스트마다 독립)"""
    import app.db.database as db_module
    original_path = db_module.DB_PATH
    db_module.DB_PATH = str(tmp_path / "test_eduai.db")
    db_module.DB_TYPE = "sqlite"
    db_module.init_db()
    yield db_module
    db_module.DB_PATH = original_path


@pytest.fixture
def sample_parsed_data():
    """AI 파서 결과 샘플 데이터"""
    return {
        "source_language": "en",
        "target_language": "ko",
        "title": "Foreign Languages",
        "type": "reading",
        "contents": [
            {
                "source_text": "The Mirae Middle School Board has been planning to teach students a few foreign languages.",
                "target_text": "미래 중학교 교육 위원회는 학생들에게 몇 가지 외국어를 가르칠 계획을 세우고 있어요.",
                "speaker_gender": "neutral",
                "speaker_name": ""
            },
            {
                "source_text": "After hearing the students' opinions, it will make a decision.",
                "target_text": "학생들의 의견을 들은 후에 결정을 내릴 거예요.",
                "speaker_gender": "neutral",
                "speaker_name": ""
            }
        ],
        "vocabulary": [
            {"word": "planning", "meaning": "계획하는"},
            {"word": "foreign", "meaning": "외국의"},
            {"word": "decision", "meaning": "결정"},
            {"word": "opinion", "meaning": "의견"},
            {"word": "languages", "meaning": "언어들"}
        ],
        "original_questions": [],
        "tutor_feedback": ""
    }


@pytest.fixture
def sample_dialogue_data():
    """대화문 타입 샘플 데이터"""
    return {
        "source_language": "en",
        "target_language": "ko",
        "title": "At the Restaurant",
        "type": "dialogue",
        "contents": [
            {
                "source_text": "Waiter: Good evening. May I take your order?",
                "target_text": "웨이터: 안녕하세요. 주문하시겠어요?",
                "speaker_gender": "male",
                "speaker_name": "Waiter"
            },
            {
                "source_text": "Customer: Yes, I'd like a steak, please.",
                "target_text": "손님: 네, 스테이크 하나 주세요.",
                "speaker_gender": "female",
                "speaker_name": "Customer"
            }
        ],
        "vocabulary": [
            {"word": "order", "meaning": "주문"},
            {"word": "steak", "meaning": "스테이크"},
            {"word": "please", "meaning": "부탁합니다"},
            {"word": "evening", "meaning": "저녁"},
            {"word": "customer", "meaning": "고객"}
        ],
        "original_questions": [],
        "tutor_feedback": ""
    }
