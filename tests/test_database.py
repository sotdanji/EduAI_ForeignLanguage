"""
테스트 2: 데이터베이스 계층 검증
- CRUD 작업 정상 동작 (user, passage, vocabulary, settings, pronunciation)
- 엣지 케이스 및 데이터 무결성
"""
import pytest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDatabaseInit:
    """DB 초기화 및 테이블 생성 검증"""

    def test_init_db_creates_tables(self, test_db):
        """init_db가 모든 테이블을 생성하는지 검증"""
        import sqlite3
        conn = sqlite3.connect(test_db.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        expected = {"users", "vocabularies", "passages", "pronunciation_scores", "user_settings"}
        assert expected.issubset(tables), f"누락된 테이블: {expected - tables}"

    def test_init_db_idempotent(self, test_db):
        """init_db를 여러 번 호출해도 에러 없이 동작하는지"""
        test_db.init_db()
        test_db.init_db()
        # 에러 없이 통과하면 성공


class TestUserCRUD:
    """사용자 등록 및 인증"""

    def test_register_user(self, test_db):
        uid = test_db.register_user("testuser", "password123")
        assert uid is not None
        assert isinstance(uid, int)

    def test_register_duplicate_user(self, test_db):
        test_db.register_user("dupuser", "pass1")
        uid2 = test_db.register_user("dupuser", "pass2")
        assert uid2 is None, "중복 사용자 등록이 None을 반환해야 합니다"

    def test_authenticate_success(self, test_db):
        test_db.register_user("authuser", "mypass")
        uid = test_db.authenticate_user("authuser", "mypass")
        assert uid is not None

    def test_authenticate_wrong_password(self, test_db):
        test_db.register_user("authuser2", "correct")
        uid = test_db.authenticate_user("authuser2", "wrong")
        assert uid is None

    def test_authenticate_nonexistent_user(self, test_db):
        uid = test_db.authenticate_user("ghost", "password")
        assert uid is None


class TestPassageCRUD:
    """지문 저장/조회/삭제"""

    def test_add_and_get_passages(self, test_db, sample_parsed_data):
        uid = test_db.register_user("passuser", "pass")
        pid = test_db.add_passage(uid, "Test Title", "reading", "en", "ko", sample_parsed_data)
        assert pid is not None

        passages = test_db.get_all_passages(uid)
        assert len(passages) == 1
        assert passages[0]['title'] == "Test Title"
        # get_all_passages가 반환하는 컬럼명은 'type'이어야 함 (p_type이 아님)
        assert 'type' in passages[0], "passages에 'type' 키가 존재해야 합니다 (p_type이 아닌!)"
        assert passages[0]['type'] == "reading"

    def test_get_passage_by_id(self, test_db, sample_parsed_data):
        uid = test_db.register_user("getuser", "pass")
        pid = test_db.add_passage(uid, "Title", "reading", "en", "ko", sample_parsed_data)
        
        result = test_db.get_passage_by_id(uid, pid)
        assert result is not None
        assert result['title'] == sample_parsed_data['title']
        assert len(result['contents']) == len(sample_parsed_data['contents'])

    def test_delete_passage(self, test_db, sample_parsed_data):
        uid = test_db.register_user("deluser", "pass")
        pid = test_db.add_passage(uid, "To Delete", "reading", "en", "ko", sample_parsed_data)
        
        test_db.delete_passage(uid, pid)
        passages = test_db.get_all_passages(uid)
        assert len(passages) == 0

    def test_passage_user_isolation(self, test_db, sample_parsed_data):
        """다른 사용자의 지문에 접근할 수 없는지 검증"""
        uid1 = test_db.register_user("user1", "pass")
        uid2 = test_db.register_user("user2", "pass")
        pid = test_db.add_passage(uid1, "Secret", "reading", "en", "ko", sample_parsed_data)
        
        result = test_db.get_passage_by_id(uid2, pid)
        assert result is None, "다른 사용자의 지문에 접근 가능하면 보안 위반!"

    def test_get_passage_by_id_returns_parseable_json(self, test_db, sample_parsed_data):
        """get_passage_by_id가 반환하는 데이터를 다시 JSON으로 파싱 가능한지"""
        uid = test_db.register_user("jsonuser", "pass")
        pid = test_db.add_passage(uid, "Title", "reading", "en", "ko", sample_parsed_data)
        result = test_db.get_passage_by_id(uid, pid)
        # result 자체가 이미 dict (json.loads 수행 후이므로)
        assert isinstance(result, dict)
        assert 'contents' in result


class TestVocabularyCRUD:
    """단어장 CRUD"""

    def test_add_word(self, test_db):
        uid = test_db.register_user("vocuser", "pass")
        success = test_db.add_word(uid, "hello", "안녕하세요")
        assert success is True

    def test_get_all_words(self, test_db):
        uid = test_db.register_user("vocuser2", "pass")
        test_db.add_word(uid, "hello", "안녕하세요")
        test_db.add_word(uid, "world", "세상")
        
        words = test_db.get_all_words(uid)
        assert len(words) == 2

    def test_delete_word(self, test_db):
        uid = test_db.register_user("vocuser3", "pass")
        test_db.add_word(uid, "test", "테스트")
        words = test_db.get_all_words(uid)
        wid = words[0]['id']
        
        test_db.delete_word(uid, wid)
        words_after = test_db.get_all_words(uid)
        assert len(words_after) == 0

    def test_duplicate_word_fails(self, test_db):
        uid = test_db.register_user("vocuser4", "pass")
        test_db.add_word(uid, "apple", "사과")
        result = test_db.add_word(uid, "apple", "사과2")
        assert result is False, "같은 단어를 중복 저장할 수 없어야 합니다"


class TestPronunciationScores:
    """발음 점수 저장/조회"""

    def test_add_and_get_scores(self, test_db):
        uid = test_db.register_user("pronuser", "pass")
        test_db.add_pronunciation_score(uid, "Hello world", 85)
        test_db.add_pronunciation_score(uid, "Good morning", 72)
        
        scores = test_db.get_recent_pronunciation_scores(uid)
        assert len(scores) == 2
        assert scores[0]['score'] == 85 or scores[1]['score'] == 85

    def test_recent_scores_limit(self, test_db):
        uid = test_db.register_user("pronuser2", "pass")
        for i in range(20):
            test_db.add_pronunciation_score(uid, f"Sentence {i}", i * 5)
        
        scores = test_db.get_recent_pronunciation_scores(uid, limit=15)
        assert len(scores) == 15


class TestDashboardStats:
    """대시보드 통계 조회"""

    def test_empty_dashboard(self, test_db):
        uid = test_db.register_user("dashuser", "pass")
        stats = test_db.get_dashboard_stats(uid)
        assert stats['total_passages'] == 0
        assert stats['total_words'] == 0
        assert stats['avg_score'] == 0.0

    def test_dashboard_with_data(self, test_db, sample_parsed_data):
        uid = test_db.register_user("dashuser2", "pass")
        test_db.add_passage(uid, "Title", "reading", "en", "ko", sample_parsed_data)
        test_db.add_word(uid, "hello", "안녕")
        test_db.add_pronunciation_score(uid, "Hello", 80)
        test_db.add_pronunciation_score(uid, "World", 90)
        
        stats = test_db.get_dashboard_stats(uid)
        assert stats['total_passages'] == 1
        assert stats['total_words'] == 1
        assert stats['avg_score'] == 85.0


class TestUserSettings:
    """사용자 설정 저장/조회"""

    def test_set_and_get_setting(self, test_db):
        uid = test_db.register_user("settingsuser", "pass")
        test_db.set_setting(uid, "student_level", "중학교 2학년")
        
        val = test_db.get_setting(uid, "student_level")
        assert val == "중학교 2학년"

    def test_get_nonexistent_setting_returns_default(self, test_db):
        uid = test_db.register_user("settingsuser2", "pass")
        val = test_db.get_setting(uid, "nonexistent", "기본값")
        assert val == "기본값"

    def test_update_setting(self, test_db):
        uid = test_db.register_user("settingsuser3", "pass")
        test_db.set_setting(uid, "tts_gender", "male")
        test_db.set_setting(uid, "tts_gender", "female")
        
        val = test_db.get_setting(uid, "tts_gender")
        assert val == "female"
