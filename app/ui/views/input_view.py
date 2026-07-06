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

def parse_page_range(range_str, max_page):
    pages = set()
    parts = str(range_str).split(',')
    for part in parts:
        part = part.strip()
        if not part: continue
        if '-' in part:
            bounds = part.split('-')
            if len(bounds) == 2 and bounds[0].isdigit() and bounds[1].isdigit():
                start, end = int(bounds[0]), int(bounds[1])
                pages.update(range(start, end + 1))
        elif part.isdigit():
            pages.add(int(part))
    
    valid_pages = sorted([p for p in pages if 1 <= p <= max_page])
    return valid_pages if valid_pages else [1]

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
        if "translation_style" not in st.session_state:
            st.session_state["translation_style"] = get_setting(st.session_state["user_id"], "translation_style", "자연스러운 번역 (의역)")
        if "translation_tone" not in st.session_state:
            st.session_state["translation_tone"] = get_setting(st.session_state["user_id"], "translation_tone", "경어체 (~해요)")

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

        new_style = st.selectbox("📝 번역 스타일", ["자연스러운 번역 (의역)", "문법 중심 직역"], index=["자연스러운 번역 (의역)", "문법 중심 직역"].index(st.session_state["translation_style"]))
        if new_style != st.session_state["translation_style"]:
            st.session_state["translation_style"] = new_style
            set_setting(st.session_state["user_id"], "translation_style", new_style)
            st.rerun()

        new_tone = st.selectbox("🗣️ 번역 어조", ["경어체 (~해요)", "평어체 (~한다)"], index=["경어체 (~해요)", "평어체 (~한다)"].index(st.session_state["translation_tone"]))
        if new_tone != st.session_state["translation_tone"]:
            st.session_state["translation_tone"] = new_tone
            set_setting(st.session_state["user_id"], "translation_tone", new_tone)
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

    def render_input_options(max_page=1):
        st.markdown("---")
        doc_type = st.radio("문서 성격 선택", ["reading", "test_paper", "handout"], format_func=lambda x: "📖 일반 지문" if x == "reading" else ("📝 시험지" if x == "test_paper" else "📄 해설 유인물"))

        custom_title = st.text_input("지문 제목 지정 (비워두면 AI가 자동 추출합니다)", value="")

        page_range_str = "1"
        do_merge = False
        if max_page > 1:
            st.markdown("##### 📄 다중 페이지 일괄 추출")
            curr_range = st.session_state.get("pdf_page_range", "1")
            page_range_str = st.text_input("분석할 페이지 (예: 1-3, 5)", value=curr_range, key="pdf_page_range")
        else:
            do_merge = st.checkbox("다음 페이지 이어서 추가하기", value=False)
            
        return custom_title, doc_type, do_merge, page_range_str

    def render_two_stage_ui(res, doc=None, coords=None, max_page_for_ui=1, source_type="image", img_or_text=None, input_t="image"):
        custom_title, doc_type, do_merge, page_range_str = res
        
        if "extracted_raw_text" not in st.session_state:
            if st.button("🚀 1단계: 원문 텍스트 추출 시작", key=f"btn_extract_{source_type}", use_container_width=True):
                pages_to_process = parse_page_range(page_range_str, max_page_for_ui) if max_page_for_ui > 1 else [1]
                
                with st.spinner("다중 페이지 원문 일괄 추출 중..." if len(pages_to_process) > 1 else "원문 텍스트 추출 중..."):
                    my_bar = st.progress(0, text="일괄 추출 중...") if len(pages_to_process) > 1 else None
                    combined_text = []
                    extracted_title = custom_title
                    
                    for idx, p in enumerate(pages_to_process):
                        if input_t == "text":
                            prep_p = preprocessor_agent.analyze_document_intent(img_or_text, "text")
                        elif source_type == "cam" or (max_page_for_ui == 1 and idx == 0 and img_or_text is not None):
                            prep_p = preprocessor_agent.analyze_document_intent(img_or_text, "image")
                        else:
                            import io
                            import PIL.Image
                            if doc is not None and coords is not None:
                                p_page = doc.load_page(p - 1)
                                p_pix = p_page.get_pixmap(dpi=150)
                                p_img = PIL.Image.open(io.BytesIO(p_pix.tobytes("png")))
                                left, top, width, height = coords['left'], coords['top'], coords['width'], coords['height']
                                curr_cropped = p_img.crop((left, top, left + width, top + height))
                                prep_p = preprocessor_agent.analyze_document_intent(curr_cropped, "image")
                            else:
                                prep_p = preprocessor_agent.analyze_document_intent(img_or_text, "image")
                                
                        if "error" in prep_p:
                            st.error(f"페이지 {p} 추출 중 오류: {prep_p['error']}")
                        else:
                            combined_text.append(prep_p.get("raw_text", ""))
                            if not extracted_title and prep_p.get("title"):
                                extracted_title = prep_p.get("title")
                                
                        if my_bar:
                            my_bar.progress((idx + 1) / len(pages_to_process), text=f"{p}페이지 추출 완료 ({idx+1}/{len(pages_to_process)})")
                    
                    st.session_state["extracted_raw_text"] = "\n\n".join(combined_text)
                    st.session_state["extracted_doc_type"] = doc_type
                    st.session_state["extracted_custom_title"] = extracted_title if extracted_title else "제목 없음"
                    st.session_state["extracted_do_merge"] = do_merge
                    st.rerun()
        else:
            st.markdown("### 🔍 1단계 완료: 추출된 원문 확인 및 편집")
            
            # AI가 추출한(또는 사용자가 입력했던) 제목을 보여주고 수정할 수 있게 제공
            extracted_title = st.session_state.get("extracted_custom_title", "")
            edited_title = st.text_input("추출된 문서 제목 (수정 가능)", value=extracted_title)
            
            st.info("아래 텍스트 창에서 오류를 직접 수정하거나 불필요한 내용(페이지 번호 등)을 삭제하세요.")
            edited_text = st.text_area("추출된 원문", value=st.session_state["extracted_raw_text"], height=300)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 2단계: 텍스트 편집 완료 및 심층 분석 시작", use_container_width=True):
                    with st.spinner("AI 번역 및 심층 분석 중..."):
                        parsed = parser_agent.parse_from_text(edited_text, doc_type=st.session_state["extracted_doc_type"], extract_original_questions=st.session_state["extract_original"], student_level=st.session_state["student_level"], target_language=st.session_state["target_language"], translation_style=st.session_state["translation_style"], translation_tone=st.session_state["translation_tone"])
                        handle_analysis(parsed, edited_title, st.session_state["extracted_doc_type"], st.session_state["extracted_do_merge"])
                        if "extracted_raw_text" in st.session_state:
                            del st.session_state["extracted_raw_text"]
                            del st.session_state["extracted_doc_type"]
                            del st.session_state["extracted_custom_title"]
                            del st.session_state["extracted_do_merge"]
            with col2:
                if st.button("❌ 취소 및 다시 추출", use_container_width=True):
                    del st.session_state["extracted_raw_text"]
                    st.rerun()

    if input_type == "📁 스크린샷 또는 사진 파일 업로드":
        uploaded_image = st.file_uploader("파일 업로드", type=["png", "jpg", "jpeg", "pdf"])
        if uploaded_image:
            max_page_for_ui = 1
            if uploaded_image.name.lower().endswith('.pdf'):
                try:
                    import fitz  # PyMuPDF
                    import io
                    doc = fitz.open(stream=uploaded_image.read(), filetype="pdf")
                    num_pages = len(doc)
                    max_page_for_ui = min(num_pages, 10)
                    if num_pages > 10:
                        st.warning(f"📄 PDF가 총 {num_pages}페이지입니다. 시스템 안정성을 위해 처음 10페이지만 추출 및 분석이 지원됩니다.")
                    
                    page_num = st.session_state.get("pdf_page_num", 1)
                    if page_num > max_page_for_ui:
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
                box = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None, default_coords=coords, return_type="box")
                cropped_img = img.crop((box['left'], box['top'], box['left'] + box['width'], box['top'] + box['height']))
                
                res = render_input_options(max_page=max_page_for_ui)
                if res[0] is not None:
                    render_two_stage_ui(res, doc=doc if 'doc' in locals() else None, coords=box, max_page_for_ui=max_page_for_ui, source_type="image", img_or_text=cropped_img, input_t="image")

    elif input_type == "📸 카메라 촬영":
        camera_image = st.camera_input("카메라로 교재 촬영")
        if camera_image:
            img = PIL.Image.open(camera_image)
            coords = get_default_coords(img)
            box = st_cropper(img, realtime_update=True, box_color='#0000FF', aspect_ratio=None, default_coords=coords, return_type="box")
            cropped_img = img.crop((box['left'], box['top'], box['left'] + box['width'], box['top'] + box['height']))
            res = render_input_options(max_page=1)
            if res[0] is not None:
                render_two_stage_ui(res, doc=None, coords=None, max_page_for_ui=1, source_type="cam", img_or_text=cropped_img, input_t="image")

    elif input_type == "📝 텍스트 직접 입력":
        input_text = st.text_area("외국어 텍스트 입력", height=200)
        if input_text.strip():
            res = render_input_options(max_page=1)
            render_two_stage_ui(res, doc=None, coords=None, max_page_for_ui=1, source_type="txt", img_or_text=input_text, input_t="text")

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
