import streamlit as st
import PIL.Image
from streamlit_cropper import st_cropper
from app.agents import parser_agent
from app.db.database import get_setting, set_setting, add_passage
from app.ui.result_view import render_parsed_result

def render_learn_view():
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
            if "ai_data_consent" not in st.session_state:
                val = get_setting(st.session_state["user_id"], "ai_data_consent", "False")
                st.session_state["ai_data_consent"] = (val == "True")

            levels = [
                "초등 1학년", "초등 2학년", "초등 3학년", "초등 4학년", "초등 5학년", "초등 6학년",
                "중학교 1학년", "중학교 2학년", "중학교 3학년",
                "고등학교 1학년", "고등학교 2학년", "고등학교 3학년",
                "성인/초급", "성인/중급", "성인/고급"
            ]
            curr_lvl_idx = levels.index(st.session_state["student_level"]) if st.session_state["student_level"] in levels else 6
            
            header_right1, header_right2 = st.columns([1, 1])
            with header_right1:
                new_student_level = st.selectbox("🎓 학생 수준", levels, index=curr_lvl_idx)
            with header_right2:
                lang_opts = ["한국어", "영어", "일본어", "중국어", "스페인어", "프랑스어"]
                curr_lang_idx = lang_opts.index(st.session_state["target_language"]) if st.session_state["target_language"] in lang_opts else 0
                new_target_language = st.selectbox("🗣️ 목표 언어 (번역 언어)", lang_opts, index=curr_lang_idx)
                
            with st.container(border=True):
                st.markdown("##### 튜터 및 AI 설정")
                header_right11, header_right12 = st.columns([1, 1])
                with header_right11:
                    col_s1, col_s2 = st.columns([1, 1])
                    with col_s1:
                        curr_gender_idx = 0 if st.session_state["tts_gender"] == "male" else 1
                        tts_gender_kr = st.radio("🗣️ 성우 선택", ["남성", "여성"], horizontal=True, index=curr_gender_idx)
                        new_gender = "male" if tts_gender_kr == "남성" else "female"
                    with col_s2:
                        new_extract = st.toggle("본문 연습문제 추출", value=st.session_state["extract_original"])
                            
                    st.markdown("---")
                    st.markdown("##### 🤝 데이터 공유 설정")
                    st.info("개인 발음 점수 등 민감 정보를 제외한 학습 지문 원문(텍스트/이미지)을 AI 성능 향상 연구에 제공하는 것에 동의합니다.")
                    new_ai_consent = st.toggle("AI 학습용 익명 데이터 제공 동의", value=st.session_state["ai_data_consent"])

                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        style_opts = ["자연스러운 번역 (의역)", "직역 (문법 구조 파악용)"]
                        curr_style_idx = style_opts.index(st.session_state["translation_style"]) if st.session_state["translation_style"] in style_opts else 0
                        new_style = st.selectbox("🔤 번역 스타일", style_opts, index=curr_style_idx)
                    with col_t2:
                        tone_opts = ["경어체 (~해요)", "평어체 (~한다)"]
                        curr_tone_idx = tone_opts.index(st.session_state["translation_tone"]) if st.session_state["translation_tone"] in tone_opts else 0
                        new_tone = st.selectbox("🗣️ 튜터 말투", tone_opts, index=curr_tone_idx)
            
            if st.button("설정 저장"):
                set_setting(st.session_state["user_id"], "student_level", new_student_level)
                set_setting(st.session_state["user_id"], "target_language", new_target_language)
                set_setting(st.session_state["user_id"], "tts_gender", new_gender)
                set_setting(st.session_state["user_id"], "extract_original", "True" if new_extract else "False")
                set_setting(st.session_state["user_id"], "translation_style", new_style)
                set_setting(st.session_state["user_id"], "translation_tone", new_tone)
                set_setting(st.session_state["user_id"], "ai_data_consent", "True" if new_ai_consent else "False")
                st.session_state["student_level"] = new_student_level
                st.session_state["target_language"] = new_target_language
                st.session_state["tts_gender"] = new_gender
                st.session_state["extract_original"] = new_extract
                st.session_state["translation_style"] = new_style
                st.session_state["translation_tone"] = new_tone
                st.session_state["ai_data_consent"] = new_ai_consent
                st.success("설정이 저장되었습니다!")

        input_type = st.radio("입력 방식 선택", ["🖼️ 갤러리/스크린샷 업로드", "📸 카메라 촬영", "📝 텍스트 직접 입력", "📂 공유된 파일 들여오기"], horizontal=True, label_visibility="collapsed")

        if input_type == "🖼️ 갤러리/스크린샷 업로드":
            uploaded_image = st.file_uploader("스크린샷 또는 사진 파일 업로드 (JPG, PNG)", type=["jpg", "jpeg", "png"])
            if uploaded_image:
                img = PIL.Image.open(uploaded_image)
                cropped_img = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None)
                if st.button("🚀 선택 영역 분석 시작", key="btn_img", use_container_width=True):
                    with st.spinner("AI 분석 중..."):
                        parsed = parser_agent.parse_from_image(cropped_img, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                        st.session_state["parsed_data"] = parsed
                        if parsed and "error" not in parsed:
                            if st.session_state.get("switch_to_tab1") is None: # Prevent duplicate insertion
                                add_passage(st.session_state["user_id"], parsed.get('title', '제목 없음'), parsed.get('type', 'reading'), parsed.get('source_language', 'en'), parsed.get('target_language', 'ko'), parsed)
                        st.rerun()

        elif input_type == "📸 카메라 촬영":
            camera_image = st.camera_input("카메라로 교재 촬영")
            if camera_image:
                img = PIL.Image.open(camera_image)
                cropped_img = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None)
                if st.button("🚀 촬영 영역 분석 시작", key="btn_cam", use_container_width=True):
                    with st.spinner("AI 분석 중..."):
                        parsed = parser_agent.parse_from_image(cropped_img, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                        st.session_state["parsed_data"] = parsed
                        if parsed and "error" not in parsed:
                            if st.session_state.get("switch_to_tab1") is None:
                                add_passage(st.session_state["user_id"], parsed.get('title', '제목 없음'), parsed.get('type', 'reading'), parsed.get('source_language', 'en'), parsed.get('target_language', 'ko'), parsed)
                        st.rerun()

        elif input_type == "📝 텍스트 직접 입력":
            input_text = st.text_area("외국어 텍스트 입력", height=200)
            if st.button("🚀 텍스트 분석 시작", key="btn_txt", use_container_width=True):
                if input_text.strip():
                    with st.spinner("AI 분석 중..."):
                        parsed = parser_agent.parse_from_text(input_text, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                        st.session_state["parsed_data"] = parsed
                        if parsed and "error" not in parsed:
                            if st.session_state.get("switch_to_tab1") is None:
                                add_passage(st.session_state["user_id"], parsed.get('title', '제목 없음'), parsed.get('type', 'reading'), parsed.get('source_language', 'en'), parsed.get('target_language', 'ko'), parsed)
                        st.rerun()

        elif input_type == "📂 공유된 파일 들여오기":
            uploaded_json = st.file_uploader("친구가 공유한 EduAI JSON 파일 업로드", type=["json"])
            if uploaded_json:
                try:
                    import json
                    parsed = json.load(uploaded_json)
                    if "title" in parsed and "sentences" in parsed:
                        if st.button("🚀 이 지문으로 학습 시작하기", use_container_width=True):
                            st.session_state["parsed_data"] = parsed
                            add_passage(st.session_state["user_id"], parsed.get('title', '공유된 지문'), parsed.get('type', 'reading'), parsed.get('source_language', 'en'), parsed.get('target_language', 'ko'), parsed)
                            st.rerun()
                    else:
                        st.error("올바른 EduAI 지문 공유 파일이 아닙니다.")
                except Exception as e:
                    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

    else:
        col_h1, col_h2 = st.columns([1, 2.5])
        with col_h1:
            st.subheader("📝 분석 결과")
        with col_h2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 새로운 지문 분석하기 (돌아가기)", use_container_width=True):
                st.session_state["parsed_data"] = None
                st.rerun()

        render_parsed_result(st.session_state["parsed_data"])
