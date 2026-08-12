#!/usr/bin/env python3
"""
Storyboard Generator for AutoTube Cinematic Pipeline
Enhances basic script sections into detailed cinematic scenes with camera motion prompts.
"""

import random

def get_random_camera_motion():
    motions = [
        "slow pan left",
        "slow pan right",
        "slow zoom in",
        "slow zoom out",
        "dolly in",
        "dolly out",
        "tracking shot",
        "orbit around subject",
        "subtle push in",
        "aerial descent"
    ]
    return random.choice(motions)

def get_mood_for_section(section_type):
    if section_type == "hook":
        return "intriguing, dramatic, attention-grabbing"
    elif section_type == "cta":
        return "inspiring, energetic, uplifting"
    else:
        return "informative, cinematic, engaging"

def generate_storyboard(hook: str, content: str, cta: str, title: str):
    """
    Generate a cinematic storyboard from script sections.
    """
    scenes = []
    
    # Hook
    scenes.append({
        "type": "hook",
        "text": hook,
        "visual_description": f"attention-grabbing visual for: {hook[:100]}",
        "motion_prompt": f"Cinematic {get_random_camera_motion()}, {get_mood_for_section('hook')}, highly detailed",
        "transition": "fade"
    })
    
    # Content parts
    content_parts = [p.strip() for p in content.split('\n') if p.strip()][:3]
    for i, part in enumerate(content_parts):
        scenes.append({
            "type": f"content_{i+1}",
            "text": part,
            "visual_description": f"illustrative visual for: {part[:100]}",
            "motion_prompt": f"Cinematic {get_random_camera_motion()}, {get_mood_for_section('content')}, highly detailed",
            "transition": "fade"
        })
        
    # CTA
    scenes.append({
        "type": "cta",
        "text": cta,
        "visual_description": f"engaging call-to-action visual with: {cta[:100]}",
        "motion_prompt": f"Cinematic {get_random_camera_motion()}, {get_mood_for_section('cta')}, highly detailed",
        "transition": "fade"
    })
    
    return {
        "title": title,
        "scenes": scenes
    }

if __name__ == "__main__":
    storyboard = generate_storyboard("Did you know AI can make videos?", "1. Kling is amazing.\n2. FFmpeg rules.", "Subscribe now!", "AI Video Test")
    import json
    print(json.dumps(storyboard, indent=2))
