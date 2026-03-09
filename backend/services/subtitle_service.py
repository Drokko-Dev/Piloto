import re
from moviepy import TextClip

def split_text_into_chunks(text: str, max_words=3):
    """
    Split text into logical chunks, respecting punctuation, and keeping word count max_words per chunk.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= max_words or any(p in word for p in ['.', ',', '?', '!']):
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

def create_subtitles(text: str, audio_dur: float, target_w: int, target_h: int):
    """
    Create subtitle TextClips synchronized to audio_dur proportionally.
    (Used as fallback for previews)
    """
    chunks = split_text_into_chunks(text, max_words=3)
    if not chunks:
        return []
        
    chunk_dur = audio_dur / len(chunks)
    clips = []
    
    for i, chunk in enumerate(chunks):
        txt = TextClip(
            text=chunk,
            font="Liberation-Sans",
            font_size=65,
            color='white',
            stroke_color='black',
            stroke_width=2.5
        )
        txt = txt.with_position(('center', target_h - 250))
        txt = txt.with_start(i * chunk_dur).with_duration(chunk_dur)
        clips.append(txt)
        
    return clips


# Global instance to load the model only once
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        from faster_whisper import WhisperModel
        # Using a small, lightweight model by default to preserve RAM
        print("Loading Whisper model...")
        whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return whisper_model

def generate_whisper_subtitles(audio_path: str, target_w: int, target_h: int):
    """
    Generate accurate TextClips for MoviePy using faster-whisper word timestamps.
    """
    model = get_whisper_model()
    # word_timestamps=True is the key to accurate syncing
    segments, info = model.transcribe(audio_path, language="es", word_timestamps=True)
    
    clips = []
    for segment in segments:
        current_chunk = []
        chunk_start = None
        
        for word in segment.words:
            if chunk_start is None:
                chunk_start = word.start
            current_chunk.append(word.word.strip())
            
            # Flush chunk if we hit 3 words or punctuation
            if len(current_chunk) >= 3 or any(p in word.word for p in ['.', ',', '?', '!']):
                txt_str = " ".join(current_chunk).strip()
                txt_clip = TextClip(
                    text=txt_str,
                    font="Liberation-Sans",
                    font_size=65,
                    color='white',
                    stroke_color='black',
                    stroke_width=2.5
                ).with_position(('center', target_h - 250))
                
                end_time = min(word.end, audio_duration - 0.05)
                txt_clip = txt_clip.with_start(chunk_start).with_end(end_time)
                clips.append(txt_clip)
                
                current_chunk = []
                chunk_start = None
                
        # Remainder words for the segment if any
        if current_chunk:
            txt_str = " ".join(current_chunk).strip()
            txt_clip = TextClip(
                text=txt_str,
                font="Liberation-Sans",
                font_size=65,
                color='white',
                stroke_color='black',
                stroke_width=2.5
            ).with_position(('center', target_h - 250))
            txt_clip = txt_clip.with_start(chunk_start).with_end(segment.end)
            clips.append(txt_clip)
            
    return clips
