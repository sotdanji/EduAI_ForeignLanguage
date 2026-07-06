import streamlit as st
from typing import Dict, Any

def render_parsed_result(data: Dict[str, Any]):
    """파싱된 JSON 데이터를 Streamlit UI 컴포넌트로 변환하여 화면에 그립니다."""
    
    if "error" in data:
        st.error(f"데이터 파싱 중 오류가 발생했습니다: {data['error']}")
        return

    # 1. 헤더 (제목)
    title = data.get("title", "EduAI 학습 자료")
    st.header(f"📖 {title}")
    st.markdown("---")

    # 2. 과외 선생님 피드백 (필기 분석 및 크롭 해설)
    tutor_feedback = data.get("tutor_feedback", "")
    if tutor_feedback:
        st.success(f"👨‍🏫 **AI 선생님의 밀착 피드백**\n\n{tutor_feedback}")
        st.markdown("---")

    import base64
    import json
    import streamlit.components.v1 as components
    from app.core.tts_engine import generate_audio_sync, get_voice_for_language

    is_test_paper = data.get("type") in ["test_paper", "handout"]
    
    if is_test_paper:
        st.markdown("### 📝 시험지 / 유인물 원문")
        st.info("시험지나 유인물은 전체를 한 번에 분석하지 않습니다. 아래 원문에서 **학습하고 싶은 부분만 드래그해서 복사**한 뒤, 바로 아래의 [부분 학습 창]에 붙여넣으세요!")
        st.markdown(f"```text\n{data.get('raw_text', '')}\n```")
        st.markdown("---")
        
        st.markdown("### 🔍 집중 학습할 텍스트 입력")
        pasted_text = st.text_area("위 원문에서 학습할 영어 문장/지문을 복사해서 여기에 붙여넣으세요.", height=150, key="partial_text_input")
        
        if st.button("🚀 이 부분만 집중 학습하기", use_container_width=True):
            if not pasted_text.strip():
                st.error("학습할 텍스트를 입력해주세요.")
            else:
                with st.spinner("선택한 부분 집중 분석 중..."):
                    from app.agents import parser_agent
                    # partial parsed result
                    partial_parsed = parser_agent.parse_from_text(pasted_text, doc_type="reading")
                    st.session_state["partial_analysis"] = partial_parsed
                    
        if "partial_analysis" in st.session_state:
            data = st.session_state["partial_analysis"]
            st.markdown("---")
            st.subheader("🎯 부분 학습 분석 결과")
        else:
            # 부분 학습 결과가 아직 없으면 여기서 렌더링 종료
            return

    # 3. 본문 (Reading/Dialogue)
    contents = data.get("contents", [])
    if contents:
        # 오디오 캐싱 (스트림릿 리렌더링 시 재생성 방지 및 성별 변경 시 캐시 무효화)
        current_gender = st.session_state.get("tts_gender", "male")
        if "audio_b64_source_list" not in data or data.get("audio_voice_gender") != current_gender:
            source_lang = data.get("source_language", "en")
            target_lang = data.get("target_language", "ko")
            source_voice = get_voice_for_language(source_lang, gender=current_gender)
            target_voice = get_voice_for_language(target_lang, gender=current_gender)
            audio_b64_source_list = []
            audio_b64_target_list = []
            
            with st.spinner("본문 오디오를 생성 중입니다... (최초 1회 또는 설정 변경 시)"):
                for line in contents:
                    source_text = line.get("source_text", "")
                    target_text = line.get("target_text", "")
                    
                    if source_text.strip():
                        try:
                            audio_bytes = generate_audio_sync(source_text, source_voice)
                            audio_b64_source_list.append(base64.b64encode(audio_bytes).decode('utf-8'))
                        except:
                            audio_b64_source_list.append("")
                    else:
                        audio_b64_source_list.append("")
                        
                    if target_text.strip():
                        try:
                            audio_bytes = generate_audio_sync(target_text, target_voice)
                            audio_b64_target_list.append(base64.b64encode(audio_bytes).decode('utf-8'))
                        except:
                            audio_b64_target_list.append("")
                    else:
                        audio_b64_target_list.append("")
                        
            data["audio_b64_source_list"] = audio_b64_source_list
            data["audio_b64_target_list"] = audio_b64_target_list
            data["audio_voice_gender"] = current_gender

        audio_b64_source_list = data["audio_b64_source_list"]
        audio_b64_target_list = data["audio_b64_target_list"]

        edit_mode = st.toggle("✏️ 본문 문장 수정 모드")
        
        if edit_mode:
            st.info("문장을 수정하고 엔터를 치면, 해당 문장의 발음 오디오가 즉시 재생성됩니다.")
            for i, line in enumerate(contents):
                st.markdown(f"**[{i+1}번 문장]**")
                
                # 원문 수정
                old_src = line.get("source_text", "")
                new_src = st.text_input("원문", value=old_src, key=f"edit_src_{i}")
                if new_src != old_src:
                    data["contents"][i]["source_text"] = new_src
                    source_lang = data.get("source_language", "en")
                    voice = get_voice_for_language(source_lang, gender=current_gender)
                    with st.spinner("원문 오디오 재생성 중..."):
                        if new_src.strip():
                            try:
                                audio_bytes = generate_audio_sync(new_src, voice)
                                data["audio_b64_source_list"][i] = base64.b64encode(audio_bytes).decode('utf-8')
                            except:
                                data["audio_b64_source_list"][i] = ""
                        else:
                            data["audio_b64_source_list"][i] = ""
                    st.rerun()

                # 번역문 수정
                old_tgt = line.get("target_text", "")
                new_tgt = st.text_input("번역문", value=old_tgt, key=f"edit_tgt_{i}")
                if new_tgt != old_tgt:
                    data["contents"][i]["target_text"] = new_tgt
                    target_lang = data.get("target_language", "ko")
                    voice = get_voice_for_language(target_lang, gender=current_gender)
                    with st.spinner("번역문 오디오 재생성 중..."):
                        if new_tgt.strip():
                            try:
                                audio_bytes = generate_audio_sync(new_tgt, voice)
                                data["audio_b64_target_list"][i] = base64.b64encode(audio_bytes).decode('utf-8')
                            except:
                                data["audio_b64_target_list"][i] = ""
                        else:
                            data["audio_b64_target_list"][i] = ""
                    st.rerun()
                st.markdown("---")
            return # 수정 모드일 때는 아래 HTML 플레이어를 그리지 않음

        html_content = f"""
        <div style="display: flex; flex-direction: column; height: 100vh; margin: 0; padding: 0;">
            <div id="sticky-header" style="flex: 0 0 auto; background: white; z-index: 100; padding: 10px; border-bottom: 1px solid #e6e6e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 10px;">
                <!-- Title Row -->
                <div>
                    <h3 style="margin: 0; font-family: sans-serif; color: #31333F; font-size: 1.5rem; font-weight: 600;">📝 본문 지문</h3>
                </div>
                
                <!-- Controls Row -->
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <!-- Box 1: View Options -->
                    <div style="background: #fcfcfc; border: 1px solid #ddd; border-radius: 8px; padding: 8px 12px; font-family: sans-serif; font-size: 13px; color: #333; display: flex; flex-direction: column; justify-content: center; gap: 8px; min-width: 160px;">
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <strong style="width: 35px; color:#555;">모드:</strong>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="textMode" value="translate" checked onchange="updateDisplay()"> 번역</label>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="textMode" value="compose" onchange="updateDisplay()"> 작문</label>
                        </div>
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <strong style="width: 35px; color:#555;">표시:</strong>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="checkbox" id="show-src" checked onchange="updateDisplay()"> 원문 보기</label>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="checkbox" id="show-tgt" checked onchange="updateDisplay()"> 번역(작문) 보기</label>
                        </div>
                        <div style="display: flex; gap: 12px; align-items: center; margin-top: 5px;">
                            <strong style="width: 35px; color:#555;">훈련:</strong>
                            <label style="cursor:pointer; white-space: nowrap; color: #d32f2f; font-weight: bold;"><input type="checkbox" id="blind-mode" onchange="toggleBlindMode()"> 🎧 블라인드 모드 (듣기 평가)</label>
                        </div>
                    </div>
                    
                    <!-- Box 2: Audio Options -->
                    <div style="background: #eef7ff; border: 1px solid #bce0fd; border-radius: 8px; padding: 8px 12px; font-family: sans-serif; font-size: 13px; color: #333; display: flex; align-items: center; gap: 15px; flex-wrap: wrap; flex: 1; min-width: 280px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <strong style="color:#1976d2;">반복:</strong>
                            <select id="repeat-count" style="padding:2px 4px; border-radius:4px; border:1px solid #ccc; font-family:sans-serif; font-size:13px; cursor:pointer;">
                                <option value="1">1회</option>
                                <option value="2">2회</option>
                                <option value="3">3회</option>
                                <option value="4">4회</option>
                                <option value="5">5회</option>
                            </select>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <strong style="color:#1976d2;">음성:</strong>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="playMode" value="src" checked> 원문</label>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="playMode" value="tgt"> 번역(작문)</label>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="playMode" value="cross"> 교차</label>
                        </div>
                        <button id="range-mode-btn" onclick="toggleRangeMode()" style="background-color:#fff; border:1px solid #ccc; color:#333; padding:4px 8px; text-align:center; text-decoration:none; display:inline-block; font-size:12px; border-radius:4px; cursor:pointer; font-family:sans-serif;">
                            부분학습 범위선택
                        </button>
                        <button id="tts-play-btn" style="background-color:#4CAF50; border:none; color:white; padding:8px 20px; text-align:center; text-decoration:none; display:inline-block; font-size:14px; font-weight:bold; border-radius:6px; cursor:pointer; font-family:sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.15); transition: background-color 0.2s; white-space: nowrap; margin-left: auto;">
                            ▶ 듣기
                        </button>
                    </div>
                </div>
            </div>
            <div id="tts-text-container" style="flex: 1 1 auto; overflow-y: auto; padding: 15px 5px; line-height: 1.8; font-family:sans-serif; position: relative;">
        """
        
        for i, line in enumerate(contents):
            source_text = line.get("source_text", "")
            target_text = line.get("target_text", "")
            html_content += f"<div style='margin-bottom:12px;'>"
            html_content += f"<span id='sent-src-{i}' class='tts-sentence tts-src' onclick='handleSentenceClick({i}, \"src\")' style='cursor:pointer; padding:4px; border-radius:4px; display:inline-block; transition: background-color 0.2s;'>{source_text}</span>"
            html_content += f"<br id='br-{i}'>"
            html_content += f"<span id='sent-tgt-{i}' class='tts-sentence tts-tgt' onclick='handleSentenceClick({i}, \"tgt\")' style='cursor:pointer; margin-left:4px; padding:4px; border-radius:4px; display:inline-block; transition: background-color 0.2s;'>{target_text}</span>"
            html_content += "</div>"
            
        html_content += """
            </div>
        </div>
        <style>
            body { margin: 0; padding: 0; overflow: hidden; background-color: transparent; }
            /* 스크롤바 커스텀 (옵션) */
            #tts-text-container::-webkit-scrollbar { width: 6px; }
            #tts-text-container::-webkit-scrollbar-thumb { background-color: #ccc; border-radius: 3px; }
        </style>
        """
        
        js_content = f"""
        <script>
            const audios_src_b64 = {json.dumps(audio_b64_source_list)};
            const audios_tgt_b64 = {json.dumps(audio_b64_target_list)};
            let audioObj = new Audio();
            let currentIdx = 0;
            let currentMode = "src"; // "src" or "tgt"
            let isPlaying = false;
            
            let isRangeMode = false;
            let rangeStart = -1;
            let selectedIndices = [];
            let playQueue = [];
            let currentQueueIdx = 0;
            let currentRepeatCount = 0;
            let maxRepeatCount = 1;
            
            function updateDisplay() {{
                const mode = document.querySelector('input[name="textMode"]:checked').value;
                const showSrc = document.getElementById("show-src").checked;
                const showTgt = document.getElementById("show-tgt").checked;

                const srcSentences = document.getElementsByClassName('tts-src');
                const tgtSentences = document.getElementsByClassName('tts-tgt');

                for(let i=0; i<srcSentences.length; i++) {{
                    srcSentences[i].style.display = showSrc ? 'inline-block' : 'none';
                    tgtSentences[i].style.display = showTgt ? 'inline-block' : 'none';

                    const br = document.getElementById('br-' + i);
                    if (br) {{
                        br.style.display = (showSrc && showTgt) ? 'inline' : 'none';
                    }}

                    // Base styling
                    if (mode === 'translate') {{
                        srcSentences[i].style.fontSize = '18px';
                        srcSentences[i].style.fontWeight = 'bold';
                        srcSentences[i].dataset.baseColor = 'inherit';
                        
                        tgtSentences[i].style.fontSize = '16px';
                        tgtSentences[i].style.fontWeight = 'normal';
                        tgtSentences[i].dataset.baseColor = '#000000';
                    }} else {{
                        tgtSentences[i].style.fontSize = '18px';
                        tgtSentences[i].style.fontWeight = 'bold';
                        tgtSentences[i].dataset.baseColor = 'inherit';
                        
                        srcSentences[i].style.fontSize = '16px';
                        srcSentences[i].style.fontWeight = 'normal';
                        srcSentences[i].dataset.baseColor = '#000000';
                    }}
                }}
                updateHighlights();
            }}
            
            function toggleBlindMode() {{
                const isBlind = document.getElementById("blind-mode").checked;
                const container = document.getElementById("tts-text-container");
                if (isBlind) {{
                    container.style.filter = "blur(8px)";
                    container.style.opacity = "0.7";
                    container.style.pointerEvents = "none";
                }} else {{
                    container.style.filter = "none";
                    container.style.opacity = "1";
                    container.style.pointerEvents = "auto";
                }}
            }}
            // Load settings from localStorage
            function loadSettings() {{
                const savedMode = localStorage.getItem("eduai_textMode");
                if (savedMode) {{
                    const el = document.querySelector(`input[name="textMode"][value="${{savedMode}}"]`);
                    if(el) el.checked = true;
                }}
                const savedShowSrc = localStorage.getItem("eduai_showSrc");
                if (savedShowSrc !== null) {{
                    document.getElementById("show-src").checked = (savedShowSrc === "true");
                }}
                const savedShowTgt = localStorage.getItem("eduai_showTgt");
                if (savedShowTgt !== null) {{
                    document.getElementById("show-tgt").checked = (savedShowTgt === "true");
                }}
                const savedRepeat = localStorage.getItem("eduai_repeatCount");
                if (savedRepeat) {{
                    const selectEl = document.getElementById("repeat-count");
                    if(selectEl) selectEl.value = savedRepeat;
                }}
                const savedPlayMode = localStorage.getItem("eduai_playMode");
                if (savedPlayMode) {{
                    const el = document.querySelector(`input[name="playMode"][value="${{savedPlayMode}}"]`);
                    if(el) el.checked = true;
                }}
            }}

            function saveSettings() {{
                localStorage.setItem("eduai_textMode", document.querySelector('input[name="textMode"]:checked').value);
                localStorage.setItem("eduai_showSrc", document.getElementById("show-src").checked);
                localStorage.setItem("eduai_showTgt", document.getElementById("show-tgt").checked);
                localStorage.setItem("eduai_repeatCount", document.getElementById("repeat-count").value);
                localStorage.setItem("eduai_playMode", document.querySelector('input[name="playMode"]:checked').value);
            }}
            
            // Hook saveSettings into change events
            document.querySelectorAll('input[name="textMode"], input[name="playMode"], #show-src, #show-tgt, #repeat-count').forEach(el => {{
                el.addEventListener('change', saveSettings);
            }});

            // Initial call to set up the view
            loadSettings();
            setTimeout(updateDisplay, 100);

            function updateHighlights() {{
                const srcSentences = document.getElementsByClassName('tts-src');
                const tgtSentences = document.getElementsByClassName('tts-tgt');
                
                for(let i=0; i<srcSentences.length; i++) {{
                    let isSelected = selectedIndices.includes(i);
                    let isPlayingThis = (i === currentIdx && isPlaying && currentMode === "src");
                    
                    if (isPlayingThis) {{
                        srcSentences[i].style.backgroundColor = '#ffff99';
                        srcSentences[i].style.color = '#000';
                        scrollToElement(srcSentences[i]);
                    }} else if (isSelected) {{
                        srcSentences[i].style.backgroundColor = '#e3f2fd';
                        srcSentences[i].style.color = srcSentences[i].dataset.baseColor || 'inherit';
                    }} else {{
                        srcSentences[i].style.backgroundColor = 'transparent';
                        srcSentences[i].style.color = srcSentences[i].dataset.baseColor || 'inherit';
                    }}
                }}
                
                for(let i=0; i<tgtSentences.length; i++) {{
                    let isSelected = selectedIndices.includes(i);
                    let isPlayingThis = (i === currentIdx && isPlaying && currentMode === "tgt");
                    
                    if (isPlayingThis) {{
                        tgtSentences[i].style.backgroundColor = '#ffff99';
                        tgtSentences[i].style.color = '#000';
                        scrollToElement(tgtSentences[i]);
                    }} else if (isSelected) {{
                        tgtSentences[i].style.backgroundColor = '#e3f2fd';
                        tgtSentences[i].style.color = tgtSentences[i].dataset.baseColor || 'inherit';
                    }} else {{
                        tgtSentences[i].style.backgroundColor = 'transparent';
                        tgtSentences[i].style.color = tgtSentences[i].dataset.baseColor || 'inherit';
                    }}
                }}
                
                const playBtn = document.getElementById("tts-play-btn");
                if (playBtn) {{
                    if (isPlaying) {{
                        playBtn.innerHTML = "⏸ 정지";
                        playBtn.style.backgroundColor = "#f44336";
                    }} else {{
                        playBtn.innerHTML = "▶ 듣기";
                        playBtn.style.backgroundColor = "#4CAF50";
                    }}
                }}
            }}
            
            function scrollToElement(el) {{
                const container = document.getElementById("tts-text-container");
                const elTop = el.offsetTop;
                container.scrollTo({{
                    top: elTop - (container.clientHeight / 2) + (el.clientHeight / 2),
                    behavior: 'smooth'
                }});
            }}
            
            function toggleRangeMode() {{
                isRangeMode = !isRangeMode;
                const btn = document.getElementById("range-mode-btn");
                if (isRangeMode) {{
                    btn.innerHTML = "선택 해제";
                    btn.style.backgroundColor = "#e3f2fd";
                    btn.style.borderColor = "#2196F3";
                    btn.style.color = "#1976d2";
                }} else {{
                    btn.innerHTML = "범위 선택";
                    btn.style.backgroundColor = "#fff";
                    btn.style.borderColor = "#ccc";
                    btn.style.color = "#333";
                    
                    rangeStart = -1;
                    selectedIndices = [];
                    playQueue = [];
                    if (isPlaying) {{
                        audioObj.pause();
                        isPlaying = false;
                    }}
                    updateHighlights();
                }}
            }}

            function handleSentenceClick(idx, mode) {{
                if (isRangeMode) {{
                    if (rangeStart === -1) {{
                        rangeStart = idx;
                        selectedIndices = [idx];
                    }} else if (rangeStart === idx && selectedIndices.length === 1) {{
                        rangeStart = -1;
                        selectedIndices = [];
                    }} else {{
                        let start = Math.min(rangeStart, idx);
                        let end = Math.max(rangeStart, idx);
                        selectedIndices = [];
                        for(let i=start; i<=end; i++) {{
                            selectedIndices.push(i);
                        }}
                        rangeStart = idx;
                    }}
                    playQueue = [];
                    if (isPlaying) {{
                        audioObj.pause();
                        isPlaying = false;
                    }}
                    updateHighlights();
                }} else {{
                    currentIdx = idx;
                    currentMode = mode;
                    
                    const currentPlayMode = document.querySelector('input[name="playMode"]:checked').value;
                    if (currentPlayMode !== "cross") {{
                        document.querySelector(`input[name="playMode"][value="${{mode}}"]`).checked = true;
                    }}
                    
                    if(isPlaying) {{
                        audioObj.pause();
                    }}
                    
                    selectedIndices = [];
                    playQueue = [];
                    const playMode = document.querySelector('input[name="playMode"]:checked').value;
                    let indicesToPlay = Array.from({{length: audios_src_b64.length}}, (_, i) => i);
                    
                    for (let i of indicesToPlay) {{
                        if (playMode === "src") playQueue.push({{idx: i, mode: "src"}});
                        else if (playMode === "tgt") playQueue.push({{idx: i, mode: "tgt"}});
                        else if (playMode === "cross") {{
                            playQueue.push({{idx: i, mode: "src"}});
                            playQueue.push({{idx: i, mode: "tgt"}});
                        }}
                    }}
                    
                    let startQIdx = playQueue.findIndex(item => item.idx === idx && item.mode === mode);
                    if (startQIdx === -1) startQIdx = playQueue.findIndex(item => item.idx === idx);
                    
                    maxRepeatCount = parseInt(document.getElementById("repeat-count").value) || 1;
                    currentRepeatCount = 1;
                    currentQueueIdx = startQIdx !== -1 ? startQIdx : 0;
                    
                    isPlaying = true;
                    playCurrentInQueue();
                }}
            }}

            function buildPlayQueue() {{
                playQueue = [];
                const playMode = document.querySelector('input[name="playMode"]:checked').value;
                
                let indicesToPlay = selectedIndices.length > 0 ? selectedIndices : Array.from({{length: audios_src_b64.length}}, (_, i) => i);
                
                for (let idx of indicesToPlay) {{
                    if (playMode === "src") {{
                        playQueue.push({{idx: idx, mode: "src"}});
                    }} else if (playMode === "tgt") {{
                        playQueue.push({{idx: idx, mode: "tgt"}});
                    }} else if (playMode === "cross") {{
                        playQueue.push({{idx: idx, mode: "src"}});
                        playQueue.push({{idx: idx, mode: "tgt"}});
                    }}
                }}
            }}

            function playCurrentInQueue() {{
                if (currentQueueIdx >= playQueue.length) {{
                    if (currentRepeatCount < maxRepeatCount) {{
                        currentRepeatCount++;
                        currentQueueIdx = 0;
                    }} else {{
                        isPlaying = false;
                        updateHighlights();
                        return;
                    }}
                }}
                
                const item = playQueue[currentQueueIdx];
                currentIdx = item.idx;
                currentMode = item.mode;
                
                const audios_b64 = currentMode === "src" ? audios_src_b64 : audios_tgt_b64;
                
                if(!audios_b64[currentIdx] || audios_b64[currentIdx] === "") {{
                    currentQueueIdx++;
                    if(isPlaying) playCurrentInQueue();
                    return;
                }}
                
                audioObj.src = "data:audio/mp3;base64," + audios_b64[currentIdx];
                audioObj.play().catch(e => {{
                    console.error("Audio play error:", e);
                    currentQueueIdx++;
                    if(isPlaying) playCurrentInQueue();
                }});
                isPlaying = true;
                updateHighlights();
            }}

            audioObj.onended = function() {{
                currentQueueIdx++;
                if(isPlaying) {{
                    playCurrentInQueue();
                }}
            }};
            
            // Rebuild queue if play settings change
            document.querySelectorAll('input[name="playMode"], #repeat-count').forEach(el => {{
                el.addEventListener('change', () => {{
                    playQueue = [];
                    if (isPlaying) {{
                        audioObj.pause();
                        isPlaying = false;
                        updateHighlights();
                    }}
                }});
            }});
            
            const playBtn = document.getElementById("tts-play-btn");
            if (playBtn) {{
                playBtn.onclick = function() {{
                    if(isPlaying) {{
                        audioObj.pause();
                        isPlaying = false;
                        updateHighlights();
                    }} else {{
                        // Resume or start
                        if (playQueue.length === 0) {{
                            maxRepeatCount = parseInt(document.getElementById("repeat-count").value) || 1;
                            currentRepeatCount = 1;
                            buildPlayQueue();
                            currentQueueIdx = 0;
                        }}
                        // If it finished previously, replay from start of queue
                        if (currentQueueIdx >= playQueue.length) {{
                            currentRepeatCount = 1;
                            currentQueueIdx = 0;
                        }}
                        
                        if (playQueue.length > 0) {{
                            isPlaying = true;
                            playCurrentInQueue();
                        }}
                    }}
                }};
            }}
        </script>
        """
        
        # iframe 높이를 동적으로 제한 (최대 650px)하여 내부 스크롤 활성화 (헤더가 커졌으므로 150 추가)
        iframe_height = min(650, max(350, len(contents) * 70 + 150))
        components.html(html_content + js_content, height=iframe_height, scrolling=False)
        
    else:
        st.info("본문 데이터가 없습니다.")

    st.markdown("---")

    # 3.5. 🗣️ 대화문 롤플레잉 또는 문장별 발음 연습
    is_dialogue = data.get("type") == "dialogue"
    
    if contents:
        from app.agents import pronunciation_agent
        from app.core.tts_engine import generate_audio_sync, get_voice_for_language
        from app.db.database import add_pronunciation_score
        source_lang = data.get("source_language", "en")
        
        if is_dialogue:
            st.subheader("🗣️ 대화문 롤플레잉 (Role-play)")
            st.write("나의 역할을 선택하고 원어민 AI 튜터와 대화하듯 실전 연습을 해보세요!")
            
            # 화자 추출 (speaker_name이 없으면 source_text에서 유추)
            speakers = set()
            for c in contents:
                name = c.get("speaker_name")
                if not name and ":" in c.get("source_text", ""):
                    name = c.get("source_text").split(":")[0].strip()
                if name:
                    speakers.add(name)
            
            speakers = list(speakers)
            if not speakers:
                speakers = ["A", "B"] # fallback
                
            selected_role = st.selectbox("🙋 나의 역할 선택", speakers)
            mode = st.radio("진행 방식 선택", ["A안: 단계별 실전 롤플레잉 (권장)", "B안: 전체 대본 자유 연습"], horizontal=True)
            
            if "B안" in mode:
                st.info("내 역할의 대사에 있는 마이크 버튼을 눌러 자유롭게 발음을 점검하세요.")
                for i, line in enumerate(contents):
                    name = line.get("speaker_name")
                    if not name and ":" in line.get("source_text", ""):
                        name = line.get("source_text").split(":")[0].strip()
                    
                    target_text = line.get("source_text", "")
                    st.markdown(f"**{name or 'Unknown'}**: {target_text}")
                    
                    if name == selected_role:
                        if hasattr(st, "audio_input"):
                            audio_val = st.audio_input(f"발음 연습 ({i+1})", key=f"rp_free_audio_{i}")
                            if audio_val:
                                with st.spinner("AI가 발음을 분석 중입니다..."):
                                    audio_bytes = audio_val.getvalue()
                                    ahash = hash(audio_bytes)
                                    skey = f"rp_free_res_{i}"
                                    if st.session_state.get(f"ahash_{skey}") != ahash:
                                        res = pronunciation_agent.evaluate_pronunciation(audio_bytes, target_text, source_lang)
                                        st.session_state[f"ahash_{skey}"] = ahash
                                        st.session_state[skey] = res
                                        add_pronunciation_score(st.session_state["user_id"], target_text, res.get('score', 0))
                                    else:
                                        res = st.session_state[skey]
                                        
                                    col_s1, col_s2 = st.columns([1, 3])
                                    with col_s1:
                                        st.metric("발음 정확도", f"{res.get('score', 0)}점")
                                    with col_s2:
                                        st.markdown(f"**인식된 문장:** {res.get('transcription', '')}")
                                        st.success(f"**AI 튜터 피드백:** {res.get('feedback', '')}")
                    st.write("")
            else:
                # A안 (단계별 실전 롤플레잉)
                if "rp_current_idx" not in st.session_state:
                    st.session_state.rp_current_idx = 0
                    
                col_ctrl1, col_ctrl2 = st.columns([3, 1])
                with col_ctrl1:
                    st.progress(st.session_state.rp_current_idx / max(1, len(contents)))
                with col_ctrl2:
                    if st.button("🔄 처음부터 다시"):
                        st.session_state.rp_current_idx = 0
                        st.rerun()
                        
                if st.session_state.rp_current_idx < len(contents):
                    curr_idx = st.session_state.rp_current_idx
                    line = contents[curr_idx]
                    
                    name = line.get("speaker_name")
                    if not name and ":" in line.get("source_text", ""):
                        name = line.get("source_text").split(":")[0].strip()
                        
                    target_text = line.get("source_text", "")
                    
                    st.markdown(f"### 💬 [{name or 'Unknown'}] 의 차례입니다.")
                    st.info(f"**대사:** {target_text}")
                    
                    if name == selected_role:
                        st.write("🎙️ 마이크를 켜고 위 대사를 읽어주세요.")
                        if hasattr(st, "audio_input"):
                            audio_val = st.audio_input("내 차례 녹음", key=f"rp_step_audio_{curr_idx}")
                            if audio_val:
                                with st.spinner("AI가 발음을 분석 중입니다..."):
                                    audio_bytes = audio_val.getvalue()
                                    ahash = hash(audio_bytes)
                                    skey = f"rp_step_res_{curr_idx}"
                                    if st.session_state.get(f"ahash_{skey}") != ahash:
                                        res = pronunciation_agent.evaluate_pronunciation(audio_bytes, target_text, source_lang)
                                        st.session_state[f"ahash_{skey}"] = ahash
                                        st.session_state[skey] = res
                                        add_pronunciation_score(st.session_state["user_id"], target_text, res.get('score', 0))
                                    else:
                                        res = st.session_state[skey]
                                        
                                    col_s1, col_s2 = st.columns([1, 3])
                                    with col_s1:
                                        st.metric("발음 정확도", f"{res.get('score', 0)}점")
                                    with col_s2:
                                        st.markdown(f"**인식된 문장:** {res.get('transcription', '')}")
                                        st.success(f"**AI 튜터 피드백:** {res.get('feedback', '')}")
                                        
                                if res.get('score', 0) >= 60:
                                    if st.button("👉 훌륭합니다! 다음 차례로 넘어가기", key=f"next_ok_{curr_idx}"):
                                        st.session_state.rp_current_idx += 1
                                        st.rerun()
                                else:
                                    st.warning("점수가 60점 미만입니다. 피드백을 참고하여 한 번 더 정확하게 발음해 보세요!")
                                    if st.button("👉 무시하고 다음으로 넘어가기", key=f"next_force_{curr_idx}"):
                                        st.session_state.rp_current_idx += 1
                                        st.rerun()
                    else:
                        st.write("🎧 상대방(AI)의 대사를 듣고 다음으로 넘어가세요.")
                        voice = get_voice_for_language(source_lang, line.get("speaker_gender", "male"))
                        with st.spinner("상대방의 목소리를 생성 중입니다..."):
                            audio_bytes = generate_audio_sync(target_text, voice)
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        
                        if st.button("👉 다음 내 차례로 넘어가기", key=f"next_{curr_idx}"):
                            st.session_state.rp_current_idx += 1
                            st.rerun()
                else:
                    st.balloons()
                    st.success("🎉 롤플레잉 대화를 성공적으로 마쳤습니다!")
                    if st.button("🔄 다시 하기"):
                        st.session_state.rp_current_idx = 0
                        st.rerun()

    st.markdown("---")

    # 3.6. 🎙️ 스피킹 & 섀도잉 집중 연습 (일반 지문/대화문 공통)
    if contents:
        st.subheader("🎙️ 스피킹 & 섀도잉 집중 연습")
        st.write("원어민 발음을 3단계 섀도잉으로 듣고 연습하거나, 바로 마이크로 읽어 발음을 평가받으세요.")
        
        practice_options = [f"문장 {i+1}: {line.get('source_text', '')}" for i, line in enumerate(contents)]
        selected_prac_str = st.selectbox("연습할 문장을 선택하세요", practice_options, key="practice_select")
        
        if selected_prac_str:
            selected_idx = practice_options.index(selected_prac_str)
            target_text = contents[selected_idx].get('source_text', '')
            source_lang = data.get("source_language", "en")
            current_gender = st.session_state.get("tts_gender", "male")
            voice = get_voice_for_language(source_lang, gender=current_gender)
            
            st.info(f"**목표 문장:** {target_text}")
            
            # 오디오 생성
            skey_normal = f"shadow_normal_{selected_idx}_{current_gender}"
            skey_slow = f"shadow_slow_{selected_idx}_{current_gender}"
            
            if skey_normal not in st.session_state:
                with st.spinner("가이드 오디오를 생성 중입니다..."):
                    st.session_state[skey_normal] = generate_audio_sync(target_text, voice, rate="+0%")
                    st.session_state[skey_slow] = generate_audio_sync(target_text, voice, rate="-30%")
            
            # HTML/JS 3-step player
            normal_b64 = base64.b64encode(st.session_state[skey_normal]).decode('utf-8')
            slow_b64 = base64.b64encode(st.session_state[skey_slow]).decode('utf-8')
            
            player_html = f"""
            <div style="text-align:center; margin:10px 0;">
                <button id="shadow-play-btn" style="background-color:#4CAF50; border:none; color:white; padding:10px 24px; font-size:16px; border-radius:8px; cursor:pointer; font-weight:bold;">
                    ▶ 3단계 섀도잉 가이드 듣기
                </button>
                <div id="shadow-status" style="margin-top:10px; font-size:14px; color:#555;">대기 중...</div>
            </div>
            <script>
                (function() {{
                    const normalAudio = "data:audio/mp3;base64,{normal_b64}";
                    const slowAudio = "data:audio/mp3;base64,{slow_b64}";
                    
                    const btn = document.getElementById("shadow-play-btn");
                    const status = document.getElementById("shadow-status");
                    
                    let audioPlayer = new Audio();
                    let step = 0;
                    
                    btn.onclick = function() {{
                        if (step !== 0 && step !== 4) return; // Ignore if playing
                        step = 1;
                        btn.disabled = true;
                        btn.style.backgroundColor = "#aaa";
                        playStep();
                    }};
                    
                    function playStep() {{
                        if (step === 1) {{
                            status.innerText = "1단계: 정상 속도 듣기";
                            audioPlayer.src = normalAudio;
                            audioPlayer.play();
                            audioPlayer.onended = function() {{
                                step = 2;
                                status.innerText = "잠시 대기...";
                                setTimeout(playStep, 1000);
                            }};
                        }} else if (step === 2) {{
                            status.innerText = "2단계: 느린 속도로 띄어 읽기";
                            audioPlayer.src = slowAudio;
                            audioPlayer.play();
                            audioPlayer.onended = function() {{
                                step = 3;
                                status.innerText = "잠시 대기...";
                                setTimeout(playStep, 1000);
                            }};
                        }} else if (step === 3) {{
                            status.innerText = "3단계: 마지막 정상 속도 섀도잉";
                            audioPlayer.src = normalAudio;
                            audioPlayer.play();
                            audioPlayer.onended = function() {{
                                step = 4;
                                status.innerText = "완료! 아래 마이크로 연습해 보세요.";
                                btn.disabled = false;
                                btn.style.backgroundColor = "#4CAF50";
                            }};
                        }}
                    }}
                }})();
            </script>
            """
            components.html(player_html, height=120)
            
            if hasattr(st, "audio_input"):
                shadow_audio_val = st.audio_input("마이크를 켜고 큰 소리로 따라 읽어보세요", key=f"shadow_input_{selected_idx}")
                if shadow_audio_val:
                    with st.spinner("AI가 발음을 분석 중입니다..."):
                        audio_bytes = shadow_audio_val.getvalue()
                        ahash = hash(audio_bytes)
                        skey_res = f"shadow_res_{selected_idx}"
                        if st.session_state.get(f"ahash_{skey_res}") != ahash:
                            res = pronunciation_agent.evaluate_pronunciation(audio_bytes, target_text, source_lang)
                            st.session_state[f"ahash_{skey_res}"] = ahash
                            st.session_state[skey_res] = res
                            add_pronunciation_score(st.session_state["user_id"], target_text, res.get('score', 0))
                        else:
                            res = st.session_state[skey_res]
                            
                        col_sh1, col_sh2 = st.columns([1, 3])
                        with col_sh1:
                            st.metric("발음 정확도", f"{res.get('score', 0)}점")
                        with col_sh2:
                            st.markdown(f"**인식된 문장:** {res.get('transcription', '')}")
                            st.success(f"**AI 선생님 피드백:** {res.get('feedback', '')}")
            else:
                st.warning("현재 브라우저 환경에서는 마이크 입력을 지원하지 않습니다.")

    st.markdown("---")

    # 4. 단어장
    st.subheader("📚 핵심 어휘")
    vocab = data.get("vocabulary", [])
    if vocab:
        from app.db.database import add_word
        for i, v in enumerate(vocab):
            word = v.get('word', '')
            meaning = v.get('meaning', '')
            col_v1, col_v2 = st.columns([4, 1])
            with col_v1:
                st.markdown(f"- **{word}**: {meaning}")
            with col_v2:
                if st.button("➕ 단어장에 저장", key=f"save_vocab_{i}_{word}"):
                    success = add_word(st.session_state["user_id"], word, meaning)
                    if success:
                        st.toast(f"'{word}' 단어장에 저장 완료! 🎉")
                    else:
                        st.toast(f"'{word}' 이미 단어장에 있습니다.", icon="⚠️")
    else:
        st.info("단어장 데이터가 없습니다.")
            
    st.markdown("---")

    # 5. 기존 교재 문제 (original_questions)
    original_questions = data.get("original_questions", [])
    if original_questions:
        st.subheader("원본 교재 문제")
        for i, q in enumerate(original_questions):
            st.markdown(f"**Q{i+1}. {q.get('question_text', '')}**")
            options = q.get("options", [])
            if options:
                for j, opt in enumerate(options):
                    st.markdown(f"({j+1}) {opt}")
            st.write("") # 간격
    
    st.markdown("---")
    st.subheader("💬 AI 튜터와 대화하기 (Q&A & 인터뷰)")
    
    # 대화 모드 선택
    chat_mode_label = st.radio("선생님 역할 선택", ["일반 Q&A 모드 (학생이 질문하기)", "AI 주도 인터뷰 모드 (선생님이 질문하기)"], horizontal=True)
    mode_key = "qa" if "일반" in chat_mode_label else "interview"
    
    # 모드가 변경되었으면 채팅 기록 리셋
    if st.session_state.get("current_chat_mode") != mode_key:
        st.session_state.current_chat_mode = mode_key
        if mode_key == "qa":
            st.session_state.chat_history = [{"role": "assistant", "content": "학습하시다가 모르는 문법이나 단어가 있다면 언제든 편하게 물어보세요!"}]
        else:
            st.session_state.chat_history = [{"role": "assistant", "content": "지금부터 본문 내용에 대한 인터뷰를 시작하겠습니다. 지문 내용을 잘 이해했는지 확인하기 위해 제가 날카로운 질문을 드릴 테니, 마음의 준비가 되셨다면 '시작'이라고 대답해 주세요!"}]
    
    # 입출력 모드 선택 토글
    col_chat1, col_chat2 = st.columns([1, 1])
    with col_chat1:
        st.caption("마이크를 사용할 수 없을 때는 하단의 입력창을 이용하세요.")
    with col_chat2:
        voice_reply_mode = st.toggle("🔊 AI 선생님 답변을 음성으로 듣기", value=False)

    # 기존 채팅 내역 출력
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "audio_b64" in msg and msg["audio_b64"]:
                st.audio(base64.b64decode(msg["audio_b64"]), format="audio/mp3")
                
    # 입력 인터페이스
    user_query = st.chat_input("질문을 텍스트로 입력해주세요...")
    audio_value = None
    if hasattr(st, "audio_input"):
        audio_value = st.audio_input("🎤 마이크로 질문하기", key="chat_audio_input")
        
    processed_query = None
    
    # 오디오 중복 처리 방지 (Streamlit 특성)
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
                st.error("음성을 제대로 인식하지 못했습니다. 다시 시도해주세요.")
    elif user_query:
        processed_query = user_query
            
    # 질문이 접수된 경우 (텍스트 또는 음성)
    if processed_query:
        # 1) 사용자 메시지 기록 및 출력
        st.session_state.chat_history.append({"role": "user", "content": processed_query})
        with st.chat_message("user"):
            st.markdown(processed_query)
            
        # 2) AI 튜터 답변 생성 및 출력
        with st.chat_message("assistant"):
            with st.spinner("AI 선생님이 답변을 작성 중입니다..."):
                from app.agents import tutor_agent
                student_level = st.session_state.get("student_level", "중학교 1학년")
                ai_response = tutor_agent.get_tutor_chat_response(st.session_state.chat_history, data, mode=st.session_state.current_chat_mode, student_level=student_level)
                st.markdown(ai_response)
                
                audio_b64 = None
                # 음성 답변 모드가 켜져 있을 경우 TTS 변환
                if voice_reply_mode:
                    with st.spinner("답변을 음성으로 변환 중입니다..."):
                        from app.core.tts_engine import generate_audio_sync, get_voice_for_language
                        # 튜터는 한국어로 답변하므로 한국어 여성/남성 목소리 사용
                        tutor_voice = get_voice_for_language("ko", gender="female")
                        try:
                            audio_bytes = generate_audio_sync(ai_response, tutor_voice)
                            st.audio(audio_bytes, format="audio/mp3")
                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        except Exception as e:
                            st.error(f"음성 변환 실패: {e}")
                
        # 3) AI 답변 기록
        msg_record = {"role": "assistant", "content": ai_response}
        if audio_b64:
            msg_record["audio_b64"] = audio_b64
        st.session_state.chat_history.append(msg_record)
        st.rerun()
