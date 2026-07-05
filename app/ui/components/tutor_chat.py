import streamlit as st
import base64
from app.agents import tutor_agent

def render_tutor_chat(data):
    st.subheader("👨‍🏫 AI 튜터와 대화하기 (Q&A & 인터뷰)")
    
    chat_mode_label = st.radio("학생/튜터 모드 선택", ["일반 Q&A 모드 (학생이 질문하기)", "AI 주도 인터뷰 모드 (선생님이 질문하기)"], horizontal=True)
    mode_key = "qa" if "일반" in chat_mode_label else "interview"
    
    if st.session_state.get("current_chat_mode") != mode_key:
        st.session_state.current_chat_mode = mode_key
        if mode_key == "qa":
            st.session_state.chat_history = [{"role": "assistant", "content": "학습하시다 모르는 문법이나 단어가 있다면 언제든 편하게 물어보세요!"}]
        else:
            st.session_state.chat_history = [{"role": "assistant", "content": "지금부터 방금 본문 내용에 대한 인터뷰를 시작하겠습니다. 지문 내용을 잘 이해했는지 확인하기 위해 제가 날카로운 질문을 드릴 테니, 마음의 준비가 되셨다면 '시작'이라고 대답해 주세요!"}]
    
    col_chat1, col_chat2 = st.columns([1, 1])
    with col_chat1:
        st.caption("마이크를 이용해 편하게 음성으로 묻거나 대답할 수 있습니다.")
    with col_chat2:
        voice_reply_mode = st.toggle("🤖 AI 선생님의 대답을 음성으로 듣기", value=False)

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "audio_b64" in msg and msg["audio_b64"]:
                st.audio(base64.b64decode(msg["audio_b64"]), format="audio/mp3")
                
    user_query = st.chat_input("질문을 텍스트로 입력해주세요...")
    audio_value = None
    if hasattr(st, "audio_input"):
        audio_value = st.audio_input("🎤 마이크로 질문하기", key="chat_audio_input")
        
    processed_query = None
    
    if audio_value and st.session_state.get("last_audio_id") != audio_value.file_id:
        st.session_state.last_audio_id = audio_value.file_id
        with st.spinner("음성을 인식하고 있습니다..."):
            from app.agents import pronunciation_agent
            audio_bytes = audio_value.read()
            mime_type = audio_value.type
            recognized_text = pronunciation_agent.transcribe_audio(audio_bytes, mime_type)
            if recognized_text and not recognized_text.startswith("[음성 인식 실패"):
                processed_query = recognized_text
            else:
                st.error("음성을 정상적으로 인식하지 못했습니다. 다시 시도해주세요.")
    elif user_query:
        processed_query = user_query
            
    if processed_query:
        st.session_state.chat_history.append({"role": "user", "content": processed_query})
        with st.chat_message("user"):
            st.markdown(processed_query)
            
        with st.chat_message("assistant"):
            with st.spinner("AI 선생님이 답변을 생성 중입니다..."):
                student_level = st.session_state.get("student_level", "중학교 1학년")
                ai_response = tutor_agent.get_tutor_chat_response(st.session_state.chat_history, data, mode=st.session_state.current_chat_mode, student_level=student_level)
                st.markdown(ai_response)
                
                audio_b64 = None
                if voice_reply_mode:
                    with st.spinner("답변을 음성으로 변환 중입니다..."):
                        from app.core.tts_engine import generate_audio_sync, get_voice_for_language
                        tutor_voice = get_voice_for_language("ko", gender="female")
                        try:
                            audio_bytes = generate_audio_sync(ai_response, tutor_voice)
                            st.audio(audio_bytes, format="audio/mp3")
                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        except Exception as e:
                            st.error(f"음성 변환 실패: {e}")
                
        msg_record = {"role": "assistant", "content": ai_response}
        if audio_b64:
            msg_record["audio_b64"] = audio_b64
        st.session_state.chat_history.append(msg_record)
        st.rerun()
