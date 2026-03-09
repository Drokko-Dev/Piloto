import os
import requests
from openai import OpenAI
import uuid
import re
import subprocess

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

from services.tts_service import generate_voice

def generate_voiceover(text: str, output_dir: str) -> str:
    """Generate voiceover by delegating to the new tts_service."""
    return generate_voice(text, output_dir)

def normalize_audio(input_file: str, output_file: str):
    """Normalize audio volume using ffmpeg."""
    
    command = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-af", "loudnorm,acompressor=threshold=-18dB:ratio=2:attack=200:release=1000",
        output_file
    ]

    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def clean_tts_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)

    # pausas naturales
    text = text.replace(".", ". ")
    text = text.replace(",", ", ")
    text = text.replace("...", ".")

    # pausa extra después de frases
    text = re.sub(r'([.!?])', r'\1 ', text)

    return text.strip()

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
