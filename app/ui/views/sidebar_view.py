import streamlit as st
from app.utils.qr import get_local_ip, generate_qr_code

def render_sidebar():
    with st.sidebar:
        st.markdown("### 👤 사용자 정보")
        username = st.session_state.get("username", "Unknown")
        st.write(f"환영합니다, **{username}**님!")
        if st.button("로그아웃", use_container_width=True, help="현재 계정에서 로그아웃합니다."):
            st.session_state["logged_in"] = False
            st.session_state.pop("user_id", None)
            st.session_state.pop("username", None)
            st.rerun()
            
        st.markdown("---")
        st.markdown("### 📱 모바일/태블릿 연동")
        st.write("스마트폰 카메라로 아래 QR을 스캔하면 현재 접속 중인 EduAI로 연결됩니다.")
        
        with st.popover("📱 태블릿 접속 QR 생성", use_container_width=True):
            import os
            public_url = os.getenv("PUBLIC_URL")
            if public_url:
                url = public_url
            else:
                local_ip = get_local_ip()
                port = 8501 # Streamlit 기본 포트
                url = f"http://{local_ip}:{port}"
            
            st.write("QR 코드를 카메라로 스캔하세요:")
            qr_img = generate_qr_code(url)
            st.image(qr_img, use_container_width=True)
            st.info(f"수동 접속 주소:\n{url}")

        st.markdown("---")
        st.markdown("### ❓ 도움말")
        from app.ui.components.manual_dialog import show_manual
        if st.button("📖 사용 설명서 보기", use_container_width=True, help="앱의 기능과 사용 방법을 확인합니다."):
            show_manual()
