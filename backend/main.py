from fastapi import FastAPI, UploadFile, Form, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import requests
from dotenv import load_dotenv

from services.ai_service import generate_script, generate_voiceover
from services.video_service import process_photos_to_video, process_video_to_video

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

@app.post("/api/generate")
async def generate_video(
    background_tasks: BackgroundTasks,
    request: Request,
    description: str = Form(...),
    media_type: str = Form(...),
    video_file: UploadFile = File(None),
    before_image: UploadFile = File(None),
    after_image: UploadFile = File(None)
):
    session_id = uuid.uuid4().hex[:8]
    
    try:
        if media_type == 'video' and video_file:
            vid_path = f"uploads/{session_id}_{video_file.filename}"
            with open(vid_path, "wb") as f:
                shutil.copyfileobj(video_file.file, f)
                
            script = generate_script(description, 'video')
            audio_path = generate_voiceover(script, "generations")
            final_video_path = process_video_to_video(vid_path, audio_path, "generations")
            
        elif media_type == 'images' and before_image and after_image:
            before_path = f"uploads/{session_id}_before_{before_image.filename}"
            after_path = f"uploads/{session_id}_after_{after_image.filename}"
            
            with open(before_path, "wb") as f, open(after_path, "wb") as f2:
                shutil.copyfileobj(before_image.file, f)
                shutil.copyfileobj(after_image.file, f2)
                
            script = generate_script(description, 'images')
            audio_path = generate_voiceover(script, "generations")
            final_video_path = process_photos_to_video(before_path, after_path, audio_path, "generations")
            
        else:
            return {"error": "Invalid media provided"}
            
        background_tasks.add_task(send_to_n8n, final_video_path, description, script)
        
        base_url = str(request.base_url).rstrip('/')
        filename = os.path.basename(final_video_path)
        video_url = f"{base_url}/outputs/{filename}"
        
        return {"status": "success", "video_url": video_url, "script": script}
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Return HTTP 500 equivalent in detail for frontend
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
