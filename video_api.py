#!/usr/bin/env python3
"""
AutoTube Video Generation API Server
Simple Flask server for n8n to call for video generation
SECURED VERSION - No debug info, input validation, rate limiting
"""

from flask import Flask, request, jsonify
from functools import wraps
import os
import json
import sys
import time
import re
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, '/scripts')
from create_video import create_youtube_short

app = Flask(__name__)

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

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "autotube-video-api"})

@app.route('/generate', methods=['POST'])
@rate_limit
def generate_video():
    """
    Generate a YouTube Short video
    
    Expected JSON body:
    {
        "hook": "...",
        "content": "...",
        "cta": "...",
        "title": "...",
        "audioPath": "/videos/audio_xxx.wav" (optional),
        "outputPath": "/videos/short_xxx.mp4" (optional),
        "useAiImages": true (optional, default: true)
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
            use_ai_images=use_ai_images
        )
        
        # Check if video was created
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            return jsonify({
                "success": True,
                "videoPath": result_path,
                "fileSize": file_size,
                "message": f"Video created successfully"
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

@app.route('/info', methods=['GET'])
def info():
    """Get server info"""
    return jsonify({
        "service": "AutoTube Video Generation API",
        "version": "2.1.0-secure",
        "features": ["AI Image Slideshows", "Crossfade Transitions", "Ken Burns Zoom"],
        "endpoints": {
            "/health": "Health check",
            "/generate": "POST - Generate video",
            "/info": "Server info"
        }
    })

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
    print("🎬 Starting AutoTube Video Generation API v2.1 (Secure)")
    print("   Features: AI Image Slideshows, Transitions, Zoom Effects")
    print("   Security: Rate limiting, Input validation, No debug info")
    print("   Listening on http://0.0.0.0:5001")
    # NEVER run with debug=True in production
    app.run(host='0.0.0.0', port=5001, debug=False)
