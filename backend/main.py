from fastapi import FastAPI, UploadFile, Form, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import requests
import boto3
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

os.makedirs(os.path.join("generations", "00_inputs"), exist_ok=True)
os.makedirs(os.path.join("generations", "01_scripts"), exist_ok=True)
os.makedirs(os.path.join("generations", "02_audio"), exist_ok=True)
os.makedirs(os.path.join("generations", "03_preview"), exist_ok=True)
os.makedirs(os.path.join("generations", "04_temp"), exist_ok=True)
os.makedirs(os.path.join("generations", "05_preview_nosub"), exist_ok=True)
os.makedirs(os.path.join("generations", "06_final"), exist_ok=True)

app.mount("/outputs", StaticFiles(directory="generations"), name="outputs")
app.mount("/videos", StaticFiles(directory="generations/06_final"), name="videos")

def upload_video_to_r2(video_path: str):
    bucket = os.getenv("R2_BUCKET")
    if not bucket:
        raise ValueError("ERROR: La variable R2_BUCKET no está configurada en el .env")
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key = os.getenv("R2_ACCESS_KEY")
    secret_key = os.getenv("R2_SECRET_KEY")
    public_url = os.getenv("R2_PUBLIC_URL")

    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto"
    )

    filename = os.path.basename(video_path)

    s3.upload_file(
        video_path,
        bucket,
        filename,
        ExtraArgs={"ContentType": "video/mp4"}
    )

    return f"{public_url}/{filename}"

def send_to_n8n(video_path: str, description: str, script: str):
    url = os.environ.get("N8N_WEBHOOK_URL")
    print(f"DEBUG: Iniciando envío a n8n. URL: {url}") # Agrega esto
    
    if not url:
        print("DEBUG: No hay URL de webhook configurada")
        return

    try:
        print(f"DEBUG: Subiendo {video_path} a R2...")
        video_url = upload_video_to_r2(video_path)
        print(f"DEBUG: Video subido con éxito: {video_url}")

        payload = {
            "video_url": video_url,
            "caption": script
        }

        response = requests.post(url, json=payload)
        print(f"DEBUG: Respuesta de n8n: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"ERROR CRÍTICO en Webhook: {str(e)}")
        import traceback
        traceback.print_exc() # Esto te dirá la línea exacta del fallo

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
            vid_path = f"generations/00_inputs/{session_id}_{video_file.filename}"
            with open(vid_path, "wb") as f:
                shutil.copyfileobj(video_file.file, f)
                
            script = generate_script(description, 'video')
            
        elif media_type == 'images' and before_image and after_image:
            before_path = f"generations/00_inputs/{session_id}_before_{before_image.filename}"
            after_path = f"generations/00_inputs/{session_id}_after_{after_image.filename}"
            
            with open(before_path, "wb") as f, open(after_path, "wb") as f2:
                shutil.copyfileobj(before_image.file, f)
                shutil.copyfileobj(after_image.file, f2)
                
            script = generate_script(description, 'images')
            
        else:
            return {"error": "Invalid media provided"}
            
        script_path = f"generations/01_scripts/{session_id}_script.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
            
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
        # NEW pipeline order: Voice generated before preview
        audio_path = generate_voiceover(script_text, os.path.join("generations", "02_audio"))
        
        if media_type == 'video' and vid_path:
            preview_path = process_video_to_preview(vid_path, script_text, audio_path, os.path.join("generations", "03_preview"))
        elif media_type == 'images' and before_path and after_path:
            preview_path = process_photos_to_preview(before_path, after_path, script_text, audio_path, os.path.join("generations", "03_preview"))
        else:
            return {"error": "Invalid media provided"}
            
        base_url = str(request.base_url).rstrip('/')
        # Return path relative to generations so the frontend can read from /outputs
        rel_path = os.path.relpath(preview_path, "generations")
        return {"status": "success", "preview_url": f"{base_url}/outputs/{rel_path}", "preview_path": preview_path, "audio_path": audio_path}
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/finalize-video")
async def finalize_video(
    request: Request,
    script_text: str = Form(...),
    preview_path: str = Form(...),
    audio_path: str = Form(...)
):
    try:
        final_video_path = finalize_video_with_voice(preview_path, audio_path, os.path.join("generations", "06_final"))
        
        base_url = str(request.base_url).rstrip('/')
        rel_path = os.path.relpath(final_video_path, "generations")
        return {"status": "success", "final_video_url": f"{base_url}/outputs/{rel_path}", "final_video_path": final_video_path, "audio_path": audio_path}
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
        #combined_text = f"{script_text}\n\nINSTAGRAM COPY:\n{copy_text}"
        background_tasks.add_task(send_to_n8n, final_video_path, description, copy_text)
        
        # Cleanup
        temps_dir = os.path.join("generations", "04_temp")
        previews_dir = os.path.join("generations", "03_preview")
        background_tasks.add_task(cleanup_files, vid_path, before_path, after_path, preview_path, audio_path)
        
        # Clean folder entirely, we can't reliably know the temp MPY intermediate files 
        def cleanup_temp_dirs(temps_dir):
            if os.path.exists(temps_dir):
                import shutil
                try:
                    for filename in os.listdir(temps_dir):
                        file_path = os.path.join(temps_dir, filename)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                except Exception:
                    pass
        background_tasks.add_task(cleanup_temp_dirs, temps_dir)
        
        return {"status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
