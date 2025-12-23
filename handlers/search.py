"""Handlers for music search and track operations."""
from io import BytesIO
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from db import (
    async_session_maker, UserRepository, SearchCacheRepository,
    StatisticsRepository, AdRepository
)
from services import Localization, MusicService
from keyboards import get_track_actions_keyboard, get_track_list_keyboard
from config import Config
from utils import logger


router = Router()

# Track counter for showing ads
user_track_counter = {}


@router.message(F.text & ~F.text.startswith("/"))
async def handle_search_query(message: Message):
    """Handle text messages as search queries."""
    # IGNORE URLS (Let social handler take them)
    if "http" in message.text:
        return

    user_id = message.from_user.id
    query = message.text.strip()
    
    if not query:
        return
    
    # Get user language and log activity
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        stats_repo = StatisticsRepository(session)
        user = await user_repo.get_or_create_user(user_id)
        lang = user.language
        
        # Log search activity
        await stats_repo.log_activity(user_id, "search", query)
    
    # Send searching message
    searching_msg = await message.answer(
        text=Localization.get("searching", lang)
    )
    
    try:
        # Search for tracks
        async with MusicService() as music_service:
            tracks = await music_service.search(query, limit=20)
        
        if not tracks:
            # No results found
            await searching_msg.edit_text(
                text=Localization.get("track_not_found", lang)
            )
            logger.info(f"No tracks found for query: {query}")
            return
        
        # Save search results to cache
        async with async_session_maker() as session:
            cache_repo = SearchCacheRepository(session)
            await cache_repo.save_search(user_id, query, tracks)
        
        # Send the best match (first track)
        best_track = tracks[0]
        success = await send_track(message, best_track, lang)
        
        # Delete searching message
        try:
            await searching_msg.delete()
        except Exception:
            pass
        
        if success:
            # Show more results button if available
            has_more = len(tracks) > 1
            await message.answer(
                text="✅",
                reply_markup=get_track_actions_keyboard(lang, has_more=has_more, track_index=0)
            )
            
            # Check if we should show an ad
            await check_and_show_ad(message, user_id)
        
        logger.info(f"Found {len(tracks)} tracks for query: {query}")
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        await searching_msg.edit_text(
            text=Localization.get("network_error", lang)
        )


@router.callback_query(F.data == "more_results")
async def show_more_results(callback: CallbackQuery):
    """Show more search results."""
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        cache_repo = SearchCacheRepository(session)
        
        user = await user_repo.get_user(user_id)
        if not user:
            await callback.answer("Error: User not found")
            return
        
        lang = user.language
        
        # Get cached tracks
        tracks = await cache_repo.get_cached_tracks(user_id)
        
        if not tracks or len(tracks) <= 1:
            await callback.answer(
                text=Localization.get("no_more_results", lang)
            )
            return
            
        # Try to delete the previous message (Preview Audio)
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id - 1
            )
        except Exception:
            pass
        
        # Show track list (skip first track as it was already sent)
        offset = 1
        
        # Delete old message to clean up chat
        await callback.message.delete()
        
        await callback.message.answer(
            text=Localization.get("select_track", lang),
            reply_markup=get_track_list_keyboard(tracks, offset, lang)
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("track:"))
async def send_selected_track(callback: CallbackQuery):
    """Send selected track from the list."""
    user_id = callback.from_user.id
    track_index = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        cache_repo = SearchCacheRepository(session)
        
        user = await user_repo.get_user(user_id)
        if not user:
            await callback.answer("Error: User not found")
            return
        
        lang = user.language
        
        # Get cached tracks
        tracks = await cache_repo.get_cached_tracks(user_id)
        
        if not tracks or track_index >= len(tracks):
            await callback.answer(
                text=Localization.get("track_not_found", lang)
            )
            return
        
        selected_track = tracks[track_index]
        
        # Delete the list message first
        await callback.message.delete()
        
        # Send searching notification
        searching_msg = await callback.message.answer(
            text=Localization.get("searching", lang)
        )
        
        success = await send_track(searching_msg, selected_track, lang)
        
        if success:
            # Show "Full Music" button for selected track too
            await searching_msg.answer(
                text="✅",
                reply_markup=get_track_actions_keyboard(
                    lang, 
                    has_more=True, # Allow going back to list/more results
                    track_index=track_index
                )
            )
            await callback.answer("✅")
        else:
            await callback.answer(
                text=Localization.get("download_error", lang)
            )


@router.callback_query(F.data == "next_page")
async def next_page(callback: CallbackQuery):
    """Show next page of results."""
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        cache_repo = SearchCacheRepository(session)
        
        user = await user_repo.get_user(user_id)
        tracks = await cache_repo.get_cached_tracks(user_id)
        
        if not user or not tracks:
            await callback.answer("Error")
            return
        
        lang = user.language
        current_offset = await cache_repo.get_offset(user_id)
        new_offset = current_offset + Config.MAX_RESULTS_PER_PAGE
        
        if new_offset >= len(tracks):
            await callback.answer(
                text=Localization.get("no_more_results", lang)
            )
            return
        
        await cache_repo.update_offset(user_id, new_offset)
        
        await callback.message.edit_reply_markup(
            reply_markup=get_track_list_keyboard(tracks, new_offset, lang)
        )
    
    await callback.answer()


