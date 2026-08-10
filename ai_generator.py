#!/usr/bin/env python3
"""
AI Media Generator for AutoTube
Generates multiple images for slideshow videos using various AI APIs.
Reads style from style_prompts.json and image model from models_config.json.
"""

import os
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# ── Config paths ──────────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).parent

def _find_config_file(filename: str) -> Path:
    """Find config file checking multiple candidate directories."""
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

STYLE_PROMPTS_PATH = _find_config_file("style_prompts.json")
MODELS_CONFIG_PATH = _find_config_file("models_config.json")

# ── Cached config (loaded once per process) ───────────────────────────────────
_style_cache: dict = {}
_models_cache: dict = {}

# ── Legacy fallback endpoints (if config files are missing) ───────────────────
POLLINATIONS_URL = (
    "https://image.pollinations.ai/prompt/{prompt}"
    "?width=1080&height=1920&model={model}&nologo=true"
)
Z_IMAGE_HF_URL = "https://api-inference.huggingface.co/models/Tongyi-Kongjian/Z-Image"


# ── Config Loaders ────────────────────────────────────────────────────────────

def load_style_config(style_id: str = "default") -> dict:
    """
    Load a style definition from style_prompts.json.

    Args:
        style_id: Key from style_prompts.json (e.g. 'anime', 'cyberpunk').
                  Falls back to 'default' if the key doesn't exist.

    Returns:
        Style dict with keys: label, image_suffix, script_system_prompt, negative.
    """
    global _style_cache

    if not _style_cache:
        target_path = _find_config_file("style_prompts.json")
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                _style_cache = json.load(f)
            print(f"✅ Loaded style_prompts.json from {target_path} ({len(_style_cache) - 1} styles)")
        except FileNotFoundError:
            print(f"⚠️  style_prompts.json not found at {target_path}. Using built-in default.")
            _style_cache = {}
        except json.JSONDecodeError as e:
            print(f"⚠️  style_prompts.json is malformed: {e}. Using built-in default.")
            _style_cache = {}

    # Skip the _meta key
    if style_id and style_id != "_meta" and style_id in _style_cache:
        style = _style_cache[style_id]
        print(f"🎨 Style loaded: {style.get('label', style_id)}")
        return style

    if style_id and style_id != "default":
        print(f"⚠️  Style '{style_id}' not found. Falling back to 'default'.")

    return _style_cache.get("default", {
        "label": "Cinematic (Built-in Default)",
        "image_suffix": (
            "cinematic, hyper-detailed, 8k, dramatic lighting, "
            "no text, storybook style, high quality, vertical 9:16 format"
        ),
        "script_system_prompt": (
            "You are a viral YouTube Shorts script writer. "
            "You create engaging, punchy 30-second scripts that hook viewers instantly."
        ),
        "negative": "blurry, low quality, distorted, watermark, text overlay, deformed",
    })


def load_image_model_config(model_id: str = "flux") -> dict:
    """
    Load an image model definition from models_config.json.

    Args:
        model_id: Model id string (e.g. 'flux', 'seedream5-pro', 'nanobanana-2').
                  Falls back to 'flux' if not found.

    Returns:
        Dict with at minimum: 'id', 'label', 'tier', '_endpoint' (resolved URL template).
    """
    global _models_cache

    if not _models_cache:
        target_path = _find_config_file("models_config.json")
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                _models_cache = json.load(f)
            print(f"✅ Loaded models_config.json from {target_path}")
        except FileNotFoundError:
            print(f"⚠️  models_config.json not found at {target_path}. Using flux default.")
            _models_cache = {}
        except json.JSONDecodeError as e:
            print(f"⚠️  models_config.json is malformed: {e}. Using built-in default.")
            _models_cache = {}

    # Search through all pollinations image model entries
    pollinations_section = (
        _models_cache
        .get("image_models", {})
        .get("pollinations", {})
    )
    endpoint_template = pollinations_section.get(
        "_endpoint",
        "https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1920&model={model}&nologo=true"
    )
    for model in pollinations_section.get("models", []):
        if model.get("id") == model_id:
            model["_endpoint"] = endpoint_template
            print(f"🤖 Image model: {model.get('label', model_id)} (tier {model.get('tier','?')})")
            return model

    # Fallback to flux
    if model_id != "flux":
        print(f"⚠️  Image model '{model_id}' not found in models_config. Falling back to 'flux'.")
    return {
        "id": "flux",
        "label": "FLUX (Default Fallback)",
        "tier": "S",
        "_endpoint": endpoint_template,
    }


