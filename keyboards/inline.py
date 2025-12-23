"""Inline keyboard builders with full audio support."""
from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services import Localization
from models import Track
from config import Config


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Build language selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🇺🇿 O'zbek tili",
                callback_data="lang:uz"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇷🇺 Русский",
                callback_data="lang:ru"
            )
        ],
        [
            InlineKeyboardButton(
                text="🇬🇧 English",
                callback_data="lang:en"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_track_actions_keyboard(
    lang: str, 
    has_more: bool = True,
    track_index: int = 0
) -> InlineKeyboardMarkup:
    """
    Build keyboard with track actions including full audio button.
    
    Args:
        lang: User language
        has_more: Whether there are more results available
        track_index: Index of the track in the current search cache
    """
    keyboard = []
    
    # YANGI: To'liq musiqa tugmasi
    full_audio_text = {
        "uz": "🎵 To'liq",
        "ru": "🎵 Полная",
        "en": "🎵 Full"
    }
    
    keyboard.append([
        InlineKeyboardButton(
            text=full_audio_text.get(lang, full_audio_text["en"]),
            callback_data=f"full_audio:{track_index}"
        )
    ])
    
    if has_more:
        keyboard.append([
            InlineKeyboardButton(
                text=Localization.get("more_results", lang),
                callback_data="more_results"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text=Localization.get("change_language", lang),
            callback_data="change_lang"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_lyrics_keyboard(track_index: int) -> InlineKeyboardMarkup:
    """Build keyboard with only Lyrics button."""
    keyboard = [[
        InlineKeyboardButton(
            text="📝 Lyrics",
            callback_data=f"lyrics:{track_index}"
        )
    ]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_track_list_keyboard(
    tracks: List[Track], 
    offset: int, 
    lang: str
) -> InlineKeyboardMarkup:
    """
    Build keyboard with list of tracks.
    
    Args:
        tracks: List of Track objects
        offset: Current offset for pagination
        lang: User language
    """
    keyboard = []
    
    # Add track buttons
    max_results = Config.MAX_RESULTS_PER_PAGE
    end_idx = min(offset + max_results, len(tracks))
    
    for i, track in enumerate(tracks[offset:end_idx], start=offset):
        button_text = f"🎵 {track.artist} – {track.title} ({track.duration_str})"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"track:{i}"
            )
        ])
    
    # Pagination
    nav_buttons = []
    
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data="prev_page"
            )
        )
    
    if end_idx < len(tracks):
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data="next_page"
            )
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Back button
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 " + Localization.get("change_language", lang).replace("🌐 ", ""),
            callback_data="back_to_search"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Build simple back button keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔙",
                callback_data="back_to_search"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
