from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from services.social_service import SocialDownloaderService
from db import async_session_maker, StatisticsRepository
from config import Config
import re
import aiohttp
import logging
from html import escape

logger = logging.getLogger(__name__)
router = Router()

async def download_content(url: str) -> bytes | None:
    """Download content ensuring browser-like headers to avoid 403."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.instagram.com/"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.read()
                logger.error(f"Failed to download content: {resp.status} for {url}")
                return None
    except Exception as e:
        logger.error(f"Download exception: {e}")
        return None

@router.message(F.text & F.text.regexp(r'https?://'))
async def social_media_handler(message: Message):
    """Handle social media links (Instagram, TikTok, etc)."""
    url = message.text.strip()
    user_id = message.from_user.id
    
    # Extract authentic URL
    urls = re.findall(r'(https?://\S+)', url)
    if urls:
        url = urls[0]
    
    # 1. Check for supported domains (Shorts/Video)
    if 'youtube.com' in url or 'youtu.be' in url:
        status_msg = await message.reply("⏳ YouTube video yuklanmoqda...")
        try:
            # Use /youtube/download endpoint for direct video
            async with aiohttp.ClientSession() as session:
                if '?' in url: url = url.split('?')[0] # Clean URL for Shorts
                
                api_url = f"{Config.FASTSAVER_API_URL}/v1/youtube/download"
                headers = {
                    'X-Api-Key': Config.FASTSAVER_API_TOKEN,
                    'Content-Type': 'application/json'
                }
                payload = {'url': url, 'format': '720p'}
                
                # Define Branded Caption
                branded_caption = f"📥 {Config.BOT_USERNAME} orqali istagan musiqangizni tez va oson toping!🚀"
                
                async with session.post(api_url, json=payload, headers=headers) as resp:
                    data = await resp.json()
                    
                    if not data.get('download_url'):
                        await status_msg.edit_text("❌ YouTube video topilmadi.")
                        return
                    
                    d_url = data['download_url']
                    
                    # TRY 1: Direct URL (Serverless)
                    try:
                        await message.answer_video(
                            video=d_url,
                            caption=branded_caption
                        )
                        await status_msg.delete()
                        return
                    except Exception:
                        pass # Fallback to local download

                    # TRY 2: Local Download (Fallback)
                    content = await download_content(d_url)
                    if content:
                        await message.answer_video(
                            video=BufferedInputFile(content, filename="video.mp4"),
                            caption=branded_caption
                        )
                        await status_msg.delete()
                    else:
                        await status_msg.edit_text("❌ Yuklab bo'lmadi.")
                    return

        except Exception as e:
            await status_msg.edit_text(f"❌ Xatolik: {escape(str(e)[:100])}")
            return

    # For other social media (Insta, TikTok) -> use /fetch
    if not SocialDownloaderService.is_supported_url(url):
        return 
    
    # 2. Notify user
    status_msg = await message.reply("⏳ Media yuklanmoqda...")
    
    try:
        # 3. Fetch Info
        data = await SocialDownloaderService.fetch_media(url)
        
        if not data or not data.get('download_url'):
            await status_msg.edit_text("❌ Media topilmadi.")
            return

        download_url = data['download_url']
        
        # Override caption with branded message
        caption = f"📥 {Config.BOT_USERNAME} orqali istagan musiqangizni tez va oson toping!🚀"
        
        media_type = data.get('type', 'video')
        
        # TRY 1: Direct URL (No Server Load)
        sent = False
        logger.info(f"Attempting DIRECT download for: {url}")
        try:
            if media_type == 'video':
                await message.answer_video(video=download_url, caption=caption)
            elif media_type == 'image':
                await message.answer_photo(photo=download_url, caption=caption)
            elif media_type == 'audio':
                await message.answer_audio(audio=download_url, caption=caption)
            else:
                 await message.answer_document(document=download_url, caption=caption)
            
            logger.info("✅ Direct download successful (Serverless).")
            sent = True
        except Exception as e:
            logger.warning(f"⚠️ Direct download failed (Telegram rejected URL). Error: {e}")
            logger.info("🔄 Switching to FALLBACK mode (Server Download)...")
        
        # TRY 2: Server Download (Fallback for 403 Forbidden)
        if not sent:
            # User still sees "Media yuklanmoqda..." (No panic)
            file_content = await download_content(download_url)
            
            if not file_content:
                logger.error("❌ Fallback download also failed (Could not fetch bytes).")
                await status_msg.edit_text("❌ Faylni yuklab bo'lmadi (Manba ruxsat bermadi).")
                return
            
            logger.info(f"✅ Downloaded {len(file_content)} bytes to RAM. Sending to user...")
            
            try:
                if media_type == 'video':
                    await message.answer_video(
                        video=BufferedInputFile(file_content, filename="video.mp4"),
                        caption=caption
                    )
                elif media_type == 'image':
                    await message.answer_photo(
                        photo=BufferedInputFile(file_content, filename="image.jpg"),
                        caption=caption
                    )
                elif media_type == 'audio':
                    await message.answer_audio(
                        audio=BufferedInputFile(file_content, filename="audio.mp3"),
                        caption=caption
                    )
                else:
                     await message.answer_document(
                        document=BufferedInputFile(file_content, filename="file"),
                        caption=caption
                    )
                logger.info("✅ Fallback sent successfully.")
            except Exception as e:
                logger.error(f"❌ Error sending bytes to Telegram: {e}")
                await status_msg.edit_text("❌ Yuborishda xatolik yuz berdi.")
                return
        
        # Cleanup
        await status_msg.delete()
        
        async with async_session_maker() as session:
             stats = StatisticsRepository(session)
             await stats.log_activity(user_id, "social_download", url)

    except Exception as e:
        logger.error(f"CRITICAL HANDLER ERROR: {e}")
        await status_msg.delete()
        await message.answer("❌ Tizim xatoligi (Adminlar xabardor qilindi).")
