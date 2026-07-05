import streamlit as st
from typing import Dict, Any

def render_parsed_result(data: Dict[str, Any]):
    """?Œì‹±??JSON ?°ì´?°ë? Streamlit UI ì»´í¬?ŒíŠ¸ë¡?ë³€?˜í•˜???”ë©´??ê·¸ë¦½?ˆë‹¤."""
    
    if "error" in data:
        st.error(f"?°ì´???Œì‹± ì¤??¤ë¥˜ê°€ ë°œìƒ?ˆìŠµ?ˆë‹¤: {data['error']}")
        return

    # 1. ?¤ë” (?œëª©)
    title = data.get("title", "EduAI ?™ìŠµ ?ë£Œ")
    st.header(f"?“– {title}")
    st.markdown("---")

    # 2. ê³¼ì™¸ ? ìƒ???¼ë“œë°?(?„ê¸° ë¶„ì„ ë°??¬ë¡­ ?´ì„¤)
    tutor_feedback = data.get("tutor_feedback", "")
    if tutor_feedback:
        st.success(f"?‘¨?ğŸ?**AI ? ìƒ?˜ì˜ ë°€ì°??¼ë“œë°?*\n\n{tutor_feedback}")
        st.markdown("---")

    import base64
    import json
    import streamlit.components.v1 as components
    from app.core.tts_engine import generate_audio_sync, get_voice_for_language

    # 3. ë³¸ë¬¸ (Reading/Dialogue)
    contents = data.get("contents", [])
    if contents:
        # ?¤ë””??ìºì‹± (?¤íŠ¸ë¦¼ë¦¿ ë¦¬ë Œ?”ë§ ???¬ìƒ??ë°©ì? ë°??±ë³„ ë³€ê²???ìºì‹œ ë¬´íš¨??
        current_gender = st.session_state.get("tts_gender", "male")
        if "audio_b64_source_list" not in data or data.get("audio_voice_gender") != current_gender:
            source_lang = data.get("source_language", "en")
            target_lang = data.get("target_language", "ko")
            source_voice = get_voice_for_language(source_lang, gender=current_gender)
            target_voice = get_voice_for_language(target_lang, gender=current_gender)
            audio_b64_source_list = []
            audio_b64_target_list = []
            
            with st.spinner("ë³¸ë¬¸ ?¤ë””?¤ë? ?ì„± ì¤‘ì…?ˆë‹¤... (ìµœì´ˆ 1???ëŠ” ?¤ì • ë³€ê²???"):
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

        edit_mode = st.toggle("?ï¸ ë³¸ë¬¸ ë¬¸ì¥ ?˜ì • ëª¨ë“œ")
        
        if edit_mode:
            st.info("ë¬¸ì¥???˜ì •?˜ê³  ?”í„°ë¥?ì¹˜ë©´, ?´ë‹¹ ë¬¸ì¥??ë°œìŒ ?¤ë””?¤ê? ì¦‰ì‹œ ?¬ìƒ?±ë©?ˆë‹¤.")
            for i, line in enumerate(contents):
                st.markdown(f"**[{i+1}ë²?ë¬¸ì¥]**")
                
                # ?ë¬¸ ?˜ì •
                old_src = line.get("source_text", "")
                new_src = st.text_input("?ë¬¸", value=old_src, key=f"edit_src_{i}")
                if new_src != old_src:
                    data["contents"][i]["source_text"] = new_src
                    source_lang = data.get("source_language", "en")
                    voice = get_voice_for_language(source_lang, gender=current_gender)
                    with st.spinner("?ë¬¸ ?¤ë””???¬ìƒ??ì¤?.."):
                        if new_src.strip():
                            try:
                                audio_bytes = generate_audio_sync(new_src, voice)
                                data["audio_b64_source_list"][i] = base64.b64encode(audio_bytes).decode('utf-8')
                            except:
                                data["audio_b64_source_list"][i] = ""
                        else:
                            data["audio_b64_source_list"][i] = ""
                    st.rerun()

                # ë²ˆì—­ë¬??˜ì •
                old_tgt = line.get("target_text", "")
                new_tgt = st.text_input("ë²ˆì—­ë¬?, value=old_tgt, key=f"edit_tgt_{i}")
                if new_tgt != old_tgt:
                    data["contents"][i]["target_text"] = new_tgt
                    target_lang = data.get("target_language", "ko")
                    voice = get_voice_for_language(target_lang, gender=current_gender)
                    with st.spinner("ë²ˆì—­ë¬??¤ë””???¬ìƒ??ì¤?.."):
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
            return # ?˜ì • ëª¨ë“œ???ŒëŠ” ?„ë˜ HTML ?Œë ˆ?´ì–´ë¥?ê·¸ë¦¬ì§€ ?ŠìŒ

        html_content = f"""
        <div style="display: flex; flex-direction: column; height: 100vh; margin: 0; padding: 0;">
            <div id="sticky-header" style="flex: 0 0 auto; background: white; z-index: 100; padding: 10px; border-bottom: 1px solid #e6e6e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; gap: 10px;">
                <!-- Title Row -->
                <div>
                    <h3 style="margin: 0; font-family: sans-serif; color: #31333F; font-size: 1.5rem; font-weight: 600;">?“ ë³¸ë¬¸ ì§€ë¬?/h3>
                </div>
                
                <!-- Controls Row -->
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <!-- Box 1: View Options -->
                    <div style="background: #fcfcfc; border: 1px solid #ddd; border-radius: 8px; padding: 8px 12px; font-family: sans-serif; font-size: 13px; color: #333; display: flex; flex-direction: column; justify-content: center; gap: 8px; min-width: 160px;">
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <strong style="width: 35px; color:#555;">ëª¨ë“œ:</strong>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="textMode" value="translate" checked onchange="updateDisplay()"> ë²ˆì—­</label>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="textMode" value="compose" onchange="updateDisplay()"> ?‘ë¬¸</label>
                        </div>
                        <div style="display: flex; gap: 12px; align-items: center;">
                            <strong style="width: 35px; color:#555;">?œì‹œ:</strong>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="checkbox" id="show-src" checked onchange="updateDisplay()"> ?ë¬¸ ë³´ê¸°</label>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="checkbox" id="show-tgt" checked onchange="updateDisplay()"> ë²ˆì—­(?‘ë¬¸) ë³´ê¸°</label>
                        </div>
                        <div style="display: flex; gap: 12px; align-items: center; margin-top: 5px;">
                            <strong style="width: 35px; color:#555;">?ˆë ¨:</strong>
                            <label style="cursor:pointer; white-space: nowrap; color: #d32f2f; font-weight: bold;"><input type="checkbox" id="blind-mode" onchange="toggleBlindMode()"> ?§ ë¸”ë¼?¸ë“œ ëª¨ë“œ (?£ê¸° ?‰ê?)</label>
                        </div>
                    </div>
                    
                    <!-- Box 2: Audio Options -->
                    <div style="background: #eef7ff; border: 1px solid #bce0fd; border-radius: 8px; padding: 8px 12px; font-family: sans-serif; font-size: 13px; color: #333; display: flex; align-items: center; gap: 15px; flex-wrap: wrap; flex: 1; min-width: 280px;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <strong style="color:#1976d2;">ë°˜ë³µ:</strong>
                            <select id="repeat-count" style="padding:2px 4px; border-radius:4px; border:1px solid #ccc; font-family:sans-serif; font-size:13px; cursor:pointer;">
                                <option value="1">1??/option>
                                <option value="2">2??/option>
                                <option value="3">3??/option>
                                <option value="4">4??/option>
                                <option value="5">5??/option>
                            </select>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <strong style="color:#1976d2;">?Œì„±:</strong>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="playMode" value="src" checked> ?ë¬¸</label>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="playMode" value="tgt"> ë²ˆì—­(?‘ë¬¸)</label>
                            <label style="cursor:pointer; white-space: nowrap;"><input type="radio" name="playMode" value="cross"> êµì°¨</label>
                        </div>
                        <button id="range-mode-btn" onclick="toggleRangeMode()" style="background-color:#fff; border:1px solid #ccc; color:#333; padding:4px 8px; text-align:center; text-decoration:none; display:inline-block; font-size:12px; border-radius:4px; cursor:pointer; font-family:sans-serif;">
                            ë²”ìœ„ ? íƒ
                        </button>
                        <button id="tts-play-btn" style="background-color:#4CAF50; border:none; color:white; padding:8px 20px; text-align:center; text-decoration:none; display:inline-block; font-size:14px; font-weight:bold; border-radius:6px; cursor:pointer; font-family:sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.15); transition: background-color 0.2s; white-space: nowrap; margin-left: auto;">
                            ???£ê¸°
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
            /* ?¤í¬ë¡¤ë°” ì»¤ìŠ¤?€ (?µì…˜) */
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
                        playBtn.innerHTML = "???•ì?";
                        playBtn.style.backgroundColor = "#f44336";
                    }} else {{
                        playBtn.innerHTML = "???£ê¸°";
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
                    btn.innerHTML = "? íƒ ?´ì œ";
                    btn.style.backgroundColor = "#e3f2fd";
                    btn.style.borderColor = "#2196F3";
                    btn.style.color = "#1976d2";
                }} else {{
                    btn.innerHTML = "ë²”ìœ„ ? íƒ";
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
        
        # iframe ?’ì´ë¥??™ì ?¼ë¡œ ?œí•œ (ìµœë? 650px)?˜ì—¬ ?´ë? ?¤í¬ë¡??œì„±??(?¤ë”ê°€ ì»¤ì¡Œ?¼ë?ë¡?150 ì¶”ê?)
        iframe_height = min(650, max(350, len(contents) * 70 + 150))
        components.html(html_content + js_content, height=iframe_height, scrolling=False)
        
    else:
        st.info("ë³¸ë¬¸ ?°ì´?°ê? ?†ìŠµ?ˆë‹¤.")

    st.markdown("---")

    # 3.5. ?—£ï¸??€?”ë¬¸ ë¡¤í”Œ?ˆì‰ ?ëŠ” ë¬¸ì¥ë³?ë°œìŒ ?°ìŠµ
    is_dialogue = data.get("type") == "dialogue"
    
    if contents:
        from app.agents import pronunciation_agent
        from app.core.tts_engine import generate_audio_sync, get_voice_for_language
        from app.db.database import add_pronunciation_score
        source_lang = data.get("source_language", "en")
        
        if is_dialogue:
            st.subheader("?—£ï¸??€?”ë¬¸ ë¡¤í”Œ?ˆì‰ (Role-play)")
            st.write("?˜ì˜ ??• ??? íƒ?˜ê³  ?ì–´ë¯?AI ?œí„°?€ ?€?”í•˜???¤ì „ ?°ìŠµ???´ë³´?¸ìš”!")
            
            # ?”ì ì¶”ì¶œ (speaker_name???†ìœ¼ë©?source_text?ì„œ ? ì¶”)
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
                
            selected_role = st.selectbox("?™‹ ?˜ì˜ ??•  ? íƒ", speakers)
            mode = st.radio("ì§„í–‰ ë°©ì‹ ? íƒ", ["A?? ?¨ê³„ë³??¤ì „ ë¡¤í”Œ?ˆì‰ (ê¶Œì¥)", "B?? ?„ì²´ ?€ë³??ìœ  ?°ìŠµ"], horizontal=True)
            
            if "B?? in mode:
                st.info("????• ???€?¬ì— ?ˆëŠ” ë§ˆì´??ë²„íŠ¼???ŒëŸ¬ ?ìœ ë¡?²Œ ë°œìŒ???ê??˜ì„¸??")
                for i, line in enumerate(contents):
                    name = line.get("speaker_name")
                    if not name and ":" in line.get("source_text", ""):
                        name = line.get("source_text").split(":")[0].strip()
                    
                    target_text = line.get("source_text", "")
                    st.markdown(f"**{name or 'Unknown'}**: {target_text}")
                    
                    if name == selected_role:
                        if hasattr(st, "audio_input"):
                            audio_val = st.audio_input(f"ë°œìŒ ?°ìŠµ ({i+1})", key=f"rp_free_audio_{i}")
                            if audio_val:
                                with st.spinner("AIê°€ ë°œìŒ??ë¶„ì„ ì¤‘ì…?ˆë‹¤..."):
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
                                        st.metric("ë°œìŒ ?•í™•??, f"{res.get('score', 0)}??)
                                    with col_s2:
                                        st.markdown(f"**?¸ì‹??ë¬¸ì¥:** {res.get('transcription', '')}")
                                        st.success(f"**AI ?œí„° ?¼ë“œë°?** {res.get('feedback', '')}")
                    st.write("")
            else:
                # A??(?¨ê³„ë³??¤ì „ ë¡¤í”Œ?ˆì‰)
                if "rp_current_idx" not in st.session_state:
                    st.session_state.rp_current_idx = 0
                    
                col_ctrl1, col_ctrl2 = st.columns([3, 1])
                with col_ctrl1:
                    st.progress(st.session_state.rp_current_idx / max(1, len(contents)))
                with col_ctrl2:
                    if st.button("?”„ ì²˜ìŒë¶€???¤ì‹œ"):
                        st.session_state.rp_current_idx = 0
                        st.rerun()
                        
                if st.session_state.rp_current_idx < len(contents):
                    curr_idx = st.session_state.rp_current_idx
                    line = contents[curr_idx]
                    
                    name = line.get("speaker_name")
                    if not name and ":" in line.get("source_text", ""):
                        name = line.get("source_text").split(":")[0].strip()
                        
                    target_text = line.get("source_text", "")
                    
                    st.markdown(f"### ?’¬ [{name or 'Unknown'}] ??ì°¨ë??…ë‹ˆ??")
                    st.info(f"**?€??** {target_text}")
                    
                    if name == selected_role:
                        st.write("?™ï¸?ë§ˆì´?¬ë? ì¼œê³  ???€?¬ë? ?½ì–´ì£¼ì„¸??")
                        if hasattr(st, "audio_input"):
                            audio_val = st.audio_input("??ì°¨ë? ?¹ìŒ", key=f"rp_step_audio_{curr_idx}")
                            if audio_val:
                                with st.spinner("AIê°€ ë°œìŒ??ë¶„ì„ ì¤‘ì…?ˆë‹¤..."):
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
                                        st.metric("ë°œìŒ ?•í™•??, f"{res.get('score', 0)}??)
                                    with col_s2:
                                        st.markdown(f"**?¸ì‹??ë¬¸ì¥:** {res.get('transcription', '')}")
                                        st.success(f"**AI ?œí„° ?¼ë“œë°?** {res.get('feedback', '')}")
                                        
                                if res.get('score', 0) >= 60:
                                    if st.button("?‘‰ ?Œë??©ë‹ˆ?? ?¤ìŒ ì°¨ë?ë¡??˜ì–´ê°€ê¸?, key=f"next_ok_{curr_idx}"):
                                        st.session_state.rp_current_idx += 1
                                        st.rerun()
                                else:
                                    st.warning("?ìˆ˜ê°€ 60??ë¯¸ë§Œ?…ë‹ˆ?? ?¼ë“œë°±ì„ ì°¸ê³ ?˜ì—¬ ??ë²????•í™•?˜ê²Œ ë°œìŒ??ë³´ì„¸??")
                                    if st.button("?‘‰ ë¬´ì‹œ?˜ê³  ?¤ìŒ?¼ë¡œ ?˜ì–´ê°€ê¸?, key=f"next_force_{curr_idx}"):
                                        st.session_state.rp_current_idx += 1
                                        st.rerun()
                    else:
                        st.write("?§ ?ë?ë°?AI)???€?¬ë? ?£ê³  ?¤ìŒ?¼ë¡œ ?˜ì–´ê°€?¸ìš”.")
                        voice = get_voice_for_language(source_lang, line.get("speaker_gender", "male"))
                        with st.spinner("?ë?ë°©ì˜ ëª©ì†Œë¦¬ë? ?ì„± ì¤‘ì…?ˆë‹¤..."):
                            audio_bytes = generate_audio_sync(target_text, voice)
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                        
                        if st.button("?‘‰ ?¤ìŒ ??ì°¨ë?ë¡??˜ì–´ê°€ê¸?, key=f"next_{curr_idx}"):
                            st.session_state.rp_current_idx += 1
                            st.rerun()
                else:
                    st.balloons()
                    st.success("?‰ ë¡¤í”Œ?ˆì‰ ?€?”ë? ?±ê³µ?ìœ¼ë¡?ë§ˆì³¤?µë‹ˆ??")
                    if st.button("?”„ ?¤ì‹œ ?˜ê¸°"):
                        st.session_state.rp_current_idx = 0
                        st.rerun()

        else:
            st.subheader("?™ï¸?ë¬¸ì¥ë³?ë°œìŒ ?°ìŠµ")
            st.write("?ì–´ë¯?ë°œìŒ???£ê³  ë§ˆì´?¬ë¡œ ì§ì ‘ ?°ë¼ ?½ì–´ë³´ì„¸?? AI ? ìƒ?˜ì´ ë°œìŒ???‰ê???ì¤ë‹ˆ??")
            
            sentence_options = [f"ë¬¸ì¥ {i+1}: {line.get('source_text', '')}" for i, line in enumerate(contents)]
            selected_sent_str = st.selectbox("?°ìŠµ??ë¬¸ì¥??? íƒ?˜ì„¸??, sentence_options)
            
            if selected_sent_str:
                selected_idx = sentence_options.index(selected_sent_str)
                target_text = contents[selected_idx].get('source_text', '')
                
                st.info(f"**ëª©í‘œ ë¬¸ì¥:** {target_text}")
                
                if hasattr(st, "audio_input"):
                    audio_val = st.audio_input("ë§ˆì´?¬ë? ì¼œê³  ???Œë¦¬ë¡??°ë¼ ?½ì–´ë³´ì„¸??, key=f"stt_input_{selected_idx}")
                    
                    if audio_val:
                        with st.spinner("AIê°€ ë°œìŒ??ë¶„ì„ ì¤‘ì…?ˆë‹¤..."):
                            audio_bytes = audio_val.getvalue()
                            ahash = hash(audio_bytes)
                            skey = f"read_res_{selected_idx}"
                            if st.session_state.get(f"ahash_{skey}") != ahash:
                                res = pronunciation_agent.evaluate_pronunciation(audio_bytes, target_text, source_lang)
                                st.session_state[f"ahash_{skey}"] = ahash
                                st.session_state[skey] = res
                                add_pronunciation_score(st.session_state["user_id"], target_text, res.get('score', 0))
                            else:
                                res = st.session_state[skey]
                                
                            col_s1, col_s2 = st.columns([1, 3])
                            with col_s1:
                                st.metric("ë°œìŒ ?•í™•??, f"{res.get('score', 0)}??)
                            with col_s2:
                                st.markdown(f"**?¸ì‹??ë¬¸ì¥:** {res.get('transcription', '')}")
                                st.success(f"**AI ?œí„° ?¼ë“œë°?** {res.get('feedback', '')}")
                else:
                    st.warning("?„ì¬ ë¸Œë¼?°ì? ?˜ê²½?ì„œ??ë§ˆì´???…ë ¥(audio_input)??ì§€?í•˜ì§€ ?ŠìŠµ?ˆë‹¤.")

    st.markdown("---")

    # 3.6. ?­ 3?¨ê³„ ?€?„ì‰ ?°ìŠµ ëª¨ë“œ
    if contents:
        st.subheader("?­ 3?¨ê³„ ?€?„ì‰ ?°ìŠµ ëª¨ë“œ")
        st.write("? íƒ??ë¬¸ì¥???ì–´ë¯?ë°œìŒ??'?•ìƒ -> ?ë¦¬ê²?-> ?•ìƒ' 3?¨ê³„ë¡??£ê³  ?°ë¼??ë³´ì„¸??")
        
        shadow_options = [f"ë¬¸ì¥ {i+1}: {line.get('source_text', '')}" for i, line in enumerate(contents)]
        selected_shadow_str = st.selectbox("?€?„ì‰ ?°ìŠµ??ë¬¸ì¥??? íƒ?˜ì„¸??, shadow_options, key="shadow_select")
        
        if selected_shadow_str:
            selected_idx = shadow_options.index(selected_shadow_str)
            target_text = contents[selected_idx].get('source_text', '')
            source_lang = data.get("source_language", "en")
            current_gender = st.session_state.get("tts_gender", "male")
            voice = get_voice_for_language(source_lang, gender=current_gender)
            
            st.info(f"**?°ìŠµ ë¬¸ì¥:** {target_text}")
            
            # ?¤ë””???ì„±
            skey_normal = f"shadow_normal_{selected_idx}_{current_gender}"
            skey_slow = f"shadow_slow_{selected_idx}_{current_gender}"
            
            if skey_normal not in st.session_state:
                with st.spinner("?€?„ì‰ ?¤ë””?¤ë? ?ì„± ì¤‘ì…?ˆë‹¤..."):
                    st.session_state[skey_normal] = generate_audio_sync(target_text, voice, rate="+0%")
                    st.session_state[skey_slow] = generate_audio_sync(target_text, voice, rate="-30%")
            
            # HTML/JS 3-step player
            normal_b64 = base64.b64encode(st.session_state[skey_normal]).decode('utf-8')
            slow_b64 = base64.b64encode(st.session_state[skey_slow]).decode('utf-8')
            
            player_html = f"""
            <div style="text-align:center; margin:10px 0;">
                <button id="shadow-play-btn" style="background-color:#4CAF50; border:none; color:white; padding:10px 24px; font-size:16px; border-radius:8px; cursor:pointer; font-weight:bold;">
                    ??3?¨ê³„ ?€?„ì‰ ?£ê¸°
                </button>
                <div id="shadow-status" style="margin-top:10px; font-size:14px; color:#555;">?€ê¸?ì¤?..</div>
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
                            status.innerText = "1?¨ê³„: ?•ìƒ ?ë„ ?£ê¸°";
                            audioPlayer.src = normalAudio;
                            audioPlayer.play();
                            audioPlayer.onended = function() {{
                                step = 2;
                                status.innerText = "? ì‹œ ?€ê¸?..";
                                setTimeout(playStep, 1000);
                            }};
                        }} else if (step === 2) {{
                            status.innerText = "2?¨ê³„: ?ë¦° ?ë„ë¡??„ì–´ ?½ê¸°";
                            audioPlayer.src = slowAudio;
                            audioPlayer.play();
                            audioPlayer.onended = function() {{
                                step = 3;
                                status.innerText = "? ì‹œ ?€ê¸?..";
                                setTimeout(playStep, 1000);
                            }};
                        }} else if (step === 3) {{
                            status.innerText = "3?¨ê³„: ë§ˆì?ë§??•ìƒ ?ë„ ?€?„ì‰";
                            audioPlayer.src = normalAudio;
                            audioPlayer.play();
                            audioPlayer.onended = function() {{
                                step = 4;
                                status.innerText = "?„ë£Œ! ?´ì œ ë§ˆì´?¬ë¡œ ?¹ìŒ??ë³´ì„¸??";
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
                shadow_audio_val = st.audio_input("?€?„ì‰ ?„ë£Œ ??ë§ˆì´?¬ë¡œ ?°ë¼ ?½ì–´ë³´ì„¸??, key=f"shadow_input_{selected_idx}")
                if shadow_audio_val:
                    with st.spinner("AIê°€ ë°œìŒ??ë¶„ì„ ì¤‘ì…?ˆë‹¤..."):
                        audio_bytes = shadow_audio_val.getvalue()
                        ahash = hash(audio_bytes)
                        skey_res = f"shadow_res_{selected_idx}"
                        if st.session_state.get(f"ahash_{skey_res}") != ahash:
                            from app.agents import pronunciation_agent
                            res = pronunciation_agent.evaluate_pronunciation(audio_bytes, target_text, source_lang)
                            st.session_state[f"ahash_{skey_res}"] = ahash
                            st.session_state[skey_res] = res
                            add_pronunciation_score(st.session_state["user_id"], target_text, res.get('score', 0))
                        else:
                            res = st.session_state[skey_res]
                            
                        col_sh1, col_sh2 = st.columns([1, 3])
                        with col_sh1:
                            st.metric("ë°œìŒ ?•í™•??, f"{res.get('score', 0)}??)
                        with col_sh2:
                            st.markdown(f"**?¸ì‹??ë¬¸ì¥:** {res.get('transcription', '')}")
                            st.success(f"**AI ?œí„° ?¼ë“œë°?** {res.get('feedback', '')}")
            else:
                st.warning("?„ì¬ ë¸Œë¼?°ì? ?˜ê²½?ì„œ??ë§ˆì´???…ë ¥??ì§€?í•˜ì§€ ?ŠìŠµ?ˆë‹¤.")

    st.markdown("---")

    if audio_value and st.session_state.get("last_audio_id") != audio_value.file_id:
        st.session_state.last_audio_id = audio_value.file_id
        with st.spinner("?Œì„±???¸ì‹?˜ê³  ?ˆìŠµ?ˆë‹¤..."):
            from app.agents import pronunciation_agent
            audio_bytes = audio_value.read()
            mime_type = audio_value.type
            recognized_text = pronunciation_agent.transcribe_audio(audio_bytes, mime_type)
            if recognized_text and not recognized_text.startswith("[?Œì„± ?¸ì‹ ?¤íŒ¨"):
                processed_query = recognized_text
            else:
                st.error("?Œì„±???œë?ë¡??¸ì‹?˜ì? ëª»í–ˆ?µë‹ˆ?? ?¤ì‹œ ?œë„?´ì£¼?¸ìš”.")
    elif user_query:
        processed_query = user_query
            
    # ì§ˆë¬¸???‘ìˆ˜??ê²½ìš° (?ìŠ¤???ëŠ” ?Œì„±)
    if processed_query:
        # 1) ?¬ìš©??ë©”ì‹œì§€ ê¸°ë¡ ë°?ì¶œë ¥
        st.session_state.chat_history.append({"role": "user", "content": processed_query})
        with st.chat_message("user"):
            st.markdown(processed_query)
            
        # 2) AI ?œí„° ?µë? ?ì„± ë°?ì¶œë ¥
        with st.chat_message("assistant"):
            with st.spinner("AI ? ìƒ?˜ì´ ?µë????‘ì„± ì¤‘ì…?ˆë‹¤..."):
                from app.agents import tutor_agent
                student_level = st.session_state.get("student_level", "ì¤‘í•™êµ?1?™ë…„")
                ai_response = tutor_agent.get_tutor_chat_response(st.session_state.chat_history, data, mode=st.session_state.current_chat_mode, student_level=student_level)
                st.markdown(ai_response)
                
                audio_b64 = None
                # ?Œì„± ?µë? ëª¨ë“œê°€ ì¼œì ¸ ?ˆì„ ê²½ìš° TTS ë³€??
                if voice_reply_mode:
                    with st.spinner("?µë????Œì„±?¼ë¡œ ë³€??ì¤‘ì…?ˆë‹¤..."):
                        from app.core.tts_engine import generate_audio_sync, get_voice_for_language
                        # ?œí„°???œêµ­?´ë¡œ ?µë??˜ë?ë¡??œêµ­???¬ì„±/?¨ì„± ëª©ì†Œë¦??¬ìš©
                        tutor_voice = get_voice_for_language("ko", gender="female")
                        try:
                            audio_bytes = generate_audio_sync(ai_response, tutor_voice)
                            st.audio(audio_bytes, format="audio/mp3")
                            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
                        except Exception as e:
                            st.error(f"?Œì„± ë³€???¤íŒ¨: {e}")
                
        # 3) AI ?µë? ê¸°ë¡
        msg_record = {"role": "assistant", "content": ai_response}
        if audio_b64:
            msg_record["audio_b64"] = audio_b64
        st.session_state.chat_history.append(msg_record)
        st.rerun()
