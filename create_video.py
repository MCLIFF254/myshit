#!/usr/bin/env python3
"""
AutoTube - YouTube Shorts Slideshow Video Creator
Creates vertical 9:16 videos from AI-generated images with transitions
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# MoviePy 2.x imports
from moviepy import (
    TextClip, ColorClip, ImageClip, CompositeVideoClip, 
    AudioFileClip, concatenate_videoclips, CompositeAudioClip
)

# Import AI generator
from ai_generator import (
    generate_slideshow_images,
    create_image_prompts_from_script,
    load_style_config,
)

# Video specifications for YouTube Shorts
WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 30  # seconds
BG_COLOR = (15, 15, 25)  # Fallback background


def create_text_clip(text, fontsize=75, color='yellow', duration=5, position='center'):
    """Create a styled text clip with shadow, popping up 2-3 words at a time."""
    words = text.split()
    chunk_size = 3
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    
    if not chunks:
        return ColorClip(size=(WIDTH, HEIGHT), color=(0,0,0)).with_opacity(0).with_duration(duration)

    chunk_duration = duration / len(chunks)
    
    clips = []
    font_path = 'Arial' if sys.platform == 'win32' else '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'
    font_fallback = 'Arial' if sys.platform == 'win32' else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
    for i, chunk in enumerate(chunks):
        try:
            txt_clip = TextClip(
                text=chunk,
                font_size=fontsize,
                color=color,
                font=font_path,
                stroke_color='black',
                stroke_width=6,
                text_align='center',
                size=(WIDTH - 100, None)
            )
        except Exception as e:
            print(f"⚠️ Text clip error: {e}")
            try:
                txt_clip = TextClip(text=chunk, font_size=fontsize, color=color, font=font_fallback)
            except Exception as e2:
                txt_clip = TextClip(text=chunk, font_size=fontsize, color=color)
            
        txt_clip = txt_clip.with_position(position)
        txt_clip = txt_clip.with_start(i * chunk_duration).with_duration(chunk_duration)
        clips.append(txt_clip)
        
    return CompositeVideoClip(clips, size=(WIDTH, HEIGHT)).with_duration(duration)


def create_image_scene(image_path, text, duration=6, zoom=True):
    """
    Create a scene from an image with text overlay and zoom effect
    
    Args:
        image_path: Path to image file
        text: Text to overlay
        duration: Scene duration in seconds
        zoom: Apply Ken Burns zoom effect
        
    Returns:
        CompositeVideoClip
    """
    clips = []
    
    try:
        # Load and prepare image
        img = ImageClip(image_path).with_duration(duration)
        
        # Resize to fit screen
        img = img.resized(height=HEIGHT)
        if img.w < WIDTH:
            img = img.resized(width=WIDTH)
        
        # Center crop if too wide
        if img.w > WIDTH:
            x_center = img.w / 2
            img = img.cropped(x_center=x_center, width=WIDTH)
        
        # Apply zoom effect (Ken Burns)
        if zoom:
            img = img.resized(lambda t: 1 + 0.08 * (t / duration))  # 1.0x to 1.08x
        
        clips.append(img)
        
        # Dark overlay for text readability
        overlay = ColorClip(size=(WIDTH, HEIGHT), color=(0, 0, 0))
        overlay = overlay.with_opacity(0.15).with_duration(duration)
        clips.append(overlay)
        
    except Exception as e:
        print(f"⚠️ Image load error: {e}, using solid background")
        bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR).with_duration(duration)
        clips.append(bg)
    
    # Add text
    if text:
        text_clip = create_text_clip(
            text,
            fontsize=75,
            color='yellow',
            duration=duration,
            position='center'
        )
        clips.append(text_clip)
    
    return CompositeVideoClip(clips, size=(WIDTH, HEIGHT))


def create_slideshow_video(
    images: list,
    texts: list,
    audio_path: str = None,
    output_path: str = "output.mp4",
    crossfade_duration: float = 0.5
):
    """
    Create slideshow video from images with crossfade transitions
    
    Args:
        images: List of image file paths
        texts: List of text overlays for each image
        audio_path: Optional audio file path
        output_path: Output video file path
        crossfade_duration: Crossfade transition duration
        
    Returns:
        Path to created video
    """
    print(f"🎬 Creating slideshow video with {len(images)} scenes")
    
    # Calculate duration per scene
    num_scenes = len(images)
    total_duration = 30  # Target 30 seconds
    
    # Check audio duration to sync
    if audio_path and os.path.exists(audio_path):
        try:
            temp_audio = AudioFileClip(audio_path)
            total_duration = temp_audio.duration
            temp_audio.close()
        except Exception as e:
            print(f"   Audio duration error: {e}")
            
    scene_duration = (total_duration + (num_scenes - 1) * crossfade_duration) / num_scenes
    
    # Create scenes
    scenes = []
    for i, (img_path, text) in enumerate(zip(images, texts)):
        print(f"   Scene {i + 1}/{num_scenes}: {os.path.basename(img_path)}")
        scene = create_image_scene(img_path, text, duration=scene_duration, zoom=True)
        scenes.append(scene)
    
    # Apply crossfade transitions
    print("   Applying transitions...")
    final_clips = [scenes[0]]
    
    for i in range(1, len(scenes)):
        # Simple approach: just concatenate with overlap
        curr_scene = scenes[i]
        
        # Set start time to create overlap
        curr_scene = curr_scene.with_start(
            final_clips[-1].end - crossfade_duration
        )
        
        final_clips.append(curr_scene)
    
    # Composite final video
    print("   Compositing...")
    video = CompositeVideoClip(final_clips, size=(WIDTH, HEIGHT))
    
    # Trim to exact duration
    if video.duration > total_duration:
        video = video.subclipped(0, total_duration)
    
    # Add audio
    if audio_path and os.path.exists(audio_path):
        print(f"   Adding audio: {audio_path}")
        try:
            audio = AudioFileClip(audio_path)
            if audio.duration > video.duration:
                audio = audio.subclipped(0, video.duration)
            elif audio.duration < video.duration:
                # Loop audio if too short
                audio = CompositeAudioClip([audio] * int(video.duration / audio.duration + 1))
                audio = audio.subclipped(0, video.duration)
            video = video.with_audio(audio)
        except Exception as e:
            print(f"   Audio error: {e}")
    
    # Render
    print(f"   Rendering: {output_path}")
    video.write_videofile(
        output_path,
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        threads=4,
        preset='medium',
        logger=None
    )
    
    video.close()
    print(f"✅ Video created: {output_path}")
    return output_path


def create_youtube_short(
    hook: str,
    content: str,
    cta: str,
    title: str,
    audio_path: str = None,
    output_path: str = "output.mp4",
    use_ai_images: bool = True,
    style_id: str = "default",
    image_model: str = "flux",
):
    """
    Create YouTube Short with AI image slideshow.

    Args:
        hook:        Hook text (0-6s)
        content:     Content text, newline-separated points (6-24s)
        cta:         Call to action text (24-30s)
        title:       Video title
        audio_path:  Optional audio file
        output_path: Output video path
        use_ai_images: Generate AI images (vs solid backgrounds)
        style_id:    Style key from style_prompts.json (e.g. 'anime', 'cyberpunk')
        image_model: Image model id from models_config.json (e.g. 'flux', 'seedream5-pro')

    Returns:
        Path to created video
    """
    print(f"🎬 Creating YouTube Short: {title}")
    
    # Prepare script sections and texts
    content_parts = [p.strip() for p in content.split('\n') if p.strip()][:3]
    
    texts = [
        hook,
        *content_parts,
        cta
    ]
    
    # Generate or use placeholder images
    if use_ai_images:
        # Load style so we can log what's being used
        style = load_style_config(style_id)
        print(f"🎨 Generating AI images | style='{style_id}' ({style.get('label','')}) | model='{image_model}'")
        prompts = create_image_prompts_from_script(hook, content, cta, title)
        images = generate_slideshow_images(
            prompts,
            title,
            use_zimage=False,
            style_id=style_id,
            image_model=image_model,
        )

        if not images or len(images) < len(texts):
            print("⚠️ Not enough images generated, using placeholders")
            use_ai_images = False
    
    if not use_ai_images:
        # Create placeholder colored backgrounds
        print("📦 Using placeholder backgrounds...")
        images = []
        colors = [(15, 15, 25), (25, 15, 35), (15, 25, 35), (35, 25, 15), (25, 35, 15)]
        for i in range(len(texts)):
            # Create temp colored image
            from PIL import Image
            img = Image.new('RGB', (WIDTH, HEIGHT), colors[i % len(colors)])
            videos_dir = Path(__file__).parent / "videos" if not (sys.platform != 'win32' and Path("/videos").exists()) else Path("/videos")
            videos_dir.mkdir(parents=True, exist_ok=True)
            img_path = str(videos_dir / f"temp_bg_{i}.jpg")
            img.save(img_path)
            images.append(img_path)
    
    # Create slideshow
    result = create_slideshow_video(images, texts, audio_path, output_path)
    
    return result


def main():
    """Main function"""
    test_data = {
        "hook": "Did you know AI can create stunning videos?",
        "content": "1. AI generates beautiful images\n2. MoviePy adds smooth transitions\n3. Combines with professional voiceover\n4. Renders in minutes, not hours",
        "cta": "Follow for more AI automation!\n#shorts #ai #automation",
        "title": "AI Video Creation Made Easy"
    }
    
    # Check for JSON input
    if len(sys.argv) > 1:
        try:
            test_data = json.loads(sys.argv[1])
        except:
            test_data["hook"] = sys.argv[1]
    
    # Paths
    output_dir = Path(__file__).parent / "videos" if not (sys.platform != 'win32' and Path("/videos").exists()) else Path("/videos")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = str(output_dir / f"short_{timestamp}.mp4")
    audio_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Create video
    result = create_youtube_short(
        hook=test_data.get("hook", "Amazing fact!"),
        content=test_data.get("content", "Great content here."),
        cta=test_data.get("cta", "Follow for more!"),
        title=test_data.get("title", "Awesome Video"),
        audio_path=audio_path,
        output_path=output_path,
        use_ai_images=True,
        style_id=test_data.get("style", "default"),
        image_model=test_data.get("imageModel", "flux"),
    )
    
    print(f"\n📁 Output: {result}")
    return result


if __name__ == "__main__":
    main()