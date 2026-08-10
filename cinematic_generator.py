"""
AutoTube Cinematic Generator - Optimized for 1-2 Minute Videos
Cost-Efficient Hybrid Approach: 83% cost reduction
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Configuration
FONTS_DIR = Path("/fonts")
CAPTION_STYLES_FILE = Path("caption_styles.json")
OUTPUT_DIR = Path("/output")
TEMP_DIR = Path("/tmp/autotube")

# Ensure directories exist
for d in [FONTS_DIR, OUTPUT_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class CinematicGenerator:
    def __init__(self):
        self.caption_styles = self._load_caption_styles()
        self.default_settings = {
            "resolution": "1080x1920",
            "fps": 30,
            "crf": 18,
            "preset": "slow"
        }
    
    def _load_caption_styles(self) -> Dict:
        """Load caption styles from JSON file"""
        if CAPTION_STYLES_FILE.exists():
            with open(CAPTION_STYLES_FILE, 'r') as f:
                return json.load(f)
        return {"default_style": "bebas_neue_pro", "caption_styles": {}}
    
    def generate_hybrid_video(
        self,
        script: str,
        ai_clips: List[str],
        static_images: List[str],
        audio_file: str,
        output_filename: str,
        kling_mode: str = "standard",
        caption_style: str = "bebas_neue_pro",
        target_duration: int = 60
    ) -> str:
        """
        Generate a hybrid video using the cost-efficient approach
        
        Strategy:
        - 0:00-0:03: AI Clip 1 (Hook)
        - 0:03-0:15: Static image with Ken Burns
        - 0:15-0:18: AI Clip 2 (Key moment)
        - 0:18-0:45: Kinetic typography
        - 0:45-0:48: AI Clip 3 (Climax)
        - 0:48-1:00: Static + CTA
        
        Args:
            script: Video script text
            ai_clips: List of AI-generated video clip URLs/paths (max 3 for efficiency)
            static_images: List of static image paths
            audio_file: Path to TTS audio file
            kling_mode: 'standard' (cost-efficient) or 'professional' (premium)
            caption_style: Style from caption_styles.json
            target_duration: Target video duration in seconds
        
        Returns:
            Path to generated video
        """
        print(f"🎬 Starting hybrid video generation...")
        print(f"   Mode: {kling_mode} | Style: {caption_style} | Duration: {target_duration}s")
        
        # Validate inputs
        if len(ai_clips) > 3:
            print(f"⚠️ Warning: Using only first 3 AI clips for cost efficiency")
            ai_clips = ai_clips[:3]
        
        # Download/copy assets
        temp_assets = self._prepare_assets(ai_clips, static_images, audio_file)
        
        # Generate captions with style
        caption_file = self._generate_captions(script, caption_style, temp_assets['duration'])
        
        # Create Ken Burns effect for static images
        ken_burns_clips = self._create_ken_burns_effects(static_images, temp_assets['duration'])
        
        # Assemble video timeline
        timeline = self._build_timeline(ai_clips, ken_burns_clips, target_duration)
        
        # Render final video with two-pass encoding
        output_path = OUTPUT_DIR / output_filename
        self._render_final_video(timeline, caption_file, temp_assets['audio'], output_path)
        
        # Cleanup temp files
        self._cleanup(temp_assets)
        
        print(f"✅ Video generated successfully: {output_path}")
        print(f"💰 Cost: ~${0.04 * len(ai_clips):.2f} ({len(ai_clips)} AI clips @ $0.04 each)")
        
        return str(output_path)
    
    def _prepare_assets(self, ai_clips: List[str], static_images: List[str], audio_file: str) -> Dict:
        """Download and prepare all assets"""
        temp_assets = {
            'ai_clips': [],
            'static_images': [],
            'audio': audio_file,
            'duration': 0
        }
        
        # Get audio duration
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_file],
                capture_output=True, text=True
            )
            temp_assets['duration'] = float(result.stdout.strip())
        except Exception as e:
            print(f"⚠️ Could not get audio duration: {e}")
            temp_assets['duration'] = 60  # Default
        
        # Process AI clips
        for i, clip in enumerate(ai_clips):
            if clip.startswith('http'):
                # Download clip
                clip_path = TEMP_DIR / f"ai_clip_{i}.mp4"
                response = requests.get(clip)
                with open(clip_path, 'wb') as f:
                    f.write(response.content)
                temp_assets['ai_clips'].append(str(clip_path))
            else:
                temp_assets['ai_clips'].append(clip)
        
        # Process static images
        for i, img in enumerate(static_images):
            if img.startswith('http'):
                img_path = TEMP_DIR / f"static_{i}.jpg"
                response = requests.get(img)
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                temp_assets['static_images'].append(str(img_path))
            else:
                temp_assets['static_images'].append(img)
        
        return temp_assets
    
    def _generate_captions(self, script: str, style_name: str, duration: float) -> str:
        """Generate styled caption overlay video"""
        style_config = self.caption_styles['caption_styles'].get(style_name, {})
        
        # Parse script into segments
        segments = self._parse_script_to_segments(script, duration)
        
        # Create caption video
        caption_video = TEMP_DIR / "captions.mp4"
        
        # FFmpeg filter complex for captions
        filter_complex = []
        
        font_path = FONTS_DIR / style_config.get('font', 'BebasNeue-Regular.ttf')
        fontsize = style_config.get('fontsize', 70)
        color = style_config.get('color', 'white')
        stroke_color = style_config.get('stroke_color', 'black')
        stroke_width = style_config.get('stroke_width', 2)
        
        # Build drawtext filters
        for i, segment in enumerate(segments):
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text'].replace("'", "'\\''")
            
            filter_str = f"drawtext=fontfile='{font_path}':fontsize={fontsize}:fontcolor={color}"
            filter_str += f":borderw={stroke_width}:bordercolor={stroke_color}"
            filter_str += f":text='{text}'"
            filter_str += f":enable='between(t,{start_time},{end_time})'"
            filter_str += f":x=(w-text_w)/2:y=h-{style_config.get('margin_y', 150)}"
            
            filter_complex.append(filter_str)
        
        # Generate black background with captions
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', f'color=c=black:s=1080x1920:d={duration}',
            '-filter_complex', ';'.join(filter_complex),
            '-t', str(duration),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            str(caption_video)
        ]
        
        subprocess.run(cmd, check=True)
        return str(caption_video)
    
    def _parse_script_to_segments(self, script: str, total_duration: float) -> List[Dict]:
        """Split script into timed segments"""
        words = script.split()
        words_per_segment = max(3, len(words) // max(1, int(total_duration / 3)))
        
        segments = []
        segment_duration = total_duration / max(1, len(words) // words_per_segment)
        
        for i in range(0, len(words), words_per_segment):
            segment_words = words[i:i + words_per_segment]
            start = (i / words_per_segment) * segment_duration
            end = min(((i / words_per_segment) + 1) * segment_duration, total_duration)
            
            segments.append({
                'text': ' '.join(segment_words),
                'start': start,
                'end': end
            })
        
        return segments if segments else [{'text': script, 'start': 0, 'end': total_duration}]
    
    def _create_ken_burns_effects(self, images: List[str], total_duration: float) -> List[str]:
        """Create Ken Burns pan/zoom effects for static images"""
        ken_burns_clips = []
        
        # Calculate duration per image based on timeline strategy
        # Static images used in 0:03-0:15 (12s) and 0:48-1:00 (12s) = 24s total
        static_duration = min(24, total_duration * 0.4)
        duration_per_image = static_duration / max(1, len(images))
        
        for i, img_path in enumerate(images):
            output_clip = TEMP_DIR / f"kenburns_{i}.mp4"
            
            # Ken Burns effect: slow zoom and pan
            filter_complex = (
                f"zoompan=z='min(zoom+0.001,1.5)':d={int(duration_per_image * 30)}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
            )
            
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1', '-i', img_path,
                '-vf', filter_complex,
                '-t', str(duration_per_image),
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
                '-pix_fmt', 'yuv420p',
                str(output_clip)
            ]
            
            subprocess.run(cmd, check=True)
            ken_burns_clips.append(str(output_clip))
        
        return ken_burns_clips
    
    def _build_timeline(self, ai_clips: List[str], ken_burns_clips: List[str], target_duration: int) -> List[Dict]:
        """Build video timeline following hybrid strategy"""
        timeline = []
        
        # Strategy: 3 AI clips at key moments, rest is static/typography
        # 0:00-0:03: AI Clip 1 (Hook)
        # 0:03-0:15: Static (Ken Burns)
        # 0:15-0:18: AI Clip 2 (Key moment)
        # 0:18-0:45: Typography (handled in caption layer)
        # 0:45-0:48: AI Clip 3 (Climax)
        # 0:48-1:00: Static + CTA
        
        current_time = 0
        
        # Add AI clips at strategic positions
        ai_positions = [
            (0, 3),      # Hook
            (15, 18),    # Key moment
            (45, 48)     # Climax
        ]
        
        for i, (start, end) in enumerate(ai_positions):
            if i < len(ai_clips):
                # Add gap before this clip if needed
                if current_time < start:
                    timeline.append({
                        'type': 'gap',
                        'start': current_time,
                        'duration': start - current_time
                    })
                
                timeline.append({
                    'type': 'video',
                    'path': ai_clips[i],
                    'start': start,
                    'duration': end - start,
                    'trim': True
                })
                current_time = end
        
        # Fill remaining gaps with Ken Burns clips
        kb_index = 0
        for i in range(len(timeline) - 1):
            current_end = timeline[i]['start'] + timeline[i]['duration']
            next_start = timeline[i + 1]['start']
            
            if next_start > current_end and kb_index < len(ken_burns_clips):
                timeline.append({
                    'type': 'video',
                    'path': ken_burns_clips[kb_index % len(ken_burns_clips)],
                    'start': current_end,
                    'duration': next_start - current_end,
                    'trim': True
                })
                kb_index += 1
        
        # Sort timeline by start time
        timeline.sort(key=lambda x: x['start'])
        
        return timeline
    
    def _render_final_video(self, timeline: List[Dict], caption_file: str, audio_file: str, output_path: Path):
        """Render final video with two-pass encoding for optimal quality/size"""
        
        # Create concat file for timeline
        concat_file = TEMP_DIR / "concat.txt"
        with open(concat_file, 'w') as f:
            for segment in timeline:
                if segment['type'] == 'video':
                    f.write(f"file '{segment['path']}'\n")
                    if segment.get('trim'):
                        f.write(f"duration {segment['duration']}\n")
                elif segment['type'] == 'gap':
                    # Black screen for gaps
                    f.write(f"file '{TEMP_DIR}/black.mp4'\n")
                    f.write(f"duration {segment['duration']}\n")
        
        # Two-pass encoding
        pass1_log = TEMP_DIR / "ffmpeg_pass1.log"
        
        # Pass 1: Analysis
        cmd_pass1 = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0', '-i', str(concat_file),
            '-i', caption_file,
            '-i', audio_file,
            '-filter_complex', '[0:v][1:v]overlay=shortest=1[outv]',
            '-map', '[outv]', '-map', '2:a',
            '-c:v', 'libx264', '-preset', 'slow', '-crf', 18,
            '-pass', '1', '-passlogfile', str(pass1_log),
            '-c:a', 'aac', '-b:a', '192k',
            '-f', 'null', '/dev/null'
        ]
        
        # Pass 2: Encoding
        cmd_pass2 = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0', '-i', str(concat_file),
            '-i', caption_file,
            '-i', audio_file,
            '-filter_complex', '[0:v][1:v]overlay=shortest=1[outv]',
            '-map', '[outv]', '-map', '2:a',
            '-c:v', 'libx264', '-preset', 'slow', '-crf', 18,
            '-pass', '2', '-passlogfile', str(pass1_log),
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]
        
        print("🎥 Running two-pass encoding (Pass 1/2)...")
        subprocess.run(cmd_pass1, check=True)
        
        print("🎥 Running two-pass encoding (Pass 2/2)...")
        subprocess.run(cmd_pass2, check=True)
        
        # Delete pass log
        if pass1_log.exists():
            pass1_log.unlink()
    
    def _cleanup(self, temp_assets: Dict):
        """Clean up temporary files"""
        # Keep AI clips and static images for potential reuse
        # Only delete intermediate processing files
        for f in TEMP_DIR.glob("captions.mp4"):
            f.unlink()
        for f in TEMP_DIR.glob("kenburns_*.mp4"):
            f.unlink()
        for f in TEMP_DIR.glob("concat.txt"):
            f.unlink()


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoTube Cinematic Generator")
    parser.add_argument("--script", type=str, required=True, help="Video script")
    parser.add_argument("--ai-clips", nargs='+', help="AI video clip URLs/paths")
    parser.add_argument("--images", nargs='+', help="Static image URLs/paths")
    parser.add_argument("--audio", type=str, required=True, help="Audio file path")
    parser.add_argument("--output", type=str, default="output.mp4", help="Output filename")
    parser.add_argument("--kling-mode", choices=['standard', 'professional'], default='standard')
    parser.add_argument("--caption-style", type=str, default="bebas_neue_pro")
    parser.add_argument("--duration", type=int, default=60, help="Target duration in seconds")
    
    args = parser.parse_args()
    
    generator = CinematicGenerator()
    output_path = generator.generate_hybrid_video(
        script=args.script,
        ai_clips=args.ai_clips or [],
        static_images=args.images or [],
        audio_file=args.audio,
        output_filename=args.output,
        kling_mode=args.kling_mode,
        caption_style=args.caption_style,
        target_duration=args.duration
    )
    
    print(f"\n🎉 Success! Video saved to: {output_path}")
