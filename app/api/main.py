import os
import io
import PIL.Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 내부 AI 엔진 임포트
from app.agents import parser_agent, configure_gemini

# 환경변수 로드 및 AI 엔진 초기화
load_dotenv()
configure_gemini()

app = FastAPI(title="EduAI Backend API", description="AI Tutor API Server")

from app.api.tts import router as tts_router
app.include_router(tts_router)


# 프론트엔드 통신을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 상용 배포 시 특정 도메인으로 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextParseRequest(BaseModel):
    text: str
    generate_ai_quiz: bool = False

@app.post("/api/parse/text")
async def parse_text(request: TextParseRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="텍스트가 비어 있습니다.")
    
    try:
        result = parser_agent.parse_from_text(request.text, extract_original_questions=request.generate_ai_quiz)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parse/image")
async def parse_image(file: UploadFile = File(...), generate_ai_quiz: bool = Form(False)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    
    try:
        # 이미지를 메모리로 읽어들여 PIL Image 객체로 변환
        contents = await file.read()
        image = PIL.Image.open(io.BytesIO(contents))
        
        result = parser_agent.parse_from_image(image, extract_original_questions=generate_ai_quiz)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/health")
async def health_check():
    return {"status": "ok"}

frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend_html")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/reading")
    async def serve_reading():
        return FileResponse(os.path.join(frontend_path, "reading.html"))

    @app.get("/tutor")
    async def serve_tutor():
        return FileResponse(os.path.join(frontend_path, "tutor.html"))
else:
    @app.get("/")
    async def serve_index():
        return {"message": "frontend_html 폴더가 없습니다."}
