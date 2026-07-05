from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
import io
import os
import wave
import edge_tts
from google import genai
from google.genai import types

router = APIRouter()
client = None

def get_gemini_client():
    global client
    if client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")
        client = genai.Client(api_key=api_key)
    return client

@router.post("/api/tts")
async def generate_tts(
    text: str = Body(..., embed=True),
    gender: str = Body("neutral", embed=True),
    speed: float = Body(1.0, embed=True),
    lang: str = Body("en-US", embed=True),
    engine: str = Body("edge", embed=True)
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
        
    try:
        if engine == "google":
            gemini_client = get_gemini_client()
            
            # Dialogue voices: Puck (male), Aoede (female)
            # Narrator voices: Charon (male), Kore (female), Leda (neutral)
            voice_mapping = {
                "male": "Puck",
                "female": "Aoede",
                "neutral": "Leda",
                "narrator_male": "Charon",
                "narrator_female": "Kore"
            }
            selected_voice = voice_mapping.get(gender.lower(), "Leda")
            
            prompt = f"Read this aloud clearly:\n\n{text}"
            
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash-preview-tts',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=selected_voice
                            )
                        )
                    )
                )
            )
            
            pcm_data = None
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    pcm_data = part.inline_data.data
                    break
                    
            if not pcm_data:
                raise HTTPException(status_code=500, detail="No audio data returned from Gemini.")
                
            # Convert PCM 16-bit 24kHz Mono to WAV
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(pcm_data)
                
            wav_io.seek(0)
            return StreamingResponse(wav_io, media_type="audio/wav")
            
        else:
            # Edge TTS logic
            if lang.startswith("ko"):
                voice_mapping = {
                    "neutral": "ko-KR-InJoonNeural",
                    "narrator_male": "ko-KR-InJoonNeural",
                    "narrator_female": "ko-KR-SunHiNeural",
                    "male": "ko-KR-InJoonNeural",
                    "female": "ko-KR-SunHiNeural"
                }
            else:
                voice_mapping = {
                    "neutral": "en-US-GuyNeural",
                    "narrator_male": "en-US-GuyNeural",
                    "narrator_female": "en-US-AriaNeural",
                    "male": "en-US-ChristopherNeural",
                    "female": "en-US-MichelleNeural"
                }
                
            selected_voice = voice_mapping.get(gender.lower(), voice_mapping["neutral"])
            
            rate_percent = int((speed - 1.0) * 100)
            rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
            
            communicate = edge_tts.Communicate(text, selected_voice, rate=rate_str)
            
            async def audio_generator():
                try:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            yield chunk["data"]
                except edge_tts.exceptions.NoAudioReceived:
                    # If text contains only punctuation or whitespace, edge_tts raises this.
                    # We can safely yield nothing, which results in an empty audio file.
                    pass

            return StreamingResponse(
                audio_generator(), 
                media_type="audio/mpeg"
            )
        
    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
