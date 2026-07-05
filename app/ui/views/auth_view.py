import streamlit as st
from app.db.database import authenticate_user, register_user

def render_auth_view():
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🚀 EduAI에 오신 것을 환영합니다!</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>찍고, 듣고, 말하는 EduAI 나의 창의적 학습 도우미 외국어 선생님</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns([1.5, 1], gap="large")
    
    with col1:
        st.markdown("""
        ### 🚨 아직도 눈으로만 언어를 배우시나요?
        대부분의 프로그램은 정해진 커리큘럼만 수동적으로 따라가며, 로봇 같은 TTS 목소리에 내 발음을 교정받을 기회조차 없습니다.

        ### 🚀 학습 주도권을 학생에게!
        EduAI는 다릅니다. **내가 지금 궁금한 것, 내가 지금 공부하고 있는 교재**가 곧 최고의 커리큘럼이 됩니다! 진정한 학습 주도권을 돌려드립니다.

        *   **📸 찍기만 하면 마법처럼 해설이 뚝딱!** 모르는 교재를 찍으면 내 수준에 맞춰 완벽한 번역과 문법 해설을 제공합니다.
        *   **🗣️ 진짜 사람과 대화하는 듯한 AI 튜터:** 원어민의 감정까지 담은 목소리로 읽어주고, 때로는 날카로운 인터뷰 모드로 나의 이해도를 점검합니다.
        *   **🎤 내 발음을 1:1로 밀착 교정:** 3단계 섀도잉 훈련과 점수화된 발음 피드백으로 완벽해질 때까지 훈련시킵니다.
        
        💡 **지금 바로 로그인하고, 나만의 똑똑한 1:1 과외 선생님을 고용해 보세요!**
        """)
        
        from app.ui.components.manual_dialog import show_manual
        if st.button("📖 EduAI 자세한 사용 설명서 보기", use_container_width=True):
            show_manual()
        
    with col2:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔑 로그인", "📝 회원가입"])
            
            with tab_login:
                st.subheader("로그인")
                login_user = st.text_input("아이디", key="login_user")
                login_pw = st.text_input("비밀번호", type="password", key="login_pw")
                if st.button("🔓 로그인", use_container_width=True):
                    # 엔터키 등으로 인한 공백/줄바꿈 문자 제거
                    clean_user = login_user.strip()
                    clean_pw = login_pw.strip()
                    user_id = authenticate_user(clean_user, clean_pw)
                    if user_id:
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = user_id
                        st.session_state["username"] = clean_user
                        st.toast("로그인 성공!", icon="🎉")
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
                        
            with tab_register:
                st.subheader("회원가입")
                reg_user = st.text_input("새 아이디", key="reg_user")
                reg_pw = st.text_input("새 비밀번호", type="password", key="reg_pw")
                reg_pw_confirm = st.text_input("비밀번호 확인", type="password", key="reg_pw_confirm")
                
                if st.button("📝 가입하기", use_container_width=True):
                    clean_reg_user = reg_user.strip()
                    clean_reg_pw = reg_pw.strip()
                    clean_reg_pw_confirm = reg_pw_confirm.strip()
                    
                    if not clean_reg_user or not clean_reg_pw:
                        st.error("아이디와 비밀번호를 모두 입력해주세요.")
                    elif clean_reg_pw != clean_reg_pw_confirm:
                        st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        new_user_id = register_user(clean_reg_user, clean_reg_pw)
                        if new_user_id:
                            st.success("회원가입이 완료되었습니다! 로그인 탭에서 로그인해주세요.")
                        else:
                            st.error("이미 존재하는 아이디이거나 오류가 발생했습니다.")
