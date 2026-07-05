import streamlit as st
from app.db.database import get_dashboard_stats, get_recent_pronunciation_scores, get_all_passages, delete_passage, get_passage_by_id, get_all_words
import json
import pandas as pd

def render_dashboard_view():
    st.write("지금까지의 학습 기록을 확인하고 이전 지문을 다시 불러와 복습해 보세요!")

    period_options = ["오늘", "이번 주", "이번 달", "이번 학기", "전체"]
    
    col_filter, col_export1, col_export2 = st.columns([2, 1, 1])
    with col_filter:
        selected_period = st.selectbox("📅 통계 기간 선택", period_options, index=4)
        
    with col_export1:
        # 단어장 CSV 백업
        all_words = get_all_words(st.session_state["user_id"])
        if all_words:
            df_words = pd.DataFrame(all_words)
            csv_data = df_words.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 단어장 백업 (.csv)", data=csv_data, file_name="my_vocabulary.csv", mime="text/csv", use_container_width=True)
            
    with col_export2:
        # 지문 전체 백업
        all_passages = get_all_passages(st.session_state["user_id"])
        if all_passages:
            all_passages_data = []
            for p in all_passages:
                p_data = get_passage_by_id(st.session_state["user_id"], p['id'])
                if p_data:
                    all_passages_data.append(p_data)
            json_data = json.dumps(all_passages_data, ensure_ascii=False, indent=2).encode('utf-8')
            st.download_button("📥 전체 지문 백업 (.json)", data=json_data, file_name="my_passages.json", mime="application/json", use_container_width=True)

    stats = get_dashboard_stats(st.session_state["user_id"], period=selected_period)
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
        st.markdown("#### 📈 최근 발음 점수 추이")
        scores = get_recent_pronunciation_scores(st.session_state["user_id"], period=selected_period)
        if scores:
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
                    scol1, scol2, scol3, scol4 = st.columns([3, 1, 1, 1])
                    with scol1:
                        st.markdown(f"**{p.get('title', '제목 없음')}** ({p.get('type', '타입없음')})")
                        st.caption(f"{p['created_at']}")
                    with scol2:
                        if st.button("📖", key=f"load_p_{p['id']}", help="불러오기"):
                            st.session_state["load_passage_id"] = p['id']
                            st.rerun()
                    with scol3:
                        p_data = get_passage_by_id(st.session_state["user_id"], p['id'])
                        if p_data:
                            json_str = json.dumps(p_data, ensure_ascii=False, indent=2).encode('utf-8')
                            st.download_button("🔗", data=json_str, file_name=f"shared_passage_{p['id']}.json", mime="application/json", key=f"share_p_{p['id']}", help="친구에게 공유하기 (.json 다운로드)")
                    with scol4:
                        if st.button("❌", key=f"del_p_{p['id']}", help="삭제"):
                            delete_passage(st.session_state["user_id"], p['id'])
                            st.rerun()
