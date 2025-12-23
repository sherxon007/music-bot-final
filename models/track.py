"""Track model representing a music track."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    """Represents a music track from external API."""
    
    title: str
    artist: str
    duration: int  # in seconds
    preview_url: Optional[str] = None
    audio_url: Optional[str] = None
    album: Optional[str] = None
    artwork_url: Optional[str] = None
    track_id: Optional[str] = None
    source: Optional[str] = None  # 'itunes', 'deezer', etc.
    
    @property
    def duration_str(self) -> str:
        """Format duration as mm:ss."""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def full_title(self) -> str:
        """Get full track title with artist."""
        return f"{self.artist} – {self.title}"
    
    @property
    def download_url(self) -> Optional[str]:
        """Get the best available download URL."""
        return self.audio_url or self.preview_url
    
    def __str__(self) -> str:
        """String representation of track."""
        return f"{self.full_title} ({self.duration_str})"
