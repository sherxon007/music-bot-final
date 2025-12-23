"""Application configuration and environment variables."""
import os
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration class."""
    
    # Bot settings
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "@music_saver_bot")  # For FastSaver API
    
    
    # Admin settings
    SUPER_ADMIN_IDS: List[int] = [
        int(id.strip()) 
        for id in os.getenv("SUPER_ADMIN_IDS", "").split(",") 
        if id.strip() and id.strip().isdigit()
    ]
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./music_bot.db"
    )
    
    # Music API Keys (if needed)
    DEEZER_API_KEY: Optional[str] = os.getenv("DEEZER_API_KEY")
    ITUNES_API_KEY: Optional[str] = os.getenv("ITUNES_API_KEY")
    
    # FastSaver API (for social media and YouTube)
    FASTSAVER_API_TOKEN: str = os.getenv("FASTSAVER_API_TOKEN", "")
    FASTSAVER_API_URL: str = "https://api.fastsaver.io"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Endpoints
    ITUNES_API_URL: str = "https://itunes.apple.com/search"
    DEEZER_API_URL: str = "https://api.deezer.com/search"
    
    # Pagination
    MAX_RESULTS_PER_PAGE: int = 5
    MAX_INLINE_RESULTS: int = 10
    
    # Audio settings
    AUDIO_BITRATE: int = 128  # kbps
    MAX_DOWNLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    
    # Advertisement settings
    SHOW_AD_AFTER_TRACKS: int = 5  # Show ad after every N tracks
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required in environment variables")


# Validate config on import
Config.validate()
