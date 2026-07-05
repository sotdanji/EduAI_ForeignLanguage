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
    
    tab1, tab2, tab3 = st.tabs(["📚 학습하기", "📝 나의 서재 (복습)", "📊 학습 대시보드"])
    
    with tab1:
        render_learn_view()
        
    with tab2:
        render_vocab_view()
        
    with tab3:
        render_dashboard_view()
