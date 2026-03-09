import os
import requests
import uuid
import re
import subprocess
import time

def split_into_sentences(text: str):
    # Natural sentence splitting on punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # filter empty
    return [s.strip() for s in sentences if s.strip()]

def generate_voice(text: str, output_dir: str, speaker_wav: str = None) -> str:
    """Generate voiceover using the external XTTS service via HTTP POST."""
    
    url = "http://xtts-service:8001/generate-voice"
    os.makedirs(output_dir, exist_ok=True)
    temp_dir = os.path.join(output_dir, "temp_tts")
    os.makedirs(temp_dir, exist_ok=True)
    
    sentences = split_into_sentences(text)
    temp_files = []
    
    try:
        f = None
        speaker_tuple = None
        if speaker_wav and os.path.exists(speaker_wav):
            f = open(speaker_wav, "rb")
            speaker_tuple = (os.path.basename(speaker_wav), f, "audio/wav")

        for i, sentence in enumerate(sentences):
            data = {"text": sentence, "language": "es"}
            files = {}
            if speaker_tuple:
                # Rewind pointer for each HTTP request
                f.seek(0)
                files["speaker_wav"] = speaker_tuple
                
            max_retries = 10
            retry_delay = 3

            for attempt in range(max_retries):
                try:
                    response = requests.post(url, data=data, files=files if files else None)
                    break
                except requests.exceptions.ConnectionError:
                    if attempt == max_retries - 1:
                        raise
                    print(f"XTTS not ready yet... retry {attempt+1}/{max_retries}")
                    time.sleep(retry_delay)
            
            if response.status_code != 200:
                raise Exception(f"XTTS Service Error {response.status_code}: {response.text}")
                
            part_path = os.path.join(temp_dir, f"temp_part_{uuid.uuid4().hex[:8]}.wav")
            with open(part_path, "wb") as out_f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        out_f.write(chunk)
                        
            temp_files.append(part_path)
            
        if f:
            f.close()
            
        # Concatenate temp_files using ffmpeg
        final_path = os.path.join(output_dir, f"voiceover_{uuid.uuid4().hex[:8]}.wav")
        list_file = os.path.join(temp_dir, f"concat_list_{uuid.uuid4().hex[:8]}.txt")
        
        with open(list_file, "w") as lf:
            for tf in temp_files:
                lf.write(f"file '{os.path.abspath(tf)}'\n")
        
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", final_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        
        # Cleanup temp directory
        for tf in temp_files:
            if os.path.exists(tf): os.remove(tf)
        if os.path.exists(list_file): os.remove(list_file)
            
        return final_path
        
    except Exception as e:
        print(f"ERROR: XTTS generation failed: {str(e)}")
        # Cleanup
        for tf in temp_files:
            if os.path.exists(tf): os.remove(tf)
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to generate TTS via XTTS: {str(e)}")
