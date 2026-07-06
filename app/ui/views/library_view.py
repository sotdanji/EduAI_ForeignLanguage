import streamlit as st
from app.db.database import get_all_passages, get_passage_by_id, delete_passage
import json

def render_library_view():
    st.write("지금까지의 학습 기록을 확인하고 이전 지문을 다시 불러와 복습해 보세요!")

    col_lib_title, col_lib_export = st.columns([3, 1])
    with col_lib_title:
        st.markdown("#### 📚 나의 서재 (과거 학습 기록)")
    with col_lib_export:
        all_passages = get_all_passages(st.session_state["user_id"])
        if all_passages:
            all_passages_data = []
            for p in all_passages:
                p_data = get_passage_by_id(st.session_state["user_id"], p['id'])
                if p_data:
                    all_passages_data.append(p_data)
            json_data = json.dumps(all_passages_data, ensure_ascii=False, indent=2).encode('utf-8')
            st.download_button("📥 전체 지문 백업 (.json)", data=json_data, file_name="my_passages.json", mime="application/json", use_container_width=True)

    if not all_passages:
        st.info("저장된 지문이 없습니다.")
    else:
        for p in all_passages:
            with st.container(border=True):
                scol1, scol2, scol3, scol4 = st.columns([4, 1, 1, 1])
                with scol1:
                    t_val = p.get('type', 'reading')
                    type_str = "📖 일반 지문" if t_val == 'reading' else ("📝 시험지" if t_val == 'test_paper' else ("📄 해설 유인물" if t_val == 'handout' else t_val))
                    st.markdown(f"**{p.get('title', '제목 없음')}** ({type_str})")
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
