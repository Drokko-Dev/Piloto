import os
import requests
from openai import OpenAI
import uuid

def generate_script(description: str, media_type: str) -> str:
    """Generate a short TikTok/Reel script based on technical description."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    media_context = "a clinical video" if media_type == 'video' else "before and after photos"
    prompt = f"""
    Act as an engaging, professional dentist creating a TikTok/Reel.
    You are showing {media_context} of a dental procedure.
    Technical Description: {description}
    
    Write a short 15-20 second voiceover script that translates this technical description into an engaging, easy-to-understand explanation for a general audience.
    Keep it professional but accessible. Output ONLY the spoken text, no actions, no titles, no emojis or hashtags.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional dentist AI assistant creating content for patients."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    return response.choices[0].message.content.strip()

def generate_voiceover(text: str, output_dir: str) -> str:
    """Generate voiceover using ElevenLabs 'Marcus' voice."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set")
        
    voice_id = os.getenv("ELEVENLABS_VOICE_ID") # Marcus
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"ElevenLabs Error {response.status_code}: {response.text}")
        
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"voiceover_{uuid.uuid4().hex[:8]}.mp3")
    
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                
    return file_path
