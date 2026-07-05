import streamlit as st
from app.db.database import get_all_words, delete_word, get_all_passages, delete_passage, get_passage_by_id
from app.core.tts_engine import generate_audio_sync, get_voice_for_language
import json
import pandas as pd

def render_vocab_view():
    st.write("저장된 지문과 단어를 다시 복습해 보세요!")

    lib_tab, vocab_tab = st.tabs(["📖 지문 서재", "🔤 나만의 단어장"])

    with lib_tab:
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

    with vocab_tab:
        col_voc_title, col_voc_export = st.columns([3, 1])
        with col_voc_title:
            st.markdown("#### 🔤 단어장")
        with col_voc_export:
            all_words = get_all_words(st.session_state["user_id"])
            if all_words:
                df_words = pd.DataFrame(all_words)
                csv_data = df_words.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 단어장 백업 (.csv)", data=csv_data, file_name="my_vocabulary.csv", mime="text/csv", use_container_width=True)

        if not all_words:
            st.info("아직 저장된 단어가 없습니다.")
        else:
            for w in all_words:
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([2, 4, 1, 1])
                    with col1:
                        st.markdown(f"### {w['word']}")
                    with col2:
                        st.markdown(f"**뜻:** {w['meaning']}")
                        if st.session_state.get(f"play_vocab_{w['id']}"):
                            voice = get_voice_for_language(st.session_state.get("target_language", "en"), st.session_state.get("tts_gender", "male"))
                            audio_bytes = generate_audio_sync(w['word'], voice=voice)
                            if audio_bytes:
                                st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                            st.session_state[f"play_vocab_{w['id']}"] = False
                    with col3:
                        if st.button("🔊", key=f"btn_play_{w['id']}", help="발음 듣기"):
                            st.session_state[f"play_vocab_{w['id']}"] = True
                            st.rerun()
                    with col4:
                        if st.button("❌", key=f"btn_del_vocab_{w['id']}", help="단어 삭제"):
                            delete_word(st.session_state["user_id"], w['id'])
                            st.rerun()
