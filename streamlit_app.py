import streamlit as st
import os
from dotenv import load_dotenv
import PIL.Image
from streamlit_cropper import st_cropper

import sys
import importlib

# 강제 모듈 리로드 (Streamlit 캐싱 방지)
if "app.core.llm_engine" in sys.modules:
    importlib.reload(sys.modules["app.core.llm_engine"])
if "app.ui.result_view" in sys.modules:
    importlib.reload(sys.modules["app.ui.result_view"])
if "app.db.database" in sys.modules:
    importlib.reload(sys.modules["app.db.database"])

from app.core.llm_engine import get_parsed_content_from_text, get_parsed_content_from_image, configure_gemini
from app.ui.result_view import render_parsed_result
from app.db.database import init_db, get_all_words, delete_word, add_passage, get_all_passages, get_passage_by_id, get_dashboard_stats, get_recent_pronunciation_scores, get_setting, set_setting, register_user, authenticate_user
from app.utils.qr import get_local_ip, generate_qr_code

load_dotenv()
configure_gemini()
init_db()

if "parsed_data" not in st.session_state:
    st.session_state["parsed_data"] = None

# 모바일 대응을 위해 레이아웃을 wide로 설정 (유연한 반응형)
st.set_page_config(page_title="EduAI 튜터", page_icon="📖", layout="wide")

# 가독성을 위해 파란박스(info) 및 UI 텍스트를 완전한 검정색(#000000)으로 강제 적용
st.markdown("""
<style>
    /* 화면 상단 여백 최소화 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    div[data-testid="stAlert"] p {
        color: #000000 !important;
    }
    .stMarkdown p {
        color: #000000 !important;
    }
    div[data-testid="stExpander"] summary p {
        color: #000000 !important;
        font-size: 16px !important;
    }
    /* 위젯 라벨(업로더, 텍스트에어리어 등) */
    div[data-testid="stWidgetLabel"] p {
        color: #000000 !important;
        font-size: 16px !important;
        font-weight: 400 !important;
    }
    /* 라디오 버튼, 체크박스, 토글 라벨 */
    div[data-testid="stRadio"] label div, 
    div[data-testid="stCheckbox"] label div, 
    label[data-baseweb="radio"] div, 
    label[data-baseweb="checkbox"] div {
        color: #000000 !important;
        font-size: 16px !important;
    }
    /* 파일 업로더 내부 안내 텍스트들 */
    div[data-testid="stFileUploaderDropzoneInstructions"] div, small {
        color: #000000 !important;
        font-size: 16px !important;
    }
</style>
""", unsafe_allow_html=True)

def render_intro_page():
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🚀 EduAI에 오신 것을 환영합니다!</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>찍고, 듣고, 말하는 나만의 꼬마 AI 외국어 선생님</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2 = st.columns([1.5, 1], gap="large")
    
    with col1:
        st.subheader("✨ EduAI는 어떤 서비스인가요?")
        st.markdown("""
        * **📸 모르는 문제, 찍기만 하세요!** 교과서나 문제집의 모르는 부분을 사진으로 올리면 AI가 번역과 문법 해설을 제공합니다.
        * **🗣️ 원어민 선생님과 롤플레잉:** 대화문을 롤플레잉 방식으로 연습하고 내 발음에 대한 상세한 피드백을 받아보세요.
        * **📚 나만의 단어장 & 서재:** 한 번 공부한 내용은 평생 내 서재에 보관되어 언제든 복습할 수 있습니다.
        """)
        st.info("👇 아래 소개 영상을 통해 EduAI의 놀라운 기능들을 확인해 보세요!")
        # 임시 홍보 영상 (저작권 없는 더미 비디오 또는 무료 안내 영상)
        st.video("https://www.youtube.com/watch?v=hB2JdE2PteQ") # Example dummy nature/educational video
        
    with col2:
        with st.container(border=True):
            tab_login, tab_register = st.tabs(["🔑 로그인", "📝 회원가입"])
            
            with tab_login:
                st.subheader("로그인")
                login_user = st.text_input("아이디", key="login_user")
                login_pw = st.text_input("비밀번호", type="password", key="login_pw")
                if st.button("🚀 로그인", use_container_width=True):
                    user_id = authenticate_user(login_user, login_pw)
                    if user_id:
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = user_id
                        st.session_state["username"] = login_user
                        st.toast("로그인 성공!", icon="✅")
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
                        
            with tab_register:
                st.subheader("회원가입")
                reg_user = st.text_input("새 아이디", key="reg_user")
                reg_pw = st.text_input("새 비밀번호", type="password", key="reg_pw")
                reg_pw_confirm = st.text_input("비밀번호 확인", type="password", key="reg_pw_confirm")
                
                if st.button("✨ 가입하기", use_container_width=True):
                    if not reg_user or not reg_pw:
                        st.error("아이디와 비밀번호를 모두 입력해주세요.")
                    elif reg_pw != reg_pw_confirm:
                        st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        new_user_id = register_user(reg_user, reg_pw)
                        if new_user_id:
                            st.success("회원가입이 완료되었습니다! 로그인 탭에서 로그인해주세요.")
                        else:
                            st.error("이미 존재하는 아이디거나 오류가 발생했습니다.")

