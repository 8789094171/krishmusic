"""
Configuration module for KrishMusic bot.
Centralized settings with environment detection and validation.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseSettings, validator

# Load environment variables
load_dotenv()

# Detect runtime environment
IS_TERMUX = os.path.exists("/data/data/com.termux") or "TERMUX_VERSION" in os.environ
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

# Database paths
BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "data"
DB_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_DIR / 'krishmusic.db'}"

# FFmpeg detection for Termux
def find_ffmpeg() -> Optional[str]:
    """Find ffmpeg binary in system PATH or Termux"""
    import shutil
    
    # Standard PATH search
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    
    # Termux-specific paths
    if IS_TERMUX:
        termux_paths = [
            "/data/data/com.termux/files/usr/bin/ffmpeg",
            "/system/bin/ffmpeg",
        ]
        for path in termux_paths:
            if os.path.exists(path):
                return path
    
    return None

class Settings(BaseSettings):
    """Main configuration class with validation."""
    
    # Telegram settings
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    api_id: str = os.getenv("API_ID", "")
    api_hash: str = os.getenv("API_HASH", "")
    bot_owner_id: int = int(os.getenv("BOT_OWNER_ID", "0"))
    
    # Database
    database_url: str = DATABASE_URL
    
    # Voice chat settings
    enable_voice_chat: bool = True
    voice_sample_rate: int = 48000  # Telegram voice chat standard
    
    # Audio processing
    ffmpeg_path: Optional[str] = find_ffmpeg()
    max_audio_duration: int = 3600  # 1 hour max per song
    audio_bitrate: str = "128k"
    
    # Logging
    log_level: str = "INFO"
    
    # Runtime settings
    python_version: str = PYTHON_VERSION
    is_termux: bool = IS_TERMUX
    is_windows: bool = IS_WINDOWS
    is_linux: bool = IS_LINUX
    
    # Feature flags
    enable_persistence: bool = True
    enable_clone_bots: bool = True
    enable_broadcast: bool = True
    
    @validator("telegram_bot_token", pre=True, always=True)
    def validate_token(cls, v):
        if not v:
            raise ValueError(
                "❌ TELEGRAM_BOT_TOKEN not found!\n"
                "   Add 'TELEGRAM_BOT_TOKEN=your_token' to .env\n"
                "   Get it from @BotFather on Telegram"
            )
        if not isinstance(v, str) or len(v) < 10:
            raise ValueError("Invalid token format")
        return v
    
    @validator("bot_owner_id", pre=True, always=True)
    def validate_owner_id(cls, v):
        if not v or v == 0:
            raise ValueError(
                "❌ BOT_OWNER_ID not found!\n"
                "   Add 'BOT_OWNER_ID=your_id' to .env\n"
                "   Get your ID from @userinfobot on Telegram"
            )
        return v
    
    @validator("ffmpeg_path", pre=True, always=True)
    def validate_ffmpeg(cls, v):
        if v is None:
            print(
                "⚠️  FFmpeg not found in PATH\n"
                "   Voice chat will be DISABLED\n"
                "   Install: apt install ffmpeg (Linux) or brew install ffmpeg (macOS)"
            )
            return None
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Initialize settings
try:
    settings = Settings()
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    sys.exit(1)

# Log configuration status
def log_config():
    """Print configuration summary at startup."""
    print("\n" + "="*60)
    print("🎵 KrishMusic Bot Configuration")
    print("="*60)
    print(f"Python Version:      {settings.python_version}")
    print(f"Platform:            {'Termux' if IS_TERMUX else 'Linux' if IS_LINUX else 'Windows' if IS_WINDOWS else 'Unknown'}")
    print(f"FFmpeg:              {'✅ Available' if settings.ffmpeg_path else '❌ Not found (voice disabled)'}")
    print(f"Database:            {settings.database_url}")
    print(f"Voice Chat Support:  {'✅ Enabled' if settings.enable_voice_chat and settings.ffmpeg_path else '❌ Disabled'}")
    print(f"Persistence:         {'✅ Enabled' if settings.enable_persistence else '❌ Disabled'}")
    print("="*60 + "\n")

if __name__ == "__main__":
    log_config()
    print("✅ Configuration loaded successfully!")
