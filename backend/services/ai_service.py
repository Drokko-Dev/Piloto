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
    
    Prompt: Escribe un guion corto de 15-20 segundos con voz en off que traduzca esta descripción técnica en una explicación atractiva y fácil de entender para el paciente.
    Mantenlo profesional pero accesible. SACA SÓLO el texto hablado, sin acciones, sin títulos, sin emojis o hashtags.
    IMPORTANTE: El guion DEBE estar SIEMPRE en español de Chile (chilenismos moderados, tono cercano pero profesional).
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
            "stability": 0.4,
            "similarity_boost": 0.85
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

def generate_instagram_copy(description: str, script: str) -> str:
    """Generate an Instagram post copy with emojis and hashtags based on the clinical description and script."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    prompt = f"""
    Act as a professional and engaging community manager for a dental clinic in Chile.
    Based on the following script from a recent procedure video and the original technical description, write an engaging Instagram caption.
    
    Technical Description: {description}
    Video Script: {script}
    
    The caption must be in Chilean Spanish, informative but friendly.
    Include relevant emojis and 5-7 relevant hashtags at the end.
    Output ONLY the text for the caption.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert social media manager for dental clinics."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=250
    )
    
    return response.choices[0].message.content.strip()
