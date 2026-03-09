from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from TTS.api import TTS
import os
import uuid
import shutil

app = FastAPI(title="XTTS Service")

# Global TTS model instance
tts = None
MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"

@app.on_event("startup")
async def startup_event():
    global tts
    print("Loading XTTS model. This may take a while...")
    tts = TTS(MODEL_NAME).to("cpu") # Using CPU mode
    print("XTTS model loaded successfully.")

@app.post("/generate-voice")
async def generate_voice(
    text: str = Form(...),
    language: str = Form("es"),
    speaker_wav: UploadFile = File(None)
):
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    output_dir = "generations"
    os.makedirs(output_dir, exist_ok=True)
    temp_speaker_path = None
    
    try:
        output_filename = f"output_{uuid.uuid4().hex[:8]}.wav"
        output_filepath = os.path.join(output_dir, output_filename)

        if speaker_wav:
            temp_speaker_path = f"temp_speaker_{uuid.uuid4().hex[:8]}.wav"
            with open(temp_speaker_path, "wb") as buffer:
                shutil.copyfileobj(speaker_wav.file, buffer)
            
            tts.tts_to_file(
                text=text,
                speaker_wav=temp_speaker_path,
                language=language,
                file_path=output_filepath
            )
        else:
            # "Ana Florence" is a native XTTS v2 speaker suitable as default
            tts.tts_to_file(
                text=text,
                speaker="Ana Florence",
                language=language,
                file_path=output_filepath
            )

        # Clean up temporary uploaded speaker wav
        if temp_speaker_path and os.path.exists(temp_speaker_path):
            os.remove(temp_speaker_path)

        return FileResponse(output_filepath, media_type="audio/wav", filename=output_filename)

    except Exception as e:
        if temp_speaker_path and os.path.exists(temp_speaker_path):
            os.remove(temp_speaker_path)
        raise HTTPException(status_code=500, detail=str(e))
