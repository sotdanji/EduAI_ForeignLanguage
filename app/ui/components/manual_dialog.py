import streamlit as st
import os

@st.dialog("📖 EduAI 사용 설명서", width="large")
def show_manual():
    # 현재 파일 위치에서 프로젝트 루트에 있는 user_manual.md 파일 경로 찾기
    manual_path = os.path.join(os.path.dirname(__file__), "../../../user_manual.md")
    try:
        with open(manual_path, "r", encoding="utf-8") as f:
            content = f.read()
        st.markdown(content)
    except Exception as e:
        st.error(f"설명서를 불러오는 중 오류가 발생했습니다: {e}")
