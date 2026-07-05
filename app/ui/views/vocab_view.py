import streamlit as st
from app.db.database import get_all_words, delete_word
from app.core.tts_engine import generate_audio_sync, get_voice_for_language
import pandas as pd

def render_vocab_view():
    st.write("학습 중 저장한 핵심 어휘들을 복습해 보세요!")

    col_voc_title, col_voc_export = st.columns([3, 1])
    with col_voc_title:
        st.markdown("#### 🔤 나만의 단어장")
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
