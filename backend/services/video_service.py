from moviepy import VideoFileClip, ImageClip, TextClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip
from moviepy import vfx
import os
import uuid
import subprocess
from services.subtitle_service import create_subtitles, generate_whisper_subtitles

def add_ken_burns(clip, duration, zoom_factor=0.08):
    """Dynamic Ken Burns effect (zoom in slowly)."""
    # Requires an active resize function over time `t`
    def resize_func(t):
        return 1 + zoom_factor * (t / duration)
    return clip.resized(resize_func)

def mix_background_music(audio_clip, audio_dur):
    bg_music_path = os.path.join(os.getcwd(), "assets", "background.mp3")
    if os.path.exists(bg_music_path):
        bg_clip = AudioFileClip(bg_music_path).volumex(0.1)
        if bg_clip.duration < audio_dur:
            bg_clip = bg_clip.with_effects([vfx.Loop(duration=audio_dur)])
        else:
            bg_clip = bg_clip.with_duration(audio_dur)
        if audio_clip:
            return CompositeAudioClip([audio_clip, bg_clip])
        return bg_clip
    return audio_clip


def process_photos_to_preview(before_path, after_path, script, audio_path, output_dir):
    audio_dur = max(len(script.split()) * 0.45, 12.0)
    half_dur = audio_dur / 2
    
    target_w, target_h = 1080, 1920
    
    # 1. Base Images Cropped to Vertical Space
    clip_before = ImageClip(before_path).resized(height=target_h).cropped(x_center=target_h/2, width=target_w)
    clip_after = ImageClip(after_path).resized(height=target_h).cropped(x_center=target_h/2, width=target_w)

    # 2. Add Animations (Dynamic Ken Burns Zoom In)
    clip_before = add_ken_burns(clip_before, half_dur + 0.5).with_duration(half_dur + 0.5)
    clip_after = add_ken_burns(clip_after, half_dur + 0.5).with_duration(half_dur + 0.5)
    
    # Transition
    clip_after = clip_after.with_effects([vfx.CrossFadeIn(0.5)])
    
    video = concatenate_videoclips([clip_before.with_position("center"), clip_after.with_position("center")], padding=-0.5, method="compose")
    
    # Llamamos a nuestra nueva función de normalización
    processed_voice_path = normalize_audio(audio_path)
    
    if processed_voice_path and os.path.exists(processed_voice_path):
        voice_clip = AudioFileClip(processed_voice_path)
        # Ajuste de duración para evitar cortes abruptos
        voice_clip = voice_clip.with_duration(voice_clip.duration - 0.05)
        final_audio = mix_background_music(voice_clip, audio_dur)
    else:
        final_audio = mix_background_music(None, audio_dur)

    layers = [video]
    
    # Overlay Labels
    try:
        txt_before = TextClip(text="BEFORE", font="Liberation-Sans", font_size=90, color='white', stroke_color='black', stroke_width=2).with_position(('center', 150)).with_duration(half_dur)
        txt_after = TextClip(text="AFTER", font="Liberation-Sans", font_size=90, color='white', stroke_color='black', stroke_width=2).with_position(('center', 150)).with_start(half_dur).with_duration(half_dur)
        layers.extend([txt_before, txt_after])
    except Exception as e:
        pass

    # Base video without subtitles saved separately
    base_video = CompositeVideoClip(layers)
    if final_audio:
        base_video = base_video.with_audio(final_audio)
    base_video = base_video.with_duration(audio_dur)
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"video_photos_preview_{uuid.uuid4().hex[:8]}.mp4")
    
    nosub_dir = os.path.join("generations", "05_preview_nosub")
    os.makedirs(nosub_dir, exist_ok=True)
    nosub_path = os.path.join(nosub_dir, os.path.basename(out_path).replace(".mp4", "_nosub.mp4"))
    
    temp_audio = os.path.join(os.getcwd(), "generations", "04_temp", f"temp_aud_{uuid.uuid4().hex[:8]}.m4a")
    
    # Save no-subtitles base
    base_video.write_videofile(nosub_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, threads=2)

    # Add fallback subtitles for preview return
    try:
        sub_clips = create_subtitles(script, audio_dur, target_w, target_h)
        layers.extend(sub_clips)
    except Exception as e:
        pass

    final_video = CompositeVideoClip(layers)
    if final_audio:
        final_video = final_video.with_audio(final_audio)
    final_video = final_video.with_duration(audio_dur)
    
    final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, threads=2)
    return out_path

