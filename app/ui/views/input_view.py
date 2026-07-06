import streamlit as st
import PIL.Image
from streamlit_cropper import st_cropper
from app.agents.parser_agent import ParserAgent
from app.agents.preprocessor_agent import PreprocessorAgent
from app.db.database import get_setting, set_setting, add_passage, check_passage_title_exists
import hashlib
import numpy as np

parser_agent = ParserAgent()
preprocessor_agent = PreprocessorAgent()

def get_image_hash(img_bytes):
    return hashlib.md5(img_bytes).hexdigest()

def get_default_coords(img):
    try:
        gray = img.convert("L")
        arr = np.array(gray)
        dark_pixels = np.argwhere(arr < 240)
        if len(dark_pixels) == 0:
            return None
        y_min, x_min = dark_pixels.min(axis=0)
        y_max, x_max = dark_pixels.max(axis=0)
        
        padding = int(min(img.width, img.height) * 0.02)
        left = max(0, int(x_min) - padding)
        right = min(img.width, int(x_max) + padding)
        top = max(0, int(y_min) - padding)
        bottom = min(img.height, int(y_max) + padding)
        return (left, right, top, bottom)
    except:
        return None

def render_input_view():
    header_left1, header_left2 = st.columns([1, 2.5])
    with header_left1:
        st.subheader("📷 원문 입력")
    with header_left2:
        st.info("태블릿 스크린샷이나 교재 사진을 올리고, 분석할 영역을 지정(Crop)하세요.")

    with st.expander("⚙️ 학습 설정", expanded=False):
        if "student_level" not in st.session_state:
            st.session_state["student_level"] = get_setting(st.session_state["user_id"], "student_level", "중학교 1학년")
        if "target_language" not in st.session_state:
            st.session_state["target_language"] = get_setting(st.session_state["user_id"], "target_language", "한국어")
        if "tts_gender" not in st.session_state:
            st.session_state["tts_gender"] = get_setting(st.session_state["user_id"], "tts_gender", "male")
        if "extract_original" not in st.session_state:
            val = get_setting(st.session_state["user_id"], "extract_original", "True")
            st.session_state["extract_original"] = (val == "True")

        new_level = st.selectbox("🎯 학습 대상 수준", ["초등학교 고학년", "중학교 1학년", "중학교 2학년", "중학교 3학년", "고등학교 1학년", "고등학교 2학년", "고등학교 3학년", "성인 (일반)"], index=["초등학교 고학년", "중학교 1학년", "중학교 2학년", "중학교 3학년", "고등학교 1학년", "고등학교 2학년", "고등학교 3학년", "성인 (일반)"].index(st.session_state["student_level"]))
        if new_level != st.session_state["student_level"]:
            st.session_state["student_level"] = new_level
            set_setting(st.session_state["user_id"], "student_level", new_level)
            st.rerun()

        new_target = st.selectbox("🌐 번역 대상 언어", ["한국어", "영어", "일본어", "중국어", "스페인어", "프랑스어", "독일어"], index=["한국어", "영어", "일본어", "중국어", "스페인어", "프랑스어", "독일어"].index(st.session_state["target_language"]))
        if new_target != st.session_state["target_language"]:
            st.session_state["target_language"] = new_target
            set_setting(st.session_state["user_id"], "target_language", new_target)
            st.rerun()

        new_extract = st.checkbox("✅ 이미지에서 기존 문제(객관식/주관식) 추출하여 보존하기", value=st.session_state["extract_original"], help="체크하면 사진에 포함된 연습문제도 함께 인식하여 '원래 문제 풀기' 기능을 활성화합니다.")
        if new_extract != st.session_state["extract_original"]:
            st.session_state["extract_original"] = new_extract
            set_setting(st.session_state["user_id"], "extract_original", "True" if new_extract else "False")
            st.rerun()

    input_type = st.radio("입력 방식 선택", ["📁 스크린샷 또는 사진 파일 업로드", "📸 카메라 촬영", "📝 텍스트 직접 입력", "📂 공유된 파일 들여오기"], horizontal=True)

    if "merge_buffer" not in st.session_state:
        st.session_state["merge_buffer"] = None

    def handle_analysis(parsed, custom_title, doc_type, do_merge):
        if not st.session_state["merge_buffer"]:
            st.session_state["merge_buffer"] = parsed
        else:
            # Merge logic
            buf = st.session_state["merge_buffer"]
            buf["contents"].extend(parsed.get("contents", []))
            buf["vocabulary"].extend(parsed.get("vocabulary", []))
            buf["original_questions"].extend(parsed.get("original_questions", []))
            if parsed.get("tutor_feedback"):
                buf["tutor_feedback"] = buf.get("tutor_feedback", "") + "\n\n" + parsed.get("tutor_feedback")
            st.session_state["merge_buffer"] = buf
            
        if not do_merge:
            final_data = st.session_state["merge_buffer"]
            st.session_state["parsed_data"] = final_data
            if final_data and "error" not in final_data:
                if st.session_state.get("switch_to_tab1") is None:
                    first_sentence = final_data.get('title', '제목 없음')
                    final_title = f"{custom_title.strip()}_{first_sentence}"
                    add_passage(st.session_state["user_id"], final_title, final_data.get('type', 'reading'), final_data.get('source_language', 'en'), final_data.get('target_language', 'ko'), final_data)
            st.session_state['switch_to_tab1'] = True
            st.session_state["merge_buffer"] = None
        else:
            st.success("현재 페이지가 병합 대기열에 추가되었습니다. 다음 페이지를 분석해주세요.")
        st.rerun()

    def render_preprocessor_ui(img_or_text, input_t):
        if "preprocessed" not in st.session_state:
            st.session_state.preprocessed = {}
        
        # Simple caching
        if input_t == "text":
            data_hash = hashlib.md5(img_or_text.encode('utf-8')).hexdigest()
        else:
            import io
            b = io.BytesIO()
            img_or_text.save(b, format="PNG")
            data_hash = get_image_hash(b.getvalue())

        if data_hash not in st.session_state.preprocessed:
            with st.spinner("AI가 문서 성격을 파악 중입니다..."):
                res = preprocessor_agent.analyze_document_intent(img_or_text if input_t=="image" else img_or_text, input_t)
                st.session_state.preprocessed[data_hash] = res
        
        prep_res = st.session_state.preprocessed[data_hash]
        
        if prep_res.get("document_type") == "irrelevant" or not prep_res.get("is_meaningful_content", True):
            st.warning("⚠️ 학습에 적합한 외국어 자료가 아닌 것 같습니다. (의미없는 이미지나 텍스트)")
            force_proceed = st.checkbox("그래도 강제로 분석 진행하기", value=False)
            if not force_proceed:
                return None, None
        
        st.markdown("---")
        doc_type = prep_res.get("document_type", "reading")
        if doc_type == "ambiguous":
            st.info("💡 똑똑한 분석을 위해 이 문서의 종류를 알려주세요!")
            doc_type = st.radio("문서 성격", ["reading", "test_paper", "handout"], format_func=lambda x: "📖 일반 지문" if x == "reading" else ("📝 시험지" if x == "test_paper" else "📄 해설 유인물"))
            
        custom_title = st.text_input("지문 제목 지정 (AI 추천 제목 적용됨)", value=prep_res.get("title", ""))
        do_merge = st.checkbox("다음 페이지 이어서 병합하기", value=False)
        
        return custom_title, doc_type, do_merge

    if input_type == "📁 스크린샷 또는 사진 파일 업로드":
        uploaded_image = st.file_uploader("파일 업로드", type=["png", "jpg", "jpeg", "pdf"])
        if uploaded_image:
            if uploaded_image.name.lower().endswith('.pdf'):
                try:
                    import fitz  # PyMuPDF
                    import io
                    doc = fitz.open(stream=uploaded_image.read(), filetype="pdf")
                    num_pages = len(doc)
                    max_page = min(num_pages, 10)
                    if num_pages > 10:
                        st.warning(f"📄 PDF가 총 {num_pages}페이지입니다. 시스템 안정성을 위해 처음 10페이지만 추출 및 분석이 지원됩니다.")
                    
                    if max_page > 1:
                        page_num = st.number_input("분석할 페이지 번호 선택", min_value=1, max_value=max_page, value=1)
                    else:
                        page_num = 1
                        
                    page = doc.load_page(page_num - 1)
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    img = PIL.Image.open(io.BytesIO(img_bytes))
                except Exception as e:
                    st.error(f"PDF 파일을 읽는 중 오류가 발생했습니다: {e}")
                    img = None
            else:
                img = PIL.Image.open(uploaded_image)
                
            if img is not None:
                coords = get_default_coords(img)
                cropped_img = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None, default_coords=coords)
                
                res = render_preprocessor_ui(cropped_img, "image")
                if res[0] is not None:
                    custom_title, doc_type, do_merge = res
                    if st.button("🚀 선택 영역 분석 시작", key="btn_img", use_container_width=True):
                        if not custom_title.strip():
                            st.error("지문 제목을 입력해주세요.")
                        else:
                            with st.spinner("AI 분석 중..."):
                                parsed = parser_agent.parse_from_image(cropped_img, doc_type=doc_type, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                                handle_analysis(parsed, custom_title, doc_type, do_merge)

    elif input_type == "📸 카메라 촬영":
        camera_image = st.camera_input("카메라로 교재 촬영")
        if camera_image:
            img = PIL.Image.open(camera_image)
            coords = get_default_coords(img)
            cropped_img = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None, default_coords=coords)
            res = render_preprocessor_ui(cropped_img, "image")
            if res[0] is not None:
                custom_title, doc_type, do_merge = res
                if st.button("🚀 촬영 영역 분석 시작", key="btn_cam", use_container_width=True):
                    if not custom_title.strip():
                        st.error("지문 제목을 입력해주세요.")
                    else:
                        with st.spinner("AI 분석 중..."):
                            parsed = parser_agent.parse_from_image(cropped_img, doc_type=doc_type, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                            handle_analysis(parsed, custom_title, doc_type, do_merge)

    elif input_type == "📝 텍스트 직접 입력":
        input_text = st.text_area("외국어 텍스트 입력", height=200)
        if input_text.strip():
            res = render_preprocessor_ui(input_text, "text")
            if res[0] is not None:
                custom_title, doc_type, do_merge = res
                if st.button("🚀 텍스트 분석 시작", key="btn_txt", use_container_width=True):
                    if not custom_title.strip():
                        st.error("지문 제목을 입력해주세요.")
                    else:
                        with st.spinner("AI 분석 중..."):
                            parsed = parser_agent.parse_from_text(input_text, doc_type=doc_type, extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                            handle_analysis(parsed, custom_title, doc_type, do_merge)

    elif input_type == "📂 공유된 파일 들여오기":
        uploaded_json = st.file_uploader("친구가 공유한 EduAI JSON 파일 업로드", type=["json"])
        if uploaded_json:
            try:
                import json
                parsed = json.load(uploaded_json)
                if "title" in parsed and "contents" in parsed:
                    if st.button("🚀 이 지문으로 학습 시작하기", use_container_width=True):
                        st.session_state["parsed_data"] = parsed
                        add_passage(st.session_state["user_id"], parsed.get('title', '공유된 지문'), parsed.get('type', 'reading'), parsed.get('source_language', 'en'), parsed.get('target_language', 'ko'), parsed)
                        st.session_state['switch_to_tab1'] = True
                        st.rerun()
                else:
                    st.error("올바른 EduAI 지문 공유 파일이 아닙니다.")
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
