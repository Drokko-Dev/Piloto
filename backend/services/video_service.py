from moviepy import VideoFileClip, ImageClip, TextClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips
from moviepy import vfx
import os
import uuid

def add_ken_burns(clip, duration, zoom_factor=0.05):
    """Simple Ken Burns effect (zoom in slowly)."""
    # Requires an active resize function over time `t`
    def resize_func(t):
        return 1 + zoom_factor * (t / duration)
    return clip.resized(resize_func)

def process_photos_to_video(before_path, after_path, audio_path, output_dir):
    audio_clip = AudioFileClip(audio_path)
    audio_dur = audio_clip.duration
    half_dur = audio_dur / 2
    
    # Common TikTok / Reel dimensions
    target_w, target_h = 1080, 1920
    
    # 1. Base Images Cropped to Vertical Space
    clip_before = ImageClip(before_path).resized(height=target_h).cropped(x_center=target_h/2, width=target_w)
    clip_after = ImageClip(after_path).resized(height=target_h).cropped(x_center=target_h/2, width=target_w)

    
    # 2. Add Animations
    # Extra time for crossfade overlap
    clip_before = add_ken_burns(clip_before, half_dur + 0.5).with_duration(half_dur + 0.5)
    clip_after = add_ken_burns(clip_after, half_dur + 0.5).with_duration(half_dur + 0.5)
    
    # Transition
    clip_after = clip_after.with_effects([vfx.CrossFadeIn(0.5)])
    
    video = concatenate_videoclips([clip_before.with_position("center"), clip_after.with_position("center")], padding=-0.5, method="compose")
    
    # Overlay Labels
    try:
        txt_before = TextClip(text="BEFORE", font="Arial", font_size=90, color='white', stroke_color='black', stroke_width=2).with_position(('center', 150)).with_duration(half_dur)
        txt_after = TextClip(text="AFTER", font="Arial", font_size=90, color='white', stroke_color='black', stroke_width=2).with_position(('center', 150)).with_start(half_dur).with_duration(half_dur)
        final_video = CompositeVideoClip([video, txt_before, txt_after])
    except Exception as e:
        # Fallback if ImageMagick not available
        final_video = video

    final_video = final_video.with_audio(audio_clip).with_duration(audio_dur)
    
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"video_photos_{uuid.uuid4().hex[:8]}.mp4")
    
    final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")
    return out_path

def process_video_to_video(video_path, audio_path, output_dir):
    audio_clip = AudioFileClip(audio_path)
    audio_dur = audio_clip.duration
    
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
        vid_clip = vid_clip.subclip(0, audio_dur)
    else:
        vid_clip = vid_clip.with_effects([vfx.Loop(duration=audio_dur)])
        
    final_video = vid_clip.with_audio(audio_clip).with_duration(audio_dur)
    
    # Simple Subs Placeholder
    try:
        subs = TextClip(text="Auto-generated Subtitles...", font="Arial", font_size=50, color='white', stroke_color='black', stroke_width=2).with_position(('center', target_h - 200)).with_duration(audio_dur)
        final_video = CompositeVideoClip([final_video, subs])
    except:
        pass
        
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"video_vid_{uuid.uuid4().hex[:8]}.mp4")
    
    final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")
    return out_path
