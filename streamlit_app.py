import streamlit as st
import os
from dotenv import load_dotenv

import sys
import importlib

# 강제 모듈 리로드 (Streamlit 캐싱 방지)
if "app.agents.parser_agent" in sys.modules:
    importlib.reload(sys.modules["app.agents.parser_agent"])
if "app.ui.result_view" in sys.modules:
    importlib.reload(sys.modules["app.ui.result_view"])
if "app.db.database" in sys.modules:
    importlib.reload(sys.modules["app.db.database"])
if "app.ui.views.auth_view" in sys.modules:
    importlib.reload(sys.modules["app.ui.views.auth_view"])
if "app.ui.views.sidebar_view" in sys.modules:
    importlib.reload(sys.modules["app.ui.views.sidebar_view"])
if "app.ui.components.manual_dialog" in sys.modules:
    importlib.reload(sys.modules["app.ui.components.manual_dialog"])

from app.agents import configure_gemini
from app.db.database import init_db, get_passage_by_id
import json

# Views
from app.ui.views.auth_view import render_auth_view
from app.ui.views.sidebar_view import render_sidebar
from app.ui.views.learn_view import render_learn_view
from app.ui.views.vocab_view import render_vocab_view
from app.ui.views.dashboard_view import render_dashboard_view

load_dotenv()
configure_gemini()
init_db()

st.set_page_config(page_title="EduAI Foreign Language", page_icon="🏫", layout="wide")

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "parsed_data" not in st.session_state:
    st.session_state["parsed_data"] = None
if "load_passage_id" not in st.session_state:
    st.session_state["load_passage_id"] = None
if "switch_to_tab1" not in st.session_state:
    st.session_state["switch_to_tab1"] = False

# 대시보드에서 지문 불러오기 처리
if st.session_state["load_passage_id"]:
    passage = get_passage_by_id(st.session_state["user_id"], st.session_state["load_passage_id"])
    if passage:
        st.session_state["parsed_data"] = json.loads(passage['parsed_data'])
        st.session_state["switch_to_tab1"] = True
    st.session_state["load_passage_id"] = None
    st.rerun()

if not st.session_state["logged_in"]:
    render_auth_view()
else:
    render_sidebar()
    
    st.title("🏫 EduAI 나만의 꼬마 외국어 선생님")
    
    tab1, tab2, tab3 = st.tabs(["📚 학습하기", "📝 단어장", "📊 대시보드 및 서재"])
    
    with tab1:
        render_learn_view()
        
    with tab2:
        render_vocab_view()
        
    with tab3:
        render_dashboard_view()
