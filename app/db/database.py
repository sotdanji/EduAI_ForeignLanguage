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
        # 파라미터 바인딩 변환
        query = query.replace("?", "%s")
        # 데이터 타입 변환
        query = query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        query = query.replace("DATETIME", "TIMESTAMP")

    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Postgres에서 lastrowid를 얻으려면 RETURNING id 필요
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
        CREATE TABLE IF NOT EXISTS vocabularies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            meaning TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
        ''',
        '''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_word ON vocabularies(word)
        ''',
        '''
        CREATE TABLE IF NOT EXISTS passages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            target_sentence TEXT,
            score INTEGER,
            created_at DATETIME NOT NULL
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS user_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        '''
    ]
    for q in queries:
        execute_query(q, commit=True)

def add_word(word: str, meaning: str) -> bool:
    try:
        execute_query(
            "INSERT INTO vocabularies (word, meaning, created_at) VALUES (?, ?, ?)",
            (word, meaning, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            commit=True
        )
        return True
    except Exception as e:
        # sqlite3.IntegrityError or psycopg2.errors.UniqueViolation
        return False

def get_all_words():
    return execute_query("SELECT * FROM vocabularies ORDER BY created_at DESC", fetch="all")

def delete_word(vocab_id: int):
    execute_query("DELETE FROM vocabularies WHERE id = ?", (vocab_id,), commit=True)

def add_passage(title: str, p_type: str, source_lang: str, target_lang: str, raw_json: dict) -> int:
    return execute_query(
        "INSERT INTO passages (title, type, source_language, target_language, raw_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (title, p_type, source_lang, target_lang, json.dumps(raw_json, ensure_ascii=False), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        commit=True,
        fetch="lastrowid"
    )

def get_all_passages():
    return execute_query("SELECT id, title, type, source_language, target_language, created_at FROM passages ORDER BY created_at DESC", fetch="all")

def get_passage_by_id(passage_id: int) -> dict:
    row = execute_query("SELECT raw_json FROM passages WHERE id = ?", (passage_id,), fetch="one")
    if row and 'raw_json' in row:
        return json.loads(row['raw_json'])
    return None

def delete_passage(passage_id: int):
    execute_query("DELETE FROM passages WHERE id = ?", (passage_id,), commit=True)

def add_pronunciation_score(target_sentence: str, score: int):
    execute_query(
        "INSERT INTO pronunciation_scores (target_sentence, score, created_at) VALUES (?, ?, ?)",
        (target_sentence, score, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        commit=True
    )

def get_recent_pronunciation_scores(limit: int = 15):
    rows = execute_query("SELECT target_sentence, score, created_at FROM pronunciation_scores ORDER BY created_at ASC", fetch="all")
    return rows[-limit:]

def get_dashboard_stats():
    total_passages = execute_query("SELECT COUNT(*) as count FROM passages", fetch="one")['count']
    total_words = execute_query("SELECT COUNT(*) as count FROM vocabularies", fetch="one")['count']
    
    avg_score_row = execute_query("SELECT AVG(score) as avg_score FROM pronunciation_scores", fetch="one")
    avg_score = round(avg_score_row['avg_score'], 1) if avg_score_row and avg_score_row['avg_score'] else 0.0
    
    return {
        "total_passages": total_passages,
        "total_words": total_words,
        "avg_score": avg_score
    }

def set_setting(key: str, value: str) -> bool:
    try:
        execute_query(
            "INSERT INTO user_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
            commit=True
        )
        return True
    except Exception as e:
        print(f"Error saving setting {key}: {e}")
        return False

def get_setting(key: str, default_value: str = None) -> str:
    try:
        row = execute_query("SELECT value FROM user_settings WHERE key = ?", (key,), fetch="one")
        if row and 'value' in row:
            return row['value']
        return default_value
    except Exception as e:
        print(f"Error reading setting {key}: {e}")
        return default_value
