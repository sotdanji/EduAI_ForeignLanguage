import streamlit as st
from app.db.database import get_all_words, delete_word
from app.core.tts_engine import generate_audio_sync, get_voice_for_language

def render_vocab_view():
    st.write("학습 중 저장한 핵심 어휘들을 복습해 보세요!")

    words = get_all_words(st.session_state["user_id"])
    if not words:
        st.info("아직 저장된 단어가 없습니다.")
    else:
        for w in words:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 4, 1, 1])
                with col1:
                    st.markdown(f"### {w['word']}")
                with col2:
                    st.markdown(f"**뜻:** {w['meaning']}")
                    if st.session_state.get(f"play_vocab_{w['id']}"):
                        voice = get_voice_for_language(st.session_state.get("target_language", "en"), st.session_state.get("tts_gender", "male"))
                        with st.spinner("오디오 생성 중..."):
                            audio_bytes = generate_audio_sync(w['word'], voice)
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        st.session_state[f"play_vocab_{w['id']}"] = False

                with col3:
                    if st.button("🔊 발음", key=f"listen_vocab_{w['id']}"):
                        st.session_state[f"play_vocab_{w['id']}"] = True
                        st.rerun()
                with col4:
                    if st.button("🗑️ 삭제", key=f"del_{w['id']}", use_container_width=True):
                        delete_word(st.session_state["user_id"], w['id'])
                        st.rerun()
