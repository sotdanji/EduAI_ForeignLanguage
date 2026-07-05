import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_PATH = os.path.join(os.path.dirname(__file__), "eduai.db")

def get_connection():
    if DB_TYPE == "postgres":
        import psycopg2
        from psycopg2.extras import RealDictCursor
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def execute_query(query: str, params: tuple = (), commit: bool = False, fetch: str = "none"):
    """
    통합 쿼리 실행기
    SQLite용 쿼리(?)를 받아서 Postgres(%s) 환경에서도 동작하게 변환합니다.
    """
    if DB_TYPE == "postgres":
        query = query.replace("?", "%s")
        query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        query = query.replace("DATETIME", "TIMESTAMP")

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if fetch == "lastrowid" and DB_TYPE == "postgres":
            if "RETURNING id" not in query:
                query += " RETURNING id"
                
        cursor.execute(query, params)
        
        if commit:
            conn.commit()
            
        if fetch == "all":
            return [dict(row) for row in cursor.fetchall()]
        elif fetch == "one":
            row = cursor.fetchone()
            return dict(row) if row else None
        elif fetch == "lastrowid":
            if DB_TYPE == "postgres":
                return cursor.fetchone()['id']
            else:
                return cursor.lastrowid
        return None
    except Exception as e:
        if commit:
            conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def init_db():
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS vocabularies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            meaning TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
        ''',
        '''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_user_word ON vocabularies(user_id, word)
        ''',
        '''
        CREATE TABLE IF NOT EXISTS passages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            type TEXT,
            source_language TEXT,
            target_language TEXT,
            raw_json TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS pronunciation_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_sentence TEXT,
            score INTEGER,
            created_at DATETIME NOT NULL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            PRIMARY KEY (user_id, key)
        )
        '''
    ]
    for q in queries:
        execute_query(q, commit=True)

# --- 사용자 관리 ---
def register_user(username: str, password: str) -> int:
    """회원가입. 실패 시 None 또는 Exception"""
    try:
        user_id = execute_query(
            "INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
            (username, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            commit=True, fetch="lastrowid"
        )
        return user_id
    except Exception as e:
        return None

def authenticate_user(username: str, password: str) -> int:
    """로그인 검증. 성공 시 user_id 반환, 실패 시 None 반환"""
    row = execute_query("SELECT id FROM users WHERE username = ? AND password = ?", (username, password), fetch="one")
    if row and 'id' in row:
        return row['id']
    return None

# --- 단어장 관리 ---
def add_word(user_id: int, word: str, meaning: str) -> bool:
    try:
        execute_query(
            "INSERT INTO vocabularies (user_id, word, meaning, created_at) VALUES (?, ?, ?, ?)",
            (user_id, word, meaning, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            commit=True
        )
        return True
    except Exception as e:
        return False

def get_all_words(user_id: int):
    return execute_query("SELECT * FROM vocabularies WHERE user_id = ? ORDER BY created_at DESC", (user_id,), fetch="all")

def delete_word(user_id: int, vocab_id: int):
    execute_query("DELETE FROM vocabularies WHERE id = ? AND user_id = ?", (vocab_id, user_id), commit=True)

# --- 지문(서재) 관리 ---
def add_passage(user_id: int, title: str, p_type: str, source_lang: str, target_lang: str, raw_json: dict) -> int:
    return execute_query(
        "INSERT INTO passages (user_id, title, type, source_language, target_language, raw_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, title, p_type, source_lang, target_lang, json.dumps(raw_json, ensure_ascii=False), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        commit=True, fetch="lastrowid"
    )

def get_all_passages(user_id: int):
    return execute_query("SELECT id, title, type, source_language, target_language, created_at FROM passages WHERE user_id = ? ORDER BY created_at DESC", (user_id,), fetch="all")

def get_passage_by_id(user_id: int, passage_id: int) -> dict:
    row = execute_query("SELECT raw_json FROM passages WHERE id = ? AND user_id = ?", (passage_id, user_id), fetch="one")
    if row and 'raw_json' in row:
        return json.loads(row['raw_json'])
    return None

def delete_passage(user_id: int, passage_id: int):
    execute_query("DELETE FROM passages WHERE id = ? AND user_id = ?", (passage_id, user_id), commit=True)

# --- 발음 점수 관리 ---
def add_pronunciation_score(user_id: int, target_sentence: str, score: int):
    execute_query(
        "INSERT INTO pronunciation_scores (user_id, target_sentence, score, created_at) VALUES (?, ?, ?, ?)",
        (user_id, target_sentence, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        commit=True
    )

def get_date_threshold(period: str) -> str:
    from datetime import datetime, timedelta
    now = datetime.now()
    if period == "오늘":
        target = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "이번 주":
        target = now - timedelta(days=now.weekday())
        target = target.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "이번 달":
        target = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "이번 학기":
        if 3 <= now.month <= 8:
            target = now.replace(month=3, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif now.month >= 9:
            target = now.replace(month=9, day=1, hour=0, minute=0, second=0, microsecond=0)
        else: # 1, 2
            target = now.replace(year=now.year - 1, month=9, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        return None
    return target.strftime("%Y-%m-%d %H:%M:%S")

def get_recent_pronunciation_scores(user_id: int, limit: int = 15, period: str = "전체"):
    threshold = get_date_threshold(period)
    if threshold:
        rows = execute_query("SELECT target_sentence, score, created_at FROM pronunciation_scores WHERE user_id = ? AND created_at >= ? ORDER BY created_at ASC", (user_id, threshold), fetch="all")
    else:
        rows = execute_query("SELECT target_sentence, score, created_at FROM pronunciation_scores WHERE user_id = ? ORDER BY created_at ASC", (user_id,), fetch="all")
    return rows[-limit:]

# --- 대시보드 ---
def get_dashboard_stats(user_id: int, period: str = "전체"):
    threshold = get_date_threshold(period)
    
    if threshold:
        query_suffix = " AND created_at >= ?"
        params = (user_id, threshold)
    else:
        query_suffix = ""
        params = (user_id,)
        
    total_passages = execute_query(f"SELECT COUNT(*) as count FROM passages WHERE user_id = ?{query_suffix}", params, fetch="one")['count']
    total_words = execute_query(f"SELECT COUNT(*) as count FROM vocabularies WHERE user_id = ?{query_suffix}", params, fetch="one")['count']
    
    avg_score_row = execute_query(f"SELECT AVG(score) as avg_score FROM pronunciation_scores WHERE user_id = ?{query_suffix}", params, fetch="one")
    avg_score = round(avg_score_row['avg_score'], 1) if avg_score_row and avg_score_row['avg_score'] else 0.0
    
    return {
        "total_passages": total_passages,
        "total_words": total_words,
        "avg_score": avg_score
    }

# --- 사용자 설정 ---
def set_setting(user_id: int, key: str, value: str) -> bool:
    try:
        execute_query(
            "INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?) ON CONFLICT(user_id, key) DO UPDATE SET value=excluded.value",
            (user_id, key, str(value)),
            commit=True
        )
        return True
    except Exception as e:
        print(f"Error saving setting {key}: {e}")
        return False

def get_setting(user_id: int, key: str, default_value: str = None) -> str:
    try:
        row = execute_query("SELECT value FROM user_settings WHERE user_id = ? AND key = ?", (user_id, key), fetch="one")
        if row and 'value' in row:
            return row['value']
        return default_value
    except Exception as e:
        print(f"Error reading setting {key}: {e}")
        return default_value
