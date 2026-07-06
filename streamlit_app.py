import streamlit as st
import os
from dotenv import load_dotenv

import sys
# 프로덕션에서는 importlib.reload를 사용하지 않습니다. (성능 최적화)

from app.agents import configure_gemini
from app.db.database import init_db, get_passage_by_id
import json

# Views
from app.ui.views.auth_view import render_auth_view
from app.ui.views.sidebar_view import render_sidebar
from app.ui.views.input_view import render_input_view
from app.ui.views.learn_view import render_learn_view
from app.ui.views.library_view import render_library_view
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
        st.session_state["parsed_data"] = passage
        st.session_state["switch_to_tab1"] = True
    st.session_state["load_passage_id"] = None
    st.rerun()

if not st.session_state["logged_in"]:
    render_auth_view()
else:
    render_sidebar()
    
    st.title("🏫 EduAI 나의 창의적 외국어 학습 도우미")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📷 원문 입력/분석", "📚 학습하기", "📖 지문 서재", "🔤 나만의 단어장", "📊 학습 대시보드"])
    
    if st.session_state.get("switch_to_tab1", False):
        import streamlit.components.v1 as components
        components.html("""
            <script>
                var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs.length > 1) {
                    tabs[1].click();
                }
            </script>
        """, height=0)
        st.session_state["switch_to_tab1"] = False

    with tab1:
        render_input_view()
        
    with tab2:
        render_learn_view()
        
    with tab3:
        render_library_view()
        
    with tab4:
        render_vocab_view()
        
    with tab5:
        render_dashboard_view()
