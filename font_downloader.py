import os
import requests
from pathlib import Path

# Configuration
FONT_DIR = Path("/fonts")
FONT_DIR.mkdir(exist_ok=True)

# Google Fonts URLs (Direct download links)
FONTS = {
    "BebasNeue-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf",
    "Montserrat-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf",
    "Poppins-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf",
    "Oswald-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Bold.ttf",
    "Roboto-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Bold.ttf",
}

def download_fonts():
    print(f"📂 Checking fonts in {FONT_DIR}...")
    downloaded_count = 0
    
    for font_name, url in FONTS.items():
        font_path = FONT_DIR / font_name
        if font_path.exists():
            print(f"✅ {font_name} already exists.")
            continue
        
        print(f"⬇️ Downloading {font_name}...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(font_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Successfully downloaded {font_name}")
            downloaded_count += 1
        except Exception as e:
            print(f"❌ Failed to download {font_name}: {e}")
    
    print(f"\n🎉 Font setup complete! {downloaded_count} new fonts installed.")

if __name__ == "__main__":
    download_fonts()
