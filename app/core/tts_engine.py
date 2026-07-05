import asyncio
import edge_tts

def get_voice_for_language(lang_code: str, gender: str = "male") -> str:
    lang_code = lang_code.lower().strip()
    gender = gender.lower().strip()
    
    mapping = {
        "en": {"male": "en-US-GuyNeural", "female": "en-US-AriaNeural"},
        "ja": {"male": "ja-JP-KeitaNeural", "female": "ja-JP-NanamiNeural"},
        "zh": {"male": "zh-CN-YunxiNeural", "female": "zh-CN-XiaoxiaoNeural"},
        "es": {"male": "es-ES-AlvaroNeural", "female": "es-ES-ElviraNeural"},
        "fr": {"male": "fr-FR-HenriNeural", "female": "fr-FR-DeniseNeural"},
        "de": {"male": "de-DE-KillianNeural", "female": "de-DE-AmalaNeural"},
        "ko": {"male": "ko-KR-InJoonNeural", "female": "ko-KR-SunHiNeural"}
    }
    
    # 언어 코드가 'en-us' 처럼 들어올 수도 있으므로 앞 2자리만 확인
    prefix = lang_code[:2]
    lang_voices = mapping.get(prefix, mapping["en"])
    return lang_voices.get(gender, lang_voices["male"])

def generate_audio_sync(text: str, voice: str, rate: str = "+0%") -> bytes:
    """Streamlit과 같은 동기 환경에서 비동기 edge-tts를 안전하게 실행합니다."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    audio_data = bytearray()
    
    async def _generate():
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
                
    try:
        # 이미 실행 중인 이벤트 루프가 없을 경우
        asyncio.run(_generate())
    except RuntimeError:
        # 이벤트 루프가 이미 실행 중인 경우 (Streamlit 쓰레드 등)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        
    return bytes(audio_data)