def render_main_app():
    def load_passage_callback(passage_id, title):
        loaded_json = get_passage_by_id(st.session_state["user_id"], passage_id)
        if loaded_json:
            st.session_state["parsed_data"] = loaded_json
            st.session_state["switch_to_tab1"] = True
            # st.toast is usually fine in callbacks, but Streamlit toasts sometimes act weird in callbacks.
            # We can leave it out or keep it. Let's keep it in session state if needed, or just skip toast for now.


    st.title("EduAI: 개인화된 AI 외국어 튜터")
    st.write("초중고 학생을 위한 반응형 스마트 학습 플랫폼입니다. 모르는 문장이나 문제를 자르면 AI가 핀셋 과외를 해줍니다!")
    st.markdown("<hr style='margin-top: 0.5rem; margin-bottom: 1rem;'/>", unsafe_allow_html=True)

    # 가로형 분할 뷰 (태블릿 최적화) 및 탭 구성
    if "switch_to_tab1" in st.session_state and st.session_state["switch_to_tab1"]:
        import streamlit.components.v1 as components
        components.html('''
            <script>
                const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs.length > 0) {
                    tabs[0].click();
                }
            </script>
        ''', height=0)
        st.session_state["switch_to_tab1"] = False

    tab_learn, tab_vocab, tab_dashboard = st.tabs(["📖 AI 튜터 학습", "📚 나만의 단어장", "📊 학습 대시보드 & 서재"])

    with tab_learn:
        if not st.session_state.get("parsed_data"):

            header_left1, header_left2 = st.columns([1, 2.5])
            with header_left1:
                st.subheader("📷 원문 입력")
            with header_left2:
                st.info("태블릿 스크린샷이나 교재 사진을 올리고, 분석할 영역을 지정(Crop)하세요.")

            with st.expander("⚙️ 학습 설정", expanded=False):
                # DB에서 초기값 불러오기
                if "student_level" not in st.session_state:
                    st.session_state["student_level"] = get_setting(st.session_state["user_id"], "student_level", "중학교 1학년")
                if "target_language" not in st.session_state:
                    st.session_state["target_language"] = get_setting(st.session_state["user_id"], "target_language", "한국어")
                if "tts_gender" not in st.session_state:
                    st.session_state["tts_gender"] = get_setting(st.session_state["user_id"], "tts_gender", "male")
                if "extract_original" not in st.session_state:
                    val = get_setting(st.session_state["user_id"], "extract_original", "True")
                    st.session_state["extract_original"] = (val == "True")
                if "translation_style" not in st.session_state:
                    st.session_state["translation_style"] = get_setting(st.session_state["user_id"], "translation_style", "자연스러운 번역 (의역)")
                if "translation_tone" not in st.session_state:
                    st.session_state["translation_tone"] = get_setting(st.session_state["user_id"], "translation_tone", "경어체 (~해요)")

                levels = [
                    "초등 1학년", "초등 2학년", "초등 3학년", "초등 4학년", "초등 5학년", "초등 6학년",
                    "중학교 1학년", "중학교 2학년", "중학교 3학년",
                    "고등학교 1학년", "고등학교 2학년", "고등학교 3학년"
                ]
                curr_level_idx = levels.index(st.session_state["student_level"]) if st.session_state["student_level"] in levels else 6
                new_student_level = st.selectbox("🎓 학생 학년 수준", levels, index=curr_level_idx)
                if new_student_level != st.session_state["student_level"]:
                    st.session_state["student_level"] = new_student_level
                    set_setting("student_level", new_student_level)

                target_languages = ["한국어", "영어", "일본어", "중국어", "스페인어", "프랑스어", "독일어", "러시아어"]
                curr_lang_idx = target_languages.index(st.session_state["target_language"]) if st.session_state["target_language"] in target_languages else 0
                new_target_language = st.selectbox("🌐 목표 언어 (번역 대상)", target_languages, index=curr_lang_idx)
                if new_target_language != st.session_state["target_language"]:
                    st.session_state["target_language"] = new_target_language
                    set_setting("target_language", new_target_language)

                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    curr_gender_idx = 0 if st.session_state["tts_gender"] == "male" else 1
                    tts_gender_kr = st.radio("🗣️ 성우 선택", ["남성", "여성"], horizontal=True, index=curr_gender_idx)
                    new_gender = "male" if tts_gender_kr == "남성" else "female"
                with col_s2:
                    new_extract = st.toggle("원문 연습문제 추출", value=st.session_state["extract_original"])
                        
                st.markdown("---")
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    style_opts = ["자연스러운 번역 (의역)", "직역 (문법 구조 파악용)"]
                    curr_style_idx = style_opts.index(st.session_state["translation_style"]) if st.session_state["translation_style"] in style_opts else 0
                    new_style = st.selectbox("🔤 번역 스타일", style_opts, index=curr_style_idx)
                with col_t2:
                    tone_opts = ["경어체 (~해요)", "평어체 (~한다)"]
                    curr_tone_idx = tone_opts.index(st.session_state["translation_tone"]) if st.session_state["translation_tone"] in tone_opts else 0
                    new_tone = st.selectbox("💬 번역 문체", tone_opts, index=curr_tone_idx)
                
                if st.button("설정 저장"):
                    set_setting(st.session_state["user_id"], "student_level", new_student_level)
                    set_setting(st.session_state["user_id"], "target_language", new_target_language)
                    set_setting(st.session_state["user_id"], "tts_gender", new_gender)
                    set_setting(st.session_state["user_id"], "extract_original", "True" if new_extract else "False")
                    set_setting(st.session_state["user_id"], "translation_style", new_style)
                    set_setting(st.session_state["user_id"], "translation_tone", new_tone)
                    st.session_state["student_level"] = new_student_level
                    st.session_state["target_language"] = new_target_language
                    st.session_state["tts_gender"] = new_gender
                    st.session_state["extract_original"] = new_extract
                    st.session_state["translation_style"] = new_style
                    st.session_state["translation_tone"] = new_tone
                    st.success("설정이 저장되었습니다!")

            input_type = st.radio("입력 방식 선택", ["🖼️ 갤러리/스크린샷 업로드", "📸 카메라 촬영", "📝 텍스트 직접 입력"], horizontal=True, label_visibility="collapsed")

            if input_type == "🖼️ 갤러리/스크린샷 업로드":
                uploaded_image = st.file_uploader("스크린샷 또는 사진 파일 업로드 (JPG, PNG)", type=["jpg", "jpeg", "png"])
                if uploaded_image:
                    img = PIL.Image.open(uploaded_image)
                    cropped_img = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None)
                    if st.button("🚀 선택 영역 분석 시작", key="btn_img", use_container_width=True):
                        with st.spinner("AI 분석 중..."):
                            parsed = get_parsed_content_from_image(cropped_img, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                            st.session_state["parsed_data"] = parsed
                            if parsed and "error" not in parsed:
                                add_passage(st.session_state["user_id"], parsed.get('title', '제목 없음'), parsed.get('type', 'reading'), parsed.get('source_language', 'en'), parsed.get('target_language', 'ko'), parsed)

            elif input_type == "📸 카메라 촬영":
                camera_image = st.camera_input("카메라로 교재 촬영")
                if camera_image:
                    img = PIL.Image.open(camera_image)
                    cropped_img = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None)
                    if st.button("🚀 촬영 영역 분석 시작", key="btn_cam", use_container_width=True):
                        with st.spinner("AI 분석 중..."):
                            parsed = get_parsed_content_from_image(cropped_img, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                            st.session_state["parsed_data"] = parsed
                            if parsed and "error" not in parsed:
                                add_passage(st.session_state["user_id"], parsed.get('title', '제목 없음'), parsed.get('type', 'reading'), parsed.get('source_language', 'en'), parsed.get('target_language', 'ko'), parsed)

            else:
                input_text = st.text_area("외국어 텍스트 입력", height=200)
                if st.button("🚀 텍스트 분석 시작", key="btn_txt", use_container_width=True):
                    if input_text.strip():
                        with st.spinner("AI 분석 중..."):
                            parsed = get_parsed_content_from_text(input_text, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                            st.session_state["parsed_data"] = parsed
                            if parsed and "error" not in parsed:
                                add_passage(st.session_state["user_id"], parsed.get('title', '제목 없음'), parsed.get('type', 'reading'), parsed.get('source_language', 'en'), parsed.get('target_language', 'ko'), parsed)

        else:
            col_h1, col_h2 = st.columns([1, 2.5])
            with col_h1:
                st.subheader("💡 AI 튜터 피드백")
            with col_h2:
                if st.button("⬅️ 다른 지문 입력하기 (초기화)"):
                    st.session_state["parsed_data"] = None
                    st.rerun()

            render_parsed_result(st.session_state["parsed_data"])

    with tab_vocab:
        st.header("📚 나만의 단어장")
        words = get_all_words(st.session_state["user_id"])
        if not words:
            st.info("아직 저장된 단어가 없습니다.")
        else:
            from app.core.tts_engine import generate_audio_sync, get_voice_for_language
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

    with tab_dashboard:
        st.header("📊 학습 대시보드 & 서재")
        stats = get_dashboard_stats(st.session_state["user_id"])
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.metric(label="총 분석 지문 수", value=f"{stats['total_passages']} 개")
        with col_d2:
            st.metric(label="나만의 단어장", value=f"{stats['total_words']} 단어")
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
                        c1, c2 = st.columns([4, 1])
                        with c1:
                            st.markdown(f"**{p['title']}**")
                            st.caption(f"{p['source_language']} → {p['target_language']} | {p['type']} | {p['created_at']}")
                        with c2:
                            st.button("🔄 복습", key=f"load_passage_{p['id']}", 
                                      on_click=load_passage_callback, args=(p['id'], p['title']))
# --- 메인 라우팅 로직 ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    render_intro_page()
else:
    with st.sidebar:
        st.markdown("### 👤 사용자 정보")
        username = st.session_state.get("username", "Unknown")
        st.write(f"환영합니다, **{username}**님!")
        if st.button("로그아웃", use_container_width=True):
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
            
    render_main_app()
