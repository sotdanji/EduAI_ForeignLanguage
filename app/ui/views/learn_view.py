import streamlit as st
from app.ui.result_view import render_parsed_result

def render_learn_view():
    if not st.session_state.get("parsed_data"):
        st.info("아직 분석된 지문이 없습니다. [📷 원문 입력/분석] 탭에서 먼저 지문을 분석해주세요.")
    else:
        # 1번 탭(input_view.py)으로 이동하는 버튼은 여기에 없어도 됨 (상단 탭이 5개로 분리되었으므로)
        render_parsed_result(st.session_state["parsed_data"])