@router.callback_query(F.data == "prev_page")
async def prev_page(callback: CallbackQuery):
    """Show previous page of results."""
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        cache_repo = SearchCacheRepository(session)
        
        user = await user_repo.get_user(user_id)
        tracks = await cache_repo.get_cached_tracks(user_id)
        
        if not user or not tracks:
            await callback.answer("Error")
            return
        
        lang = user.language
        current_offset = await cache_repo.get_offset(user_id)
        new_offset = max(0, current_offset - Config.MAX_RESULTS_PER_PAGE)
        
        await cache_repo.update_offset(user_id, new_offset)
        
        await callback.message.edit_reply_markup(
            reply_markup=get_track_list_keyboard(tracks, new_offset, lang)
        )
    
    await callback.answer()


@router.callback_query(F.data == "back_to_search")
async def back_to_search(callback: CallbackQuery):
    """Return to search mode."""
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_user(user_id)
        
        if not user:
            await callback.answer("Error")
            return
        
        lang = user.language
    
    await callback.message.edit_text(
        text=Localization.get("welcome", lang, bot_username=Config.BOT_USERNAME)
    )
    
    await callback.answer()


async def send_track(message: Message, track, lang: str) -> bool:
    """
    Download and send a track to the user.
    
    Args:
        message: Message object to reply to
        track: Track object to send
        lang: User language
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not track.download_url:
            logger.warning(f"No download URL for track: {track.title}")
            await message.answer(
                text=Localization.get("download_error", lang)
            )
            return False
        
        # Download audio
        async with MusicService() as music_service:
            audio_data = await music_service.download_audio(track.download_url)
        
        if not audio_data:
            logger.warning(f"Failed to download track: {track.title}")
            await message.answer(
                text=Localization.get("download_error", lang)
            )
            return False
        
        # Create caption
        caption = Localization.get(
            "track_caption",
            lang,
            title=track.title,
            artist=track.artist,
            duration=track.duration_str
        )
        
        # Send audio
        audio_file = BufferedInputFile(
            audio_data,
            filename=f"{track.artist} - {track.title}.mp3"
        )
        
        await message.answer_audio(
            audio=audio_file,
            title=track.title,
            performer=track.artist,
            caption=caption
        )
        
        # Log download activity
        async with async_session_maker() as session:
            stats_repo = StatisticsRepository(session)
            await stats_repo.log_activity(message.from_user.id, "download")
        
        logger.info(f"Successfully sent track: {track.full_title}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending track: {e}")
        await message.answer(
            text=Localization.get("download_error", lang)
        )
        return False


async def check_and_show_ad(message: Message, user_id: int):
    """Check if we should show an ad and display it."""
    # Update counter
    if user_id not in user_track_counter:
        user_track_counter[user_id] = 0
    
    user_track_counter[user_id] += 1
    
    # Show ad after N tracks
    if user_track_counter[user_id] >= Config.SHOW_AD_AFTER_TRACKS:
        user_track_counter[user_id] = 0  # Reset counter
        
        async with async_session_maker() as session:
            ad_repo = AdRepository(session)
            ad = await ad_repo.get_random_active_ad()
            
            if ad:
                await display_ad(message, ad, ad_repo)


async def display_ad(message: Message, ad, ad_repo: AdRepository):
    """Display an advertisement."""
    try:
        # Increment impressions
        await ad_repo.increment_impressions(ad.id)
        
        # Build keyboard if button exists
        reply_markup = None
        if ad.button_text and ad.button_url:
            keyboard = [[
                InlineKeyboardButton(
                    text=ad.button_text,
                    url=ad.button_url,
                    callback_data=f"ad_click:{ad.id}"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Send ad based on type
        if ad.ad_type == "text":
            await message.answer(
                text=ad.text or "📢 Reklama",
                reply_markup=reply_markup
            )
        elif ad.ad_type == "photo" and ad.file_id:
            await message.answer_photo(
                photo=ad.file_id,
                caption=ad.text,
                reply_markup=reply_markup
            )
        elif ad.ad_type == "video" and ad.file_id:
            await message.answer_video(
                video=ad.file_id,
                caption=ad.text,
                reply_markup=reply_markup
            )
        
        logger.info(f"Displayed ad {ad.id} to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error displaying ad: {e}")


@router.callback_query(F.data.startswith("ad_click:"))
async def handle_ad_click(callback: CallbackQuery):
    """Handle ad click."""
    ad_id = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        ad_repo = AdRepository(session)
        await ad_repo.increment_clicks(ad_id)
    
    await callback.answer()


@router.callback_query(F.data.startswith("full_audio:"))
async def handle_full_audio_request(callback: CallbackQuery):
    """Handle full audio download request using YouTubeService (B Plan)."""
    user_id = callback.from_user.id
    
    # Get User Language
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_user(user_id)
        lang = user.language if user else "uz"
        
        # NEW: Get track from cache using index
        cache_repo = SearchCacheRepository(session)
        tracks = await cache_repo.get_cached_tracks(user_id)
    
    try:
        # data format: "full_audio:{index}"
        track_index = int(callback.data.split(":")[1])
        
        if not tracks or track_index >= len(tracks):
            await callback.answer("⚠️ Session expired or invalid track.")
            return

        track = tracks[track_index]
        artist = track.artist
        title = track.title
        search_query = f"{artist} - {title}"
        
    except Exception as e:
        logger.error(f"Error parsing callback: {e}")
        await callback.answer("Error parsing track info")
        return
    
    # Text messages
    loading_text = {
        "uz": f"🔍 <b>{search_query}</b> youtube'dan qidirilmoqda...",
        "ru": f"🔍 <b>{search_query}</b> ищется на YouTube...",
        "en": f"🔍 Searching <b>{search_query}</b> on YouTube..."
    }
    
    downloading_text = {
        "uz": "📥 Topildi! Yuklab olinmoqda...",
        "ru": "📥 Найдено! Загрузка...",
        "en": "📥 Found! Downloading..."
    }

    # 1. Notify User
    await callback.answer("🔍 Qidirilmoqda...")
    
    # Delete the menu message (buttons)
    await callback.message.delete()
    
    # Try to delete the previous message (Preview Audio)
    try:
        await callback.message.bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id - 1
        )
    except Exception:
        pass # If fails (message too old or not found), just ignore
    
    status_msg = await callback.message.answer(text=loading_text.get(lang, loading_text["en"]))
    
    try:
        from services.youtube_service import YouTubeService
        
        # 2. Search Locally (Free & Fast)
        video_id = await YouTubeService.get_video_id(search_query)
        
        if not video_id:
            await status_msg.edit_text("❌ YouTube'da topilmadi.")
            return

        await status_msg.edit_text(downloading_text.get(lang, downloading_text["en"]))

        # 3. Get Audio File ID from API (Fast & Serverless)
        file_id = await YouTubeService.get_audio_file_id(video_id)
        
        if not file_id:
            await status_msg.edit_text("❌ Yuklashda xatolik (API Error).")
            return
        
        # 4. Send Audio (Instant)
        caption_text = (
            f"🎵 <b>{title}</b>\n"
            f"👤 {artist}\n"
            f"📥 {Config.BOT_USERNAME}"
        )
        
        # 4. Send Audio (Instant)
        caption_text = (
            f"🎵 <b>{title}</b>\n"
            f"👤 {artist}\n"
            f"📥 {Config.BOT_USERNAME}"
        )
        
        await callback.message.answer_audio(
            audio=file_id,
            caption=caption_text,
            title=title,
            performer=artist
        )
        
        await status_msg.delete()
        
        # 5. Log
        async with async_session_maker() as session:
            stats_repo = StatisticsRepository(session)
            await stats_repo.log_activity(user_id, "download_full_fastsaver", search_query)
            
        logger.info(f"Sent full audio via FastSaver: {search_query}")
        
    except Exception as e:
        logger.error(f"Handler error: {e}")
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)[:50]}")


@router.callback_query(F.data.startswith("lyrics:"))
async def handle_lyrics_request(callback: CallbackQuery):
    """Handle lyrics request."""
    user_id = callback.from_user.id
    
    # Get User Language
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_user(user_id)
        lang = user.language if user else "uz"
        
        # Get track from cache
        cache_repo = SearchCacheRepository(session)
        tracks = await cache_repo.get_cached_tracks(user_id)
    
    try:
        track_index = int(callback.data.split(":")[1])
        
        if not tracks or track_index >= len(tracks):
            await callback.answer("⚠️ Session expired.")
            return

        track = tracks[track_index]
        query = f"{track.artist} - {track.title}"
        
    except Exception as e:
        logger.error(f"Error parsing lyrics callback: {e}")
        await callback.answer("Error")
        return
        
    await callback.answer("📝 Matn qidirilmoqda...")
    status_msg = await callback.message.answer(f"📝 <b>{track.artist} - {track.title}</b>\n\n🔍 Qidirilmoqda...")
    
    try:
        from services.lyrics_service import LyricsService
        lyrics = await LyricsService.get_lyrics(track.artist, track.title)
        
        if lyrics:
            # Create lyrics message (max 4096 chars)
            header = f"📝 <b>{track.artist} - {track.title}</b>\n\n"
            full_text = header + lyrics
            
            if len(full_text) > 4000:
                full_text = full_text[:4000] + "..."
                
            await status_msg.edit_text(full_text)
        else:
            await status_msg.edit_text(f"📝 <b>{track.artist} - {track.title}</b>\n\n❌ Matn topilmadi.")
            
    except Exception as e:
        logger.error(f"Lyrics error: {e}")
        await status_msg.edit_text(f"❌ Xatolik: {e}")
