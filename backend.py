import os
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from character_consistency import CharacterProfile, generate_character_profile
from story_generator import Storybook, generate_story
from image_generator import generate_illustration, generate_all_story_illustrations
from pdf_generator import generate_pdf, sanitize_filename

app = FastAPI(
    title="MagicTale AI Backend",
    description="FastAPI service for AI-powered children's storybook generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("generated", exist_ok=True)
app.mount("/generated", StaticFiles(directory="generated"), name="generated")

class StoryRequest(BaseModel):
    prompt: str
    target_age: str = "4-8 years"
    api_key: Optional[str] = None

class ImageRequest(BaseModel):
    scene_description: str
    character: CharacterProfile
    page_number: int
    page_title: str
    story_id: str
    api_key: Optional[str] = None

class PDFRequest(BaseModel):
    storybook: Storybook
    image_paths: List[str]

class FullGenerationRequest(BaseModel):
    prompt: str
    target_age: str = "4-8 years"
    api_key: Optional[str] = None

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
    has_env_key = bool((os.getenv("OPEN_ROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip())
    return {
        "status": "online",
        "service": "MagicTale AI Backend",
        "openai_key_configured": has_env_key,
        "supported_stages": 5
    }

@app.post("/api/generate-story", response_model=Storybook)
def api_generate_story(req: StoryRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Story prompt cannot be empty.")
    storybook = generate_story(
        prompt=req.prompt,
        target_age=req.target_age,
        api_key=req.api_key
    )
    return storybook

@app.post("/api/generate-image")
def api_generate_image(req: ImageRequest):
    story_dir = os.path.join("generated", req.story_id)
    os.makedirs(story_dir, exist_ok=True)
    out_file = os.path.join(story_dir, f"page_{req.page_number}.jpg")
    
    result = generate_illustration(
        scene_description=req.scene_description,
        character=req.character,
        page_number=req.page_number,
        page_title=req.page_title,
        output_path=out_file,
        story_id=req.story_id,
        api_key=req.api_key
    )
    return result

@app.post("/api/generate-pdf")
def api_generate_pdf(req: PDFRequest):
    output_dir = os.path.join("generated", "pdfs")
    pdf_path = generate_pdf(req.storybook, req.image_paths, output_dir)
    filename = os.path.basename(pdf_path)
    return {
        "pdf_path": pdf_path,
        "filename": filename,
        "download_url": f"/api/download-pdf/{filename}"
    }

@app.post("/api/generate-storybook")
def api_generate_full_storybook(req: FullGenerationRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Story prompt cannot be empty.")
    
    story_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join("generated", story_id)
    os.makedirs(output_dir, exist_ok=True)

    storybook = generate_story(
        prompt=req.prompt,
        target_age=req.target_age,
        api_key=req.api_key
    )

    image_results = generate_all_story_illustrations(
        pages=storybook.pages,
        character=storybook.character,
        output_dir=output_dir,
        story_id=story_id,
        api_key=req.api_key
    )

    image_paths = [res["image_path"] for res in image_results]
    
    pdf_dir = os.path.join("generated", "pdfs")
    pdf_path = generate_pdf(storybook, image_paths, pdf_dir)
    filename = os.path.basename(pdf_path)

    return {
        "story_id": story_id,
        "storybook": storybook.dict(),
        "images": image_results,
        "pdf_path": pdf_path,
        "filename": filename,
        "download_url": f"/api/download-pdf/{filename}"
    }

@app.get("/api/download-pdf/{filename}")
def download_pdf(filename: str):
    clean_name = os.path.basename(filename)
    file_path = os.path.join("generated", "pdfs", clean_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Requested PDF file not found.")
    return FileResponse(
        path=file_path,
        filename=clean_name,
        media_type="application/pdf"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
