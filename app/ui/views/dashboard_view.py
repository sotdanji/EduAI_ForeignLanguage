import streamlit as st
from app.db.database import get_dashboard_stats, get_recent_pronunciation_scores, get_all_passages, delete_passage

def render_dashboard_view():
    st.write("지금까지의 학습 기록을 확인하고 이전 지문을 다시 불러와 복습해 보세요!")

    stats = get_dashboard_stats(st.session_state["user_id"])
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.metric(label="총 분석 지문 수", value=f"{stats['total_passages']} 개")
    with col_d2:
        st.metric(label="저장한 단어 수", value=f"{stats['total_words']} 개")
    with col_d3:
        st.metric(label="발음 점수 평균", value=f"{stats['avg_score']} 점")

    st.markdown("---")
    db_col1, db_col2 = st.columns([1, 1], gap="large")

    with db_col1:
        st.markdown("#### 🎯 최근 발음 점수 추이")
        scores = get_recent_pronunciation_scores(st.session_state["user_id"])
        if scores:
            import pandas as pd
            df_scores = pd.DataFrame(scores)
            st.line_chart(df_scores, y="score")
        else:
            st.info("아직 발음 연습 기록이 없습니다.")

    with db_col2:
        st.markdown("#### 📚 내 서재 (과거 학습 기록)")
        passages = get_all_passages(st.session_state["user_id"])
        if not passages:
            st.info("저장된 지문이 없습니다.")
        else:
            for p in passages:
                with st.container(border=True):
                    scol1, scol2, scol3 = st.columns([3, 1, 1])
                    with scol1:
                        st.markdown(f"**{p.get('title', '제목 없음')}** ({p.get('type', '알 수 없음')})")
                        st.caption(f"{p['created_at']}")
                    with scol2:
                        if st.button("📖", key=f"load_p_{p['id']}"):
                            st.session_state["load_passage_id"] = p['id']
                            st.rerun()
                    with scol3:
                        if st.button("🗑️", key=f"del_p_{p['id']}"):
                            delete_passage(st.session_state["user_id"], p['id'])
                            st.rerun()
