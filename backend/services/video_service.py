from moviepy import VideoFileClip, ImageClip, TextClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip
from moviepy import vfx
import os
import uuid

def add_ken_burns(clip, duration, zoom_factor=0.08):
    """Dynamic Ken Burns effect (zoom in slowly)."""
    # Requires an active resize function over time `t`
    def resize_func(t):
        return 1 + zoom_factor * (t / duration)
    return clip.resized(resize_func)

def mix_background_music(audio_clip, audio_dur):
    bg_music_path = os.path.join(os.getcwd(), "assets", "background.mp3")
    if os.path.exists(bg_music_path):
        bg_clip = AudioFileClip(bg_music_path).with_effects([vfx.MultiplyVolume(0.1)])
        if bg_clip.duration < audio_dur:
            bg_clip = bg_clip.with_effects([vfx.Loop(duration=audio_dur)])
        else:
            bg_clip = bg_clip.with_duration(audio_dur)
        if audio_clip:
            return CompositeAudioClip([audio_clip, bg_clip])
        return bg_clip
    return audio_clip

def create_subtitles(text, duration, target_w, target_h):
    words = text.split()
    clips = []
    chunk_size = 4
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    
    if not chunks:
        return []
        
    chunk_dur = duration / len(chunks)
    
    for i, chunk in enumerate(chunks):
        txt = TextClip(text=chunk, font="Liberation-Sans", font_size=55, color='white', 
                       stroke_color='black', stroke_width=2.5).with_position(('center', target_h - 220)).with_start(i * chunk_dur).with_duration(chunk_dur)
        clips.append(txt)
        
    return clips

def process_photos_to_preview(before_path, after_path, script, output_dir):
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
    
    # Mix audio
    final_audio = mix_background_music(None, audio_dur)
    layers = [video]
    
    # Overlay Labels
    try:
        txt_before = TextClip(text="BEFORE", font="Liberation-Sans", font_size=90, color='white', stroke_color='black', stroke_width=2).with_position(('center', 150)).with_duration(half_dur)
        txt_after = TextClip(text="AFTER", font="Liberation-Sans", font_size=90, color='white', stroke_color='black', stroke_width=2).with_position(('center', 150)).with_start(half_dur).with_duration(half_dur)
        layers.extend([txt_before, txt_after])
    except Exception as e:
        pass

    # Subtitles
    try:
        sub_clips = create_subtitles(script, audio_dur, target_w, target_h)
        layers.extend(sub_clips)
    except Exception as e:
        pass

    # Watermark
    try:
        watermark = TextClip(text="@DentalFlow", font="Liberation-Sans", font_size=35, color='white')
        if hasattr(watermark, 'with_opacity'):
            watermark = watermark.with_opacity(0.6)
        watermark = watermark.with_position(('right', 'bottom')).with_duration(audio_dur)
        layers.append(watermark)
    except Exception as e:
        pass

    final_video = CompositeVideoClip(layers)
    if final_audio:
        final_video = final_video.with_audio(final_audio)
    final_video = final_video.with_duration(audio_dur)
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"video_photos_preview_{uuid.uuid4().hex[:8]}.mp4")
    
    # Render with limited threads to optimize memory usage (4GB limit)
    temp_audio = os.path.join(os.getcwd(), "generations", "04_temp", f"temp_aud_{uuid.uuid4().hex[:8]}.m4a")
    final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, threads=2)
    return out_path

def process_video_to_preview(video_path, script, output_dir):
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
        
    final_audio = mix_background_music(None, audio_dur)
    layers = [vid_clip]
    
    try:
        sub_clips = create_subtitles(script, audio_dur, target_w, target_h)
        layers.extend(sub_clips)
    except Exception as e:
        pass
        
    # Watermark
    try:
        watermark = TextClip(text="@DentalFlow", font="Liberation-Sans", font_size=35, color='white')
        if hasattr(watermark, 'with_opacity'):
            watermark = watermark.with_opacity(0.6)
        watermark = watermark.with_position(('right', 'bottom')).with_duration(audio_dur)
        layers.append(watermark)
    except Exception as e:
        pass
        
    final_video = CompositeVideoClip(layers)
    if final_audio:
        final_video = final_video.with_audio(final_audio)
    final_video = final_video.with_duration(audio_dur)
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"video_vid_preview_{uuid.uuid4().hex[:8]}.mp4")
    
    # Render with limited threads to optimize memory usage (4GB limit)
    temp_audio = os.path.join(os.getcwd(), "generations", "04_temp", f"temp_aud_{uuid.uuid4().hex[:8]}.m4a")
    final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile=temp_audio, remove_temp=True, threads=2)
    return out_path

def finalize_video_with_voice(preview_path, audio_path, output_dir):
    vid_clip = VideoFileClip(preview_path)
    voice_clip = AudioFileClip(audio_path)
    
    # 1. Audio Trimming to avoid "Accessing time t" at the very end
    safe_audio_dur = voice_clip.duration - 0.1 if voice_clip.duration > 0.1 else voice_clip.duration
    voice_clip = voice_clip.with_duration(safe_audio_dur).with_end(safe_audio_dur)
    
    # 2. Strict Sync
    final_duration = min(vid_clip.duration, voice_clip.duration)
    
    vid_clip = vid_clip.with_duration(final_duration)
    voice_clip = voice_clip.with_duration(final_duration)
    
    # 3. Mix original audio (bg_music) + voice
    if vid_clip.audio:
        bg_audio = vid_clip.audio.with_duration(final_duration)
        final_audio = CompositeAudioClip([bg_audio, voice_clip]).with_duration(final_duration)
    else:
        final_audio = voice_clip
        
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