def list_available_styles() -> list:
    """Return a list of available style ids and their labels."""
    load_style_config("default")  # Ensures cache is populated
    return [
        {"id": k, "label": v.get("label", k), "category": v.get("category", "general")}
        for k, v in _style_cache.items()
        if not k.startswith("_")
    ]


def list_available_image_models() -> list:
    """Return a list of available image model ids from models_config.json."""
    load_image_model_config("flux")  # Ensures cache is populated
    pollinations_models = (
        _models_cache
        .get("image_models", {})
        .get("pollinations", {})
        .get("models", [])
    )
    return [
        {
            "id": m.get("id"),
            "label": m.get("label"),
            "tier": m.get("tier"),
            "cost": m.get("cost"),
            "speed": m.get("speed"),
            "best_for": m.get("best_for", []),
        }
        for m in pollinations_models
    ]


# ── Image Generators ──────────────────────────────────────────────────────────

def generate_image_pollinations(
    prompt: str,
    output_path: str = None,
    index: int = 0,
    model: str = "flux",
    endpoint_template: str = None,
) -> str:
    """Generate an image using Pollinations.ai."""
    try:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            videos_dir = (
                Path(__file__).parent / "videos"
                if not (os.name != 'nt' and Path("/videos").exists())
                else Path("/videos")
            )
            videos_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(videos_dir / f"scene_{index}_{timestamp}.jpg")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        clean_prompt = prompt.replace('\n', ' ').strip()

        template = endpoint_template or POLLINATIONS_URL
        url = template.format(
            prompt=requests.utils.quote(clean_prompt),
            model=model,
        )

        print(f"🎨 Generating image {index + 1} [{model}]: {clean_prompt[:50]}...")

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"✅ Image {index + 1} saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Image {index + 1} generation failed: {e}")
        return None


def generate_image_zimage(
    prompt: str,
    output_path: str = None,
    index: int = 0,
    hf_token: str = None,
) -> str:
    """Generate image using Z-Image via HuggingFace (best quality, requires token)."""
    if not hf_token:
        hf_token = os.getenv('HUGGINGFACE_TOKEN')

    try:
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            videos_dir = (
                Path(__file__).parent / "videos"
                if not (os.name != 'nt' and Path("/videos").exists())
                else Path("/videos")
            )
            videos_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(videos_dir / f"scene_{index}_{timestamp}.jpg")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}

        print(f"🎨 Generating Z-Image {index + 1}: {prompt[:50]}...")

        response = requests.post(
            Z_IMAGE_HF_URL,
            headers=headers,
            json={"inputs": prompt},
            timeout=120,
        )

        # Handle model loading cold-start
        if response.status_code == 503:
            result = response.json()
            if 'estimated_time' in result:
                wait_time = result['estimated_time']
                print(f"⏳ Model loading, waiting {wait_time}s...")
                time.sleep(wait_time + 5)
                response = requests.post(
                    Z_IMAGE_HF_URL, headers=headers,
                    json={"inputs": prompt}, timeout=120,
                )

        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"✅ Z-Image {index + 1} saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Z-Image {index + 1} generation failed: {e}")
        return None


# ── Slideshow Generator ───────────────────────────────────────────────────────

