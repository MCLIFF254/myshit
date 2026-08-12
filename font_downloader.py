#!/usr/bin/env python3
"""
Font Downloader for AutoTube Pipeline
Downloads professional Google Fonts required for cinematic captions.
"""
import os
import requests

FONT_DIR = "fonts"
FONTS = {
    "BebasNeue-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    "Montserrat-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf",
    "Poppins-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Oswald-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Bold.ttf",
    "Roboto-Bold.ttf": "https://github.com/google/fonts/raw/main/main/roboto/Roboto-Bold.ttf",
}

def main():
    print("🎨 AutoTube Font Downloader")
    if not os.path.exists(FONT_DIR):
        os.makedirs(FONT_DIR)
    
    for name, url in FONTS.items():
        try:
            print(f"⬇️ Downloading {name}...")
            r = requests.get(url)
            with open(os.path.join(FONT_DIR, name), 'wb') as f:
                f.write(r.content)
            print(f"✅ Saved {name}")
        except Exception as e:
            print(f"❌ Failed {name}: {e}")

if __name__ == "__main__":
    main()