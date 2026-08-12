#!/usr/bin/env python3
"""
Cinematic Video Generator for AutoTube
Uses Kling API for AI image-to-video, FFmpeg for assembly, transitions, and ASS subtitle burn-in.
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from ai_generator import load_style_config, load_image_model_config, generate_slideshow_images

# --- Config paths ---
_BASE_DIR = Path(__file__).parent

def _find_config_file(filename: str) -> Path:
    candidates = [
        _BASE_DIR / filename,
        Path.cwd() / filename,
        _BASE_DIR.parent / filename,
        _BASE_DIR / "data" / filename,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return _BASE_DIR / filename

CAPTION_STYLES_PATH = _find_config_file("caption_styles.json")

# --- Kling API Client ---
class KlingClient:
    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or os.getenv("KLING_API_KEY")
        self.base_url = (base_url or os.getenv("KLING_API_BASE", "https://api-singapore.klingai.com")).rstrip("/")
        
        if not self.api_key:
            raise ValueError("KLING_API_KEY environment variable is not set.")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_video_from_image(self, image_url, prompt, model="kling-v1.6", duration=5, resolution="720p"):
        """Start a video generation task."""
        url = f"{self.base_url}/v1/videos/image2video"
        
        payload = {
            "model": model,
            "image_url": image_url,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "mode": "standard" # standard vs professional
        }
        
        print(f"🎬 [Kling] Starting task: {prompt[:30]}... ({resolution}, {duration}s)")
        
        response = requests.post(url, json=payload, headers=self.headers, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ [Kling API Error]: {response.status_code} - {response.text}")
            response.raise_for_status()
            
        data = response.json()
        task_id = data.get("data", {}).get("task_id")
        if not task_id:
            raise ValueError(f"Failed to get task_id from Kling API response: {data}")
            
        return task_id

    def get_task_status(self, task_id):
        """Check status of a task."""
        url = f"{self.base_url}/v1/videos/image2video/{task_id}"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def wait_for_task(self, task_id, timeout_sec=600, poll_interval=15):
        """Poll task until completion or timeout."""
        start_time = time.time()
        print(f"⏳ [Kling] Polling task {task_id}...")
        
        while time.time() - start_time < timeout_sec:
            try:
                res = self.get_task_status(task_id)
                status = res.get("data", {}).get("status", "").lower()
                
                if status == "succeed" or status == "success" or status == "succeeded":
                    video_url = res.get("data", {}).get("task_result", {}).get("videos", [{}])[0].get("url")
                    if not video_url:
                        video_url = res.get("data", {}).get("video_url")
                        
                    if video_url:
                        print(f"✅ [Kling] Task {task_id} completed successfully.")
                        return video_url
                    else:
                        raise ValueError(f"Task succeeded but no video URL found in response: {res}")
                        
                elif status == "failed" or status == "fail":
                    error_msg = res.get("data", {}).get("task_status_msg", "Unknown error")
                    raise RuntimeError(f"Kling task {task_id} failed: {error_msg}")
                    
                print(f"   ... status: {status} (elapsed: {int(time.time() - start_time)}s)")
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ [Kling] Network error while polling task {task_id}: {e}")
                
            time.sleep(poll_interval)
            
        raise TimeoutError(f"Kling task {task_id} timed out after {timeout_sec}s")


# --- Subtitle Generation ---
def generate_ass_subtitles(srt_content: str, ass_path: str, style_id: str = "default"):
    """
    Convert SRT content to ASS subtitle format with styling.
    """
    
    # Load styles
    styles = {}
    if CAPTION_STYLES_PATH.is_file():
        try:
            with open(CAPTION_STYLES_PATH, 'r', encoding='utf-8') as f:
                styles = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to load caption styles: {e}")
            
    style_config = styles.get(style_id, styles.get("default", {
        "font_name": "Arial",
        "font_size": 24,
        "primary_color": "&H0000FFFF", # BGR (Yellow)
        "outline_color": "&H00000000", # Black
        "outline_width": 2,
        "shadow_width": 1,
        "alignment": 2, # Bottom center
        "margin_v": 60
    }))
    
    # Parse SRT blocks
    blocks = srt_content.strip().split("\n\n")
    events = []
    
    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3:
            time_line = lines[1]
            text = "\\N".join(lines[2:])
            
            try:
                start_str, end_str = time_line.split(" --> ")
                start_ass = start_str.replace(",", ".")[:-1].lstrip("0:") or "0"
                if start_str.startswith("00:"): start_ass = start_str[1:].replace(",", ".")[:-1]
                
                end_ass = end_str.replace(",", ".")[:-1].lstrip("0:") or "0"
                if end_str.startswith("00:"): end_ass = end_str[1:].replace(",", ".")[:-1]
                
                events.append(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{text}")
            except Exception as e:
                print(f"Skipping malformed SRT block: {e}")
                continue

    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style_config.get('font_name', 'Arial')},{style_config.get('font_size', 48)},{style_config.get('primary_color', '&H0000FFFF')},&H000000FF,{style_config.get('outline_color', '&H00000000')},&H00000000,-1,0,0,0,100,100,0,0,1,{style_config.get('outline_width', 2)},{style_config.get('shadow_width', 1)},{style_config.get('alignment', 2)},10,10,{style_config.get('margin_v', 60)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    ass_content = ass_header + "\n".join(events) + "\n"
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
        
    return ass_path


# --- FFmpeg Assembly ---
def assemble_with_ffmpeg(scene_videos, audio_path, ass_path, output_path, music_path=None):
    """
    Concatenate scene videos with crossfade, add audio, mix music, burn ASS subtitles.
    """
    if not scene_videos:
        raise ValueError("No scene videos provided for assembly.")
        
    print(f"🎬 Assembling {len(scene_videos)} scenes with FFmpeg...")
    
    filter_complex = []
    inputs = []
    
    # Add video inputs
    for i, vid in enumerate(scene_videos):
        inputs.extend(["-i", vid])
        filter_complex.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p,fps=30[v{i}];")
        
    # Audio inputs
    audio_idx = len(scene_videos)
    if audio_path:
        inputs.extend(["-i", audio_path])
    
    music_idx = -1
    if music_path:
        music_idx = len(scene_videos) + (1 if audio_path else 0)
        inputs.extend(["-i", music_path])
        
    # Crossfade logic
    if len(scene_videos) == 1:
        v_out = "[v0]"
    else:
        duration = 5.0 # Assuming 5s clips
        fade_dur = 0.5
        offset = duration - fade_dur
        
        filter_complex.append(f"[v0][v1]xfade=transition=fade:duration={fade_dur}:offset={offset}[xf0];")
        
        last_xf = "[xf0]"
        curr_offset = offset + duration - fade_dur
        
        for i in range(2, len(scene_videos)):
            filter_complex.append(f"{last_xf}[v{i}]xfade=transition=fade:duration={fade_dur}:offset={curr_offset}[xf{i-1}];")
            last_xf = f"[xf{i-1}]"
            curr_offset += (duration - fade_dur)
            
        v_out = last_xf
        
    # Burn subtitles
    if ass_path:
        safe_ass_path = ass_path.replace("\\", "\\\\").replace(":", "\\:")
        filter_complex.append(f"{v_out}ass='{safe_ass_path}'[v_final];")
    else:
        filter_complex.append(f"{v_out}copy[v_final];")
        
    # Audio mixing
    a_out = None
    if audio_path and music_path:
        filter_complex.append(f"[{music_idx}:a]volume=0.15[bgm];")
        filter_complex.append(f"[{audio_idx}:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a_final]")
        a_out = "[a_final]"
    elif audio_path:
        filter_complex.append(f"[{audio_idx}:a]anull[a_final]")
        a_out = "[a_final]"
    elif music_path:
        filter_complex.append(f"[{music_idx}:a]anull[a_final]")
        a_out = "[a_final]"

    cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", "".join(filter_complex)]
    
    if ass_path:
        cmd.extend(["-map", "[v_final]"])
    else:
        cmd.extend(["-map", v_out])
        
    if a_out:
        cmd.extend(["-map", a_out])
        
    cmd.extend([
        "-c:v", "libx264", 
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ])
    
    print(f"Executing FFmpeg:\n{' '.join(cmd)}")
    
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print(f"✅ FFmpeg assembly complete: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg failed:\n{e.stderr}")
        raise RuntimeError("FFmpeg video assembly failed.")


# --- Main Pipeline ---
def generate_cinematic_video(
    hook: str,
    content: str,
    cta: str,
    title: str,
    audio_path: str = None,
    output_path: str = "output.mp4",
    style_id: str = "default",
    image_model: str = "flux",
    kling_model: str = "kling-v1.6",
    caption_style: str = "modern_bold_yellow",
    music_genre: str = None
):
    print(f"🎬 Starting Cinematic Pipeline for: {title}")
    
    # 1. Generate Storyboard Prompts
    from ai_generator import create_image_prompts_from_script
    base_prompts = create_image_prompts_from_script(hook, content, cta, title)
    
    # 2. Generate Base Images
    print("🎨 Generating base images...")
    image_paths = generate_slideshow_images(base_prompts, title, use_zimage=False, style_id=style_id, image_model=image_model)
    
    if not image_paths:
        raise RuntimeError("Failed to generate base images.")
        
    # 3. Generate Videos with Kling API
    print(f"🚀 Submitting {len(image_paths)} tasks to Kling API...")
    kling = KlingClient()
    
    style = load_style_config(style_id)
    image_suffix = style.get("image_suffix", "cinematic")
    
    def process_scene(i, prompt, local_img_path):
        enhanced_prompt = f"{title}, {prompt}, {image_suffix}"
        from urllib.parse import quote
        public_img_url = f"https://image.pollinations.ai/prompt/{quote(enhanced_prompt)}?width=1080&height=1920&nologo=true"
        motion_prompt = f"Cinematic camera movement, slow pan, {prompt}"
        
        try:
            task_id = kling.generate_video_from_image(
                image_url=public_img_url,
                prompt=motion_prompt,
                model=kling_model,
                duration=5,
                resolution="720p"
            )
            
            video_url = kling.wait_for_task(task_id)
            
            vid_path = str(Path(local_img_path).with_suffix('.mp4'))
            resp = requests.get(video_url, stream=True)
            resp.raise_for_status()
            with open(vid_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return vid_path
            
        except Exception as e:
            print(f"❌ Failed to generate video for scene {i}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_scene, i, base_prompts[i], image_paths[i]): i for i in range(len(image_paths))}
        results = [None] * len(image_paths)
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as exc:
                print(f"Scene {idx} generated an exception: {exc}")

    valid_videos = [v for v in results if v]
    
    if not valid_videos:
        print("⚠️ No valid cinematic videos generated. Falling back to slideshow.")
        from create_video import create_slideshow_video
        return create_slideshow_video(image_paths, [hook, content, cta], audio_path, output_path)

    # 4. Generate Subtitles
    print("📝 Generating subtitles...")
    srt_path = str(Path(output_path).with_suffix('.srt'))
    ass_path = str(Path(output_path).with_suffix('.ass'))
    
    dummy_srt = f"1\n00:00:00,000 --> 00:00:05,000\n{hook}\n\n2\n00:00:05,000 --> 00:00:15,000\n{content}\n\n3\n00:00:15,000 --> 00:00:20,000\n{cta}"
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(dummy_srt)
        
    generate_ass_subtitles(dummy_srt, ass_path, caption_style)
    
    # 5. Assemble Video
    music_path = None
    if music_genre:
        music_dir = _BASE_DIR / "assets" / "music"
        potential_music = list(music_dir.glob(f"{music_genre}*.mp3"))
        if potential_music:
            music_path = str(potential_music[0])
            
    final_path = assemble_with_ffmpeg(valid_videos, audio_path, ass_path, output_path, music_path)
    
    return final_path

if __name__ == "__main__":
    print("Cinematic generator module loaded.")