def generate_slideshow_images(
    prompts: list,
    topic: str,
    use_zimage: bool = False,
    style_id: str = "default",
    image_model: str = "flux",
) -> list:
    """
    Generate multiple AI images for slideshow video.

    Args:
        prompts:     List of base text prompts for each scene.
        topic:       Overall video topic — prepended to each prompt.
        use_zimage:  Use Z-Image (HuggingFace) instead of Pollinations.
        style_id:    Key from style_prompts.json (e.g. 'anime', 'cyberpunk').
        image_model: Model id from models_config.json (e.g. 'flux', 'seedream5-pro').

    Returns:
        List of image file paths.
    """
    # Load the style config for its image suffix
    style = load_style_config(style_id)
    image_suffix = style.get(
        "image_suffix",
        "cinematic, hyper-detailed, 8k, dramatic lighting, no text, vertical 9:16 format",
    )

    # Load the model config for its endpoint template
    model_cfg = load_image_model_config(image_model)
    endpoint_template = model_cfg.get("_endpoint", POLLINATIONS_URL)
    resolved_model_id = model_cfg.get("id", "flux")

    print(f"\n🖼️  Generating {len(prompts)} images")
    print(f"   Style:  {style.get('label', style_id)}")
    print(f"   Model:  {model_cfg.get('label', resolved_model_id)} (tier {model_cfg.get('tier','?')})\n")

    images = []

    for i, prompt in enumerate(prompts):
        # Build enhanced prompt: topic + base prompt + style suffix
        enhanced_prompt = f"{topic}, {prompt}, {image_suffix}"

        if use_zimage:
            image_path = generate_image_zimage(enhanced_prompt, index=i)
        else:
            image_path = generate_image_pollinations(
                enhanced_prompt,
                index=i,
                model=resolved_model_id,
                endpoint_template=endpoint_template,
            )

        if image_path:
            images.append(image_path)
        else:
            print(f"⚠️ Using fallback for image {i + 1}")
            if images:
                images.append(images[-1])

        time.sleep(1)  # Avoid rate limiting

    return images


# ── Script Prompt Helper ──────────────────────────────────────────────────────

def create_image_prompts_from_script(
    hook: str, content: str, cta: str, topic: str
) -> list:
    """
    Generate base image prompts from script sections.
    These are enhanced with the style suffix inside generate_slideshow_images().

    Returns:
        List of base prompts for each scene.
    """
    prompts = []

    # Hook scene
    prompts.append(f"attention-grabbing visual for: {hook[:100]}")

    # Content scenes (up to 3)
    content_parts = [p.strip() for p in content.split('\n') if p.strip()][:3]
    for part in content_parts:
        prompts.append(f"illustrative visual for: {part[:100]}")

    # CTA scene
    prompts.append(f"engaging call-to-action visual with: {cta[:100]}")

    return prompts


# ── CLI Test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AutoTube AI Image Generator")
    parser.add_argument("--style", default="default", help="Style id from style_prompts.json")
    parser.add_argument("--model", default="flux", help="Image model id from models_config.json")
    parser.add_argument("--list-styles", action="store_true", help="List all available styles")
    parser.add_argument("--list-models", action="store_true", help="List all available image models")
    args = parser.parse_args()

    if args.list_styles:
        print("\n📋 Available Styles:")
        for s in list_available_styles():
            print(f"  [{s['category']:15}] {s['id']:20} → {s['label']}")
        sys.exit(0)

    if args.list_models:
        print("\n🤖 Available Image Models (ranked):")
        for m in list_available_image_models():
            print(f"  [tier {m['tier']}] [{m['cost']:8}] {m['id']:20} → {m['label']}")
        sys.exit(0)

    # Test generation
    test_topic = "AI Tools for 2025"
    test_prompts = [
        "futuristic AI interface dashboard",
        "ChatGPT productivity workspace",
        "AI art generation showcase",
        "subscribe and follow visual",
    ]

    print(f"Testing image generation | style={args.style} | model={args.model}\n")
    images = generate_slideshow_images(
        test_prompts,
        test_topic,
        use_zimage=False,
        style_id=args.style,
        image_model=args.model,
    )
    print(f"\n✅ Generated {len(images)} images:")
    for img in images:
        print(f"  - {img}")