def process_video_to_preview(video_path, script, audio_path, output_dir):
    audio_dur = max(len(script.split()) * 0.45, 12.0)
    
    vid_clip = VideoFileClip(video_path)
    target_w, target_h = 1080, 1920
    
    # Crop to 9:16
    if vid_clip.h < vid_clip.w:
        vid_clip = vid_clip.resized(height=target_h)
        vid_clip = vid_clip.cropped(x_center=vid_clip.w/2, width=target_w)
    else:
        vid_clip = vid_clip.resized(width=target_w)
        vid_clip = vid_clip.cropped(y_center=vid_clip.h/2, height=target_h)
        
    if vid_clip.duration > audio_dur:
        vid_clip = vid_clip.with_duration(audio_dur)
    else:
        vid_clip = vid_clip.with_effects([vfx.Loop(duration=audio_dur)])
        
    if audio_path and os.path.exists(audio_path):
        voice_clip = AudioFileClip(audio_path)
        final_audio = mix_background_music(voice_clip, audio_dur)
    else:
        final_audio = mix_background_music(None, audio_dur)
    layers = [vid_clip]
    
    # Base video without subtitles saved separately
    base_video = CompositeVideoClip(layers)
    if final_audio:
        base_video = base_video.with_audio(final_audio)
    base_video = base_video.with_duration(audio_dur)
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"video_vid_preview_{uuid.uuid4().hex[:8]}.mp4")
    
    nosub_dir = os.path.join("generations", "05_preview_nosub")
    os.makedirs(nosub_dir, exist_ok=True)
    nosub_path = os.path.join(nosub_dir, os.path.basename(out_path).replace(".mp4", "_nosub.mp4"))
    
    temp_audio = os.path.join(os.getcwd(), "generations", "04_temp", f"temp_aud_{uuid.uuid4().hex[:8]}.m4a")
    base_video.write_videofile(nosub_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, threads=2)

    # Add fallback subtitles for preview return
    try:
        sub_clips = create_subtitles(script, audio_dur, target_w, target_h)
        layers.extend(sub_clips)
    except Exception as e:
        pass
        
    final_video = CompositeVideoClip(layers)
    if final_audio:
        final_video = final_video.with_audio(final_audio)
    final_video = final_video.with_duration(audio_dur)
    
    final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, threads=2)
    return out_path

def normalize_audio(audio_path):
    """Normaliza el audio usando FFmpeg para un volumen profesional y constante."""
    if not audio_path or not os.path.exists(audio_path):
        return audio_path

    norm_path = audio_path.replace(".wav", "_norm.wav")
    try:
        # Aplicamos compresión y normalización para que la voz resalte sobre la música
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_path, 
            "-af", "loudnorm,acompressor=threshold=-18dB:ratio=2:attack=200:release=1000", 
            norm_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return norm_path
    except Exception as e:
        print(f"Warning: Audio normalization failed: {e}. Usando original.")
        return audio_path

def finalize_video_with_voice(preview_path, audio_path, output_dir):
    # Normalize volume using ffmpeg before mixing
    #norm_audio_path = audio_path.replace(".wav", "_norm.wav")
    norm_audio_path = normalize_audio(audio_path)
    voice_clip = AudioFileClip(norm_audio_path)

    # Try to load the no-subtitle version if available to avoid double subtitles
    nosub_dir = os.path.join("generations", "05_preview_nosub")
    nosub_path = os.path.join(nosub_dir, os.path.basename(preview_path).replace(".mp4", "_nosub.mp4"))
    
    if os.path.exists(nosub_path):
        vid_clip = VideoFileClip(nosub_path)
    else:
        vid_clip = VideoFileClip(preview_path)
    
    # 2. Strict Sync using exact audio duration (auto-scales transitions)
    final_duration = max(voice_clip.duration - 0.05, 0)
    
    # Use speedx to stretch or shrink the video to perfectly match audio length
    factor = vid_clip.duration / final_duration
    vid_clip = vid_clip.without_audio().fx(vfx.speedx, factor).with_duration(final_duration)
    
    # Apply Whisper accurate subtitles
    try:
        whisper_clips = generate_whisper_subtitles(norm_audio_path, vid_clip.w, vid_clip.h)
        if whisper_clips:
            vid_clip = CompositeVideoClip([vid_clip] + whisper_clips).with_duration(final_duration)
    except Exception as e:
        print(f"Warning: Whisper subtitle generation failed: {e}. Falling back without accurate subtitles.")
    
    # 3. Mix new background music with 10% volume + voice
    bg_music_path = os.path.join(os.getcwd(), "assets", "background.mp3")
    if os.path.exists(bg_music_path):
        bg_clip = AudioFileClip(bg_music_path).volumex(0.1)
        if bg_clip.duration < final_duration:
            bg_clip = bg_clip.with_effects([vfx.Loop(duration=final_duration)])
        else:
            bg_clip = bg_clip.with_duration(final_duration)
        final_audio = CompositeAudioClip([bg_clip, voice_clip]).with_duration(final_duration)
    else:
        final_audio = voice_clip.with_duration(final_duration)
        
    final_video = vid_clip.with_audio(final_audio)
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"video_final_{uuid.uuid4().hex[:8]}.mp4")
    
    # 4. Error Handling & Retry
    temp_audio = os.path.join(os.getcwd(), "generations", "04_temp", f"temp_aud_{uuid.uuid4().hex[:8]}.m4a")
    try:
        final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, threads=2)
    except Exception as e:
        print(f"Warning: Render failed with duration {final_duration}. Retrying with shorter duration. Error: {e}")
        retry_duration = final_duration - 0.1
        if retry_duration > 0:
            final_video = final_video.with_duration(retry_duration)
            final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, threads=2)
        else:
            raise e
    
    # Close clips to free memory
    try:
        vid_clip.close()
        voice_clip.close()
        final_video.close()
    except:
        pass
    
    return out_path
