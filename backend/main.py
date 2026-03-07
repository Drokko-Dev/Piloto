from fastapi import FastAPI, UploadFile, Form, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import requests
from dotenv import load_dotenv

from services.ai_service import generate_script, generate_voiceover, generate_instagram_copy
from services.video_service import process_photos_to_preview, process_video_to_preview, finalize_video_with_voice

load_dotenv()

app = FastAPI(title="DentalFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("generations", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app.mount("/outputs", StaticFiles(directory="generations"), name="outputs")

def send_to_n8n(video_path: str, description: str, script: str):
    url = os.environ.get("N8N_WEBHOOK_URL")
    if not url: return
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
            data = {'description': description, 'script': script}
            requests.post(url, files=files, data=data)
            print(f"Sent webhook successfully to {url}")
    except Exception as e:
        print(f"Webhook error: {e}")

def cleanup_files(*paths):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

@app.post("/api/generate-script")
async def generate_script_endpoint(
    description: str = Form(...),
    media_type: str = Form(...),
    video_file: UploadFile = File(None),
    before_image: UploadFile = File(None),
    after_image: UploadFile = File(None)
):
    session_id = uuid.uuid4().hex[:8]
    
    try:
        vid_path = ""
        before_path = ""
        after_path = ""
        
        if media_type == 'video' and video_file:
            vid_path = f"uploads/{session_id}_{video_file.filename}"
            with open(vid_path, "wb") as f:
                shutil.copyfileobj(video_file.file, f)
                
            script = generate_script(description, 'video')
            
        elif media_type == 'images' and before_image and after_image:
            before_path = f"uploads/{session_id}_before_{before_image.filename}"
            after_path = f"uploads/{session_id}_after_{after_image.filename}"
            
            with open(before_path, "wb") as f, open(after_path, "wb") as f2:
                shutil.copyfileobj(before_image.file, f)
                shutil.copyfileobj(after_image.file, f2)
                
            script = generate_script(description, 'images')
            
        else:
            return {"error": "Invalid media provided"}
            
        return {
            "status": "success", 
            "script": script,
            "session_id": session_id,
            "media_type": media_type,
            "vid_path": vid_path,
            "before_path": before_path,
            "after_path": after_path
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/preview-video")
async def preview_video(
    request: Request,
    script_text: str = Form(...),
    media_type: str = Form(...),
    vid_path: str = Form(""),
    before_path: str = Form(""),
    after_path: str = Form("")
):
    try:
        if media_type == 'video' and vid_path:
            preview_path = process_video_to_preview(vid_path, script_text, "generations")
        elif media_type == 'images' and before_path and after_path:
            preview_path = process_photos_to_preview(before_path, after_path, script_text, "generations")
        else:
            return {"error": "Invalid media provided"}
            
        base_url = str(request.base_url).rstrip('/')
        filename = os.path.basename(preview_path)
        return {"status": "success", "preview_url": f"{base_url}/outputs/{filename}", "preview_path": preview_path}
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/finalize-video")
async def finalize_video(
    request: Request,
    script_text: str = Form(...),
    preview_path: str = Form(...)
):
    try:
        audio_path = "generations/voiceover_bf999b1f.mp3" #generate_voiceover(script_text, "generations")
        final_video_path = finalize_video_with_voice(preview_path, audio_path, "generations")
        
        base_url = str(request.base_url).rstrip('/')
        filename = os.path.basename(final_video_path)
        return {"status": "success", "final_video_url": f"{base_url}/outputs/{filename}", "final_video_path": final_video_path, "audio_path": audio_path}
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-instagram-copy")
async def generate_instagram(
    description: str = Form(...),
    script_text: str = Form(...)
):
    try:
        copy = generate_instagram_copy(description, script_text)
        return {"status": "success", "copy": copy}
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/publish")
async def publish(
    background_tasks: BackgroundTasks,
    description: str = Form(...),
    script_text: str = Form(...),
    copy_text: str = Form(...),
    final_video_path: str = Form(...),
    audio_path: str = Form(""),
    vid_path: str = Form(""),
    before_path: str = Form(""),
    after_path: str = Form(""),
    preview_path: str = Form("")
):
    try:
        combined_text = f"{script_text}\n\nINSTAGRAM COPY:\n{copy_text}"
        background_tasks.add_task(send_to_n8n, final_video_path, description, combined_text)
        background_tasks.add_task(cleanup_files, vid_path, before_path, after_path, preview_path, audio_path)
        return {"status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
