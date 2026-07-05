import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "eduai.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabularies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            meaning TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
    ''')
    # 중복 방지를 위한 UNIQUE 인덱스 (선택적)
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_word ON vocabularies(word)
    ''')
    
    # 지문 보관소 (Library)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            type TEXT,
            source_language TEXT,
            target_language TEXT,
            raw_json TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
    ''')
    
    # 발음 평가 점수
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pronunciation_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_sentence TEXT,
            score INTEGER,
            created_at DATETIME NOT NULL
        )
    ''')
    
    # 사용자 설정 저장소
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def add_word(word: str, meaning: str) -> bool:
    """단어를 저장합니다. 이미 존재하면 무시하고 False 반환, 성공 시 True 반환"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO vocabularies (word, meaning, created_at) VALUES (?, ?, ?)",
            (word, meaning, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # UNIQUE 제약 조건(이미 있는 단어) 위반 시
        return False

def get_all_words():
    """모든 단어를 최신순으로 가져옵니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vocabularies ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_word(vocab_id: int):
    """지정된 ID의 단어를 삭제합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vocabularies WHERE id = ?", (vocab_id,))
    conn.commit()
    conn.close()

# --- Passages (Library) CRUD ---
import json

def add_passage(title: str, p_type: str, source_lang: str, target_lang: str, raw_json: dict) -> int:
    """분석된 지문을 보관소에 저장합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO passages (title, type, source_language, target_language, raw_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (title, p_type, source_lang, target_lang, json.dumps(raw_json, ensure_ascii=False), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    passage_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return passage_id

def get_all_passages():
    """모든 보관된 지문을 최신순으로 가져옵니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, type, source_language, target_language, created_at FROM passages ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_passage_by_id(passage_id: int) -> dict:
    """특정 지문의 원본 JSON 데이터를 가져옵니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT raw_json FROM passages WHERE id = ?", (passage_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row['raw_json'])
    return None

def delete_passage(passage_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM passages WHERE id = ?", (passage_id,))
    conn.commit()
    conn.close()

# --- Pronunciation Scores CRUD ---

def add_pronunciation_score(target_sentence: str, score: int):
    """발음 점수를 저장합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pronunciation_scores (target_sentence, score, created_at) VALUES (?, ?, ?)",
        (target_sentence, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()

def get_recent_pronunciation_scores(limit: int = 15):
    """최근 발음 점수 기록을 가져옵니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT target_sentence, score, created_at FROM pronunciation_scores ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    # Pandas dataframe 용으로 변환하기 쉽도록 리스트 반환
    return [dict(row) for row in rows][-limit:]

# --- Dashboard Stats ---
def get_dashboard_stats():
    """대시보드 상단 요약을 위한 통계 데이터를 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM passages")
    total_passages = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vocabularies")
    total_words = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(score) FROM pronunciation_scores")
    avg_score_row = cursor.fetchone()[0]
    avg_score = round(avg_score_row, 1) if avg_score_row else 0.0
    
    conn.close()
    return {
        "total_passages": total_passages,
        "total_words": total_words,
        "avg_score": avg_score
    }


def set_setting(key: str, value: str) -> bool:
    """사용자 설정을 DB에 저장하거나 업데이트합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value))
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving setting {key}: {e}")
        return False

def get_setting(key: str, default_value: str = None) -> str:
    """사용자 설정을 DB에서 불러옵니다. 없으면 기본값을 반환합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        return default_value
    except Exception as e:
        print(f"Error reading setting {key}: {e}")
        return default_value
