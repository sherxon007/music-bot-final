"""Shazam music identification handler."""
from io import BytesIO
from aiogram import Router, F
from aiogram.types import Message
from db import async_session_maker, UserRepository, StatisticsRepository
from services.shazam_service import ShazamService
from services.youtube_service import YouTubeService
from config import Config
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.content_type.in_({'audio', 'voice', 'video', 'video_note'}))
async def handle_shazam_identify(message: Message):
    """Handle audio/video files for Shazam identification."""
    user_id = message.from_user.id
    
    # 0. Get user language
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create_user(user_id)
        lang = user.language

    # 1. Notify User
    loading_text = {
        "uz": "🎵 Musiqa aniqlanmoqda...",
        "ru": "🎵 Определяем музыку...",
        "en": "🎵 Identifying music..."
    }
    status_msg = await message.reply(loading_text.get(lang, loading_text["uz"]))
    
    try:
        # 2. Get File ID
        if message.audio: file_id = message.audio.file_id
        elif message.voice: file_id = message.voice.file_id
        elif message.video: file_id = message.video.file_id
        else: file_id = message.video_note.file_id
        
        # 3. Download File (Telegram -> Bot)
        # We need to be careful with size. Max 20MB for bot download usually.
        # FastSaver accepts up to 50MB.
        file_info = await message.bot.get_file(file_id)
        if file_info.file_size and file_info.file_size > 20 * 1024 * 1024:
            await status_msg.edit_text("❌ Fayl hajmi juda katta (Max 20MB).")
            return

        file_bytes = BytesIO()
        await message.bot.download_file(file_info.file_path, file_bytes)
        file_bytes.seek(0)
        
        # 4. Identify (Shazam)
        shazam_result = await ShazamService.identify_music(file_bytes.read())
        
        if not shazam_result:
            not_found_text = {
                "uz": "❌ Aniqlab bo'lmadi. Iltimos, musiqa nomini yozing.",
                "ru": "❌ Не удалось распознать. Пожалуйста, напишите название.",
                "en": "❌ Could not identify. Please type the name."
            }
            await status_msg.edit_text(not_found_text.get(lang, not_found_text["uz"]))
            return
        
        # 5. Extract Info
        title = shazam_result.get('title', 'Unknown')
        artist = shazam_result.get('artist', 'Unknown')
        youtube_results = shazam_result.get('results', [])
        
        found_text = {
            "uz": f"✅ <b>{artist} - {title}</b>\n📥 Yuklanmoqda...",
            "ru": f"✅ <b>{artist} - {title}</b>\n📥 Загрузка...",
            "en": f"✅ <b>{artist} - {title}</b>\n📥 Downloading..."
        }
        await status_msg.edit_text(found_text.get(lang, found_text["uz"]))
        
        # 6. Download Full Audio
        # We have 2 options: Use video_id from Shazam results OR Search locally.
        # Shazam results are usually accurate. Let's try that first.
        
        file_id = None
        if youtube_results:
            # Take the first video ID from Shazam's proposed YouTube videos
            video_id = youtube_results[0].get('video_id')
            if video_id:
                file_id = await YouTubeService.get_audio_file_id(video_id)
        
        # Fallback: If Shazam didn't give video_id or it failed, search locally
        if not file_id:
            logger.info("Shazam results empty/failed, trying local search backup...")
            search_query = f"{artist} - {title}"
            video_id = await YouTubeService.get_video_id(search_query)
            if video_id:
                file_id = await YouTubeService.get_audio_file_id(video_id)
        
        if not file_id:
             await status_msg.edit_text("❌ Musiqa topildi, lekin yuklab bo'lmadi.")
             return

        # 7. Send Audio
        lyrics_text = shazam_result.get('lyrics')
        
        caption = f"🎵 <b>{title}</b>\n👤 {artist}\n🔍 Shazam\n📥 {Config.BOT_USERNAME}"
        
        await message.answer_audio(
            audio=file_id,
            caption=caption,
            title=title,
            performer=artist
        )
        await status_msg.delete()
        
        # 8. Send Lyrics if available
        if lyrics_text:
            lyrics_header = {
                "uz": "📝 <b>Qo'shiq matni:</b>\n\n",
                "ru": "📝 <b>Текст песни:</b>\n\n",
                "en": "📝 <b>Lyrics:</b>\n\n"
            }
            # Limit lyrics length to avoid message too long error
            full_lyrics = lyrics_header.get(lang, "en") + lyrics_text
            if len(full_lyrics) > 4000:
                full_lyrics = full_lyrics[:4000] + "..."
            
            await message.answer(full_lyrics)
        
        # 8. Log
        async with async_session_maker() as session:
            stats = StatisticsRepository(session)
            await stats.log_activity(user_id, "shazam_identify", f"{artist} - {title}")

    except Exception as e:
        logger.error(f"Shazam handler exception: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi.")
