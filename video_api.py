#!/usr/bin/env python3
"""
AutoTube Video Generation API Server
Simple Flask server for n8n to call for video generation
SECURED VERSION - No debug info, input validation, rate limiting
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from functools import wraps
import os
import json
import sys
import time
import re
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Add current directory and scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
if '/scripts' not in sys.path and os.path.exists('/scripts'):
    sys.path.insert(0, '/scripts')

from create_video import create_youtube_short
from ai_generator import list_available_styles, list_available_image_models, load_style_config, load_image_model_config
from cinematic_generator import generate_cinematic_video

app = Flask(__name__, template_folder='templates')

@app.after_request
def add_cors_headers(response):
    """Enable CORS headers for cross-origin frontend requests"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

# Rate limiting storage
rate_limit_store = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 10  # max requests per window

def rate_limit(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time.time()
        
        if client_ip not in rate_limit_store:
            rate_limit_store[client_ip] = []
        
        # Clean old entries
        rate_limit_store[client_ip] = [
            t for t in rate_limit_store[client_ip] 
            if current_time - t < RATE_LIMIT_WINDOW
        ]
        
        if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return jsonify({
                "success": False,
                "error": "Rate limit exceeded. Try again later."
            }), 429
        
        rate_limit_store[client_ip].append(current_time)
        return f(*args, **kwargs)
    return decorated_function

def validate_path(path, allowed_base_dirs):
    """Validate file path to prevent path traversal attacks"""
    if not path:
        return None
    
    # Normalize path
    path = os.path.normpath(path)
    
    # Check for path traversal attempts
    if '..' in path or path.startswith('/'):
        return None
    
    # Ensure path is within allowed directories
    for base_dir in allowed_base_dirs:
        if path.startswith(base_dir) or path.startswith(os.path.basename(base_dir)):
            return path
    
    return None

@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Serve web dashboard UI"""
    return render_template('dashboard.html')

@app.route('/videos/<path:filename>', methods=['GET'])
def serve_video(filename):
    """Serve generated video files"""
    video_dir = '/videos'
    if not os.path.exists(os.path.join(video_dir, filename)):
        # Fallback to local ./videos if running outside container
        video_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'videos')
    return send_from_directory(video_dir, filename)

@app.route('/health', methods=['GET', 'OPTIONS'])
@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health():
    """Health check endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    return jsonify({"status": "healthy", "service": "autotube-video-api"})

@app.route('/generate-cinematic', methods=['POST', 'OPTIONS'])
@app.route('/api/generate-cinematic', methods=['POST', 'OPTIONS'])
@rate_limit
def generate_cinematic():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        def sanitize_string(value, max_length=500, default=''):
            if not value or not isinstance(value, str):
                return default
            return re.sub(r'[<>\"\'\\]', '', value)[:max_length]
            
        hook = sanitize_string(data.get('hook', 'Did you know this?'), 200, 'Did you know this?')
        content = sanitize_string(data.get('content', 'Amazing content here.'), 1000, 'Amazing content here.')
        cta = sanitize_string(data.get('cta', 'Follow for more!'), 200, 'Follow for more!')
        title = sanitize_string(data.get('title', 'Awesome Video'), 100, 'Awesome Video')
        
        audio_path = data.get('audioPath')
        output_path = data.get('outputPath')
        style = sanitize_string(data.get('style', 'default'))
        image_model = sanitize_string(data.get('imageModel', 'flux'))
        video_provider = sanitize_string(data.get('videoProvider', 'kling'))
        kling_model = 'kling-v1.6-turbo' if video_provider == 'kling_turbo' else 'kling-v1.6'
        caption_style = sanitize_string(data.get('captionStyle', 'modern_bold_yellow'))
        music_genre = sanitize_string(data.get('musicGenre', ''))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_path:
            output_path = f'/videos/cinematic_{timestamp}.mp4'
            
        Path('/videos').mkdir(exist_ok=True)
            
        result_path = generate_cinematic_video(
            hook=hook,
            content=content,
            cta=cta,
            title=title,
            audio_path=audio_path,
            output_path=output_path,
            style_id=style,
            image_model=image_model,
            kling_model=kling_model,
            caption_style=caption_style,
            music_genre=music_genre
        )
        
        if os.path.exists(result_path):
            return jsonify({
                "success": True,
                "videoPath": result_path,
                "fileSize": os.path.getsize(result_path),
                "message": "Cinematic video created successfully"
            })
        else:
            return jsonify({"success": False, "error": "Video file was not created"}), 500
            
    except Exception as e:
        app.logger.error(f"Cinematic generation error: {str(e)}")
        return jsonify({"success": False, "error": "Internal error: " + str(e)}), 500

@app.route('/video-providers', methods=['GET', 'OPTIONS'])
def video_providers():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    return jsonify({
        "success": True,
        "providers": [
            {"id": "kling", "label": "Kling 1.6 (Standard)"},
            {"id": "kling_turbo", "label": "Kling 1.6 Turbo (Fast)"},
            {"id": "slideshow", "label": "Static Slideshow (Fallback)"}
        ]
    })

@app.route('/caption-styles', methods=['GET', 'OPTIONS'])
def caption_styles():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    return jsonify({
        "success": True,
        "styles": [
            {"id": "modern_bold_yellow", "label": "Modern Bold Yellow"},
            {"id": "minimal_white", "label": "Minimal White"},
            {"id": "zack_films_style", "label": "Cinematic Drop Shadow"}
        ]
    })

@app.route('/generate', methods=['POST', 'OPTIONS'])
@app.route('/api/generate', methods=['POST', 'OPTIONS'])
@app.route('/api/create-video', methods=['POST', 'OPTIONS'])
@rate_limit
def generate_video():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    """
    Generate a YouTube Short video
    
    Expected JSON body:
    {
        "hook":        "...",
        "content":     "...",
        "cta":         "...",
        "title":       "...",
        "audioPath":   "/videos/audio_xxx.wav"  (optional),
        "outputPath":  "/videos/short_xxx.mp4"  (optional),
        "useAiImages": true                      (optional, default: true),
        "style":       "anime"                   (optional, default: "default"),
        "imageModel":  "seedream5-pro"           (optional, default: "flux")
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Input validation - sanitize strings
        def sanitize_string(value, max_length=500, default=''):
            if not value or not isinstance(value, str):
                return default
            # Remove potentially dangerous characters
            cleaned = re.sub(r'[<>\"\'\\]', '', value)
            return cleaned[:max_length]
        
        hook = sanitize_string(data.get('hook', 'Did you know this?'), max_length=200, default='Did you know this?')
        content = sanitize_string(data.get('content', 'Amazing content here.'), max_length=1000, default='Amazing content here.')
        cta = sanitize_string(data.get('cta', 'Follow for more!'), max_length=200, default='Follow for more!')
        title = sanitize_string(data.get('title', 'Awesome Video'), max_length=100, default='Awesome Video')

        audio_path = data.get('audioPath', data.get('audio_path'))
        use_ai_images = bool(data.get('useAiImages', data.get('use_ai_images', True)))

        video_mode = data.get('videoMode', 'slideshow')
        if video_mode == 'cinematic':
            # Reroute to cinematic pipeline
            return generate_cinematic()

        # ── Style validation (whitelist against style_prompts.json) ──────────
        requested_style = sanitize_string(data.get('style', 'default'), max_length=50, default='default')
        available_styles = {s['id'] for s in list_available_styles()}
        if requested_style and requested_style in available_styles:
            style_id = requested_style
        else:
            if requested_style and requested_style != 'default':
                app.logger.warning(f"Unknown style '{requested_style}', falling back to 'default'")
            style_id = 'default'

        # ── Image model validation (whitelist against models_config.json) ────
        requested_model = sanitize_string(data.get('imageModel', data.get('image_model', 'flux')), max_length=50, default='flux')
        available_models = {m['id'] for m in list_available_image_models()}
        if requested_model and requested_model in available_models:
            image_model = requested_model
        else:
            if requested_model and requested_model != 'flux':
                app.logger.warning(f"Unknown image model '{requested_model}', falling back to 'flux'")
            image_model = 'flux'
        
        # Validate audio path if provided
        allowed_dirs = ['/videos', '/scripts']
        if audio_path:
            audio_path = validate_path(audio_path, allowed_dirs)
            if audio_path and not os.path.exists(audio_path):
                return jsonify({
                    "success": False,
                    "error": "Audio file not found"
                }), 404
        
        # Generate output path if not provided
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = data.get('outputPath', data.get('output_path', f'/videos/short_{timestamp}.mp4'))
        
        # Validate output path
        output_path = validate_path(output_path, allowed_dirs)
        if not output_path:
            output_path = f'/videos/short_{timestamp}.mp4'
        
        # Ensure output directory exists
        Path('/videos').mkdir(exist_ok=True)
        
        # Create the video
        result_path = create_youtube_short(
            hook=hook,
            content=content,
            cta=cta,
            title=title,
            audio_path=audio_path,
            output_path=output_path,
            use_ai_images=use_ai_images,
            style_id=style_id,
            image_model=image_model,
        )
        
        # Check if video was created
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            style_info = load_style_config(style_id)
            return jsonify({
                "success": True,
                "videoPath": result_path,
                "fileSize": file_size,
                "style": style_id,
                "styleLabel": style_info.get("label", style_id),
                "imageModel": image_model,
                "message": "Video created successfully",
            })
        else:
            return jsonify({
                "success": False,
                "error": "Video file was not created"
            }), 500
            
    except Exception as e:
        # Log error internally but don't expose details
        app.logger.error(f"Video generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An internal error occurred during video generation"
        }), 500

@app.route('/info', methods=['GET', 'OPTIONS'])
@app.route('/api/info', methods=['GET', 'OPTIONS'])
@app.route('/api/config', methods=['GET', 'OPTIONS'])
def info():
    """Get server info"""
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    return jsonify({
        "service": "AutoTube Video Generation API",
        "version": "3.0.0-configurable",
        "features": ["AI Image Slideshows", "Crossfade Transitions", "Ken Burns Zoom",
                     "Dynamic Style Selection", "Dynamic Model Selection"],
        "endpoints": {
            "/health": "GET — Health check",
            "/generate": "POST — Generate video (accepts style + imageModel)",
            "/styles": "GET — List all available visual styles",
            "/models": "GET — List all available image models (ranked)",
            "/info": "GET — Server info",
        },
    })


@app.route('/styles', methods=['GET', 'OPTIONS'])
@app.route('/api/styles', methods=['GET', 'OPTIONS'])
@app.route('/api/config/style', methods=['GET', 'OPTIONS'])
def get_styles():
    """
    List all available visual styles from style_prompts.json.
    Returns styles sorted by category then label.
    """
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    try:
        styles = list_available_styles()
        styles_sorted = sorted(styles, key=lambda s: (s.get('category', ''), s.get('label', '')))
        return jsonify({
            "success": True,
            "count": len(styles_sorted),
            "styles": styles_sorted,
            "usage": "Pass \"style\": \"<id>\" in your /generate POST body",
        })
    except Exception as e:
        app.logger.error(f"Styles list error: {str(e)}")
        return jsonify({"success": False, "error": "Could not load styles"}), 500


@app.route('/models', methods=['GET', 'OPTIONS'])
@app.route('/api/models', methods=['GET', 'OPTIONS'])
def get_models():
    """
    List all available image models from models_config.json, ranked best-to-worst.
    """
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
    try:
        models = list_available_image_models()
        return jsonify({
            "success": True,
            "count": len(models),
            "models": models,
            "usage": "Pass \"imageModel\": \"<id>\" in your /generate POST body",
            "ranking_note": "Models listed in order: S > A > B > C tier",
        })
    except Exception as e:
        app.logger.error(f"Models list error: {str(e)}")
        return jsonify({"success": False, "error": "Could not load models"}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors without exposing information"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors without exposing information"""
    app.logger.error(f"Internal error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🎬 Starting AutoTube Video Generation API v3.0 (Configurable)")
    print("   Features: AI Slideshows, Transitions, Zoom, Dynamic Styles & Models")
    print("   Security: Rate limiting, Input validation, Whitelisted style/model params")
    print("   Endpoints: /generate  /styles  /models  /info  /health")
    print("   Listening on http://0.0.0.0:5001")
    # NEVER run with debug=True in production
    app.run(host='0.0.0.0', port=5001, debug=False)
