"""Localization service for multi-language support."""
from typing import Dict, Any


class Localization:
    """Centralized localization for UZ/RU/EN messages."""
    
    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        "welcome": {
            "uz": "🔥 Assalomu alaykum. {bot_username} ga xush kelibsiz. Bot orqali quyidagilarni yuklab olishingiz mumkin:\n\n"
                  "• Instagram - post va IGTV + audio bilan;\n"
                  "• TikTok - suv belgisiz video + audio bilan;\n"
                  "• YouTube - videolar va shorts + audio bilan;\n"
                  "• Snapchat - suv belgisiz video + audio bilan;\n"
                  "• Likee - suv belgisiz video + audio bilan;\n"
                  "• Pinterest - suv belgisiz video va rasmlar + audio bilan;\n\n"
                  "🎵 <b>Musiqa qidiruvi (30s intro + Full MP3)</b>\n\n"
                  "⚡️ <b>Shazam funksiya:</b>\n"
                  "• Qo‘shiq nomi yoki ijrochi ismi\n"
                  "• Qo‘shiq matni\n"
                  "• Ovozli xabar\n"
                  "• Video\n"
                  "• Audio\n"
                  "• Video xabar\n\n"
                  "🚀 <b>Yuklab olmoqchi bo'lgan videoga havolani yuboring!</b>",
            "ru": "🔥 Здравствуйте. Добро пожаловать в {bot_username}. Через бот вы можете скачать:\n\n"
                  "• Instagram - посты, IGTV + аудио;\n"
                  "• TikTok - видео без водяных знаков + аудио;\n"
                  "• YouTube - видео и шортс + аудио;\n"
                  "• Snapchat - видео без водяных знаков + аудио;\n"
                  "• Likee - видео без водяных знаков + аудио;\n"
                  "• Pinterest - видео и фото без водяных знаков + аудио;\n\n"
                  "🎵 <b>Поиск музыки (30с демо + Полный MP3)</b>\n\n"
                  "⚡️ <b>Функция Shazam:</b>\n"
                  "• Название песни или имя исполнителя\n"
                  "• Текст песни\n"
                  "• Голосовое сообщение\n"
                  "• Видео\n"
                  "• Аудио\n"
                  "• Видеосообщение\n\n"
                  "🚀 <b>Отправьте ссылку на видео, которое хотите скачать!</b>",
            "en": "🔥 Hello. Welcome to {bot_username}. You can download the following:\n\n"
                  "• Instagram - posts, IGTV + audio;\n"
                  "• TikTok - no watermark video + audio;\n"
                  "• YouTube - videos and shorts + audio;\n"
                  "• Snapchat - no watermark video + audio;\n"
                  "• Likee - no watermark video + audio;\n"
                  "• Pinterest - no watermark video/images + audio;\n\n"
                  "🎵 <b>Music Search (30s preview + Full MP3)</b>\n\n"
                  "⚡️ <b>Shazam features:</b>\n"
                  "• Song name or artist name\n"
                  "• Song lyrics\n"
                  "• Voice message\n"
                  "• Video\n"
                  "• Audio\n"
                  "• Video note\n\n"
                  "🚀 <b>Send the link to the video you want to download!</b>"
        },
        
        "choose_language": {
            "uz": "🌐 Tilni tanlang:",
            "ru": "🌐 Выберите язык:",
            "en": "🌐 Choose language:"
        },
        
        "language_changed": {
            "uz": "✅ Til o'zgartirildi: O'zbek tili",
            "ru": "✅ Язык изменён: Русский",
            "en": "✅ Language changed: English"
        },
        
        "searching": {
            "uz": "🔍 Qidirilmoqda...",
            "ru": "🔍 Ищу...",
            "en": "🔍 Searching..."
        },
        
        "track_not_found": {
            "uz": "😔 Kechirasiz, bu so'rov bo'yicha qo'shiq topa olmadim.\n\n"
                  "Iltimos, boshqa nom bilan urinib ko'ring.",
            "ru": "😔 К сожалению, по этому запросу ничего не нашёл.\n\n"
                  "Попробуйте другое название.",
            "en": "😔 Sorry, I couldn't find a track for this query.\n\n"
                  "Please try another spelling."
        },
        
        "download_error": {
            "uz": "❌ Yuklab olishda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
            "ru": "❌ Ошибка при скачивании. Пожалуйста, попробуйте снова.",
            "en": "❌ Download error occurred. Please try again."
        },
        
        "network_error": {
            "uz": "🌐 Internet aloqasida muammo. Iltimos, keyinroq urinib ko'ring.",
            "ru": "🌐 Проблема с интернет-соединением. Попробуйте позже.",
            "en": "🌐 Network connection problem. Please try later."
        },
        
        "track_caption": {
            "uz": "🎵 {title}\n🎤 {artist}\n⏱ {duration}",
            "ru": "🎵 {title}\n🎤 {artist}\n⏱ {duration}",
            "en": "🎵 {title}\n🎤 {artist}\n⏱ {duration}"
        },
        
        "more_results": {
            "uz": "🔁 Ko'proq",
            "ru": "🔁 Ещё",
            "en": "🔁 More"
        },
        
        "change_language": {
            "uz": "🌐 Til",
            "ru": "🌐 Язык",
            "en": "🌐 Lang"
        },
        
        "no_more_results": {
            "uz": "🔚 Boshqa natijalar yo'q",
            "ru": "🔚 Больше нет результатов",
            "en": "🔚 No more results"
        },
        
        "select_track": {
            "uz": "🎵 Qo'shiqni tanlang:",
            "ru": "🎵 Выберите песню:",
            "en": "🎵 Select a track:"
        },
        
        "inline_description": {
            "uz": "{artist} - {duration}",
            "ru": "{artist} - {duration}",
            "en": "{artist} - {duration}"
        }
    }
    
    LANGUAGES = {
        "uz": "🇺🇿 O'zbek tili",
        "ru": "🇷🇺 Русский",
        "en": "🇬🇧 English"
    }
    
    @classmethod
    def get(cls, key: str, lang: str = "en", **kwargs: Any) -> str:
        """
        Get translated message.
        
        Args:
            key: Message key
            lang: Language code (uz/ru/en)
            **kwargs: Format arguments
        
        Returns:
            Translated and formatted message
        """
        message = cls.TRANSLATIONS.get(key, {}).get(lang, cls.TRANSLATIONS.get(key, {}).get("en", ""))
        
        if kwargs:
            return message.format(**kwargs)
        
        return message
    
    @classmethod
    def get_language_name(cls, lang: str) -> str:
        """Get language display name."""
        return cls.LANGUAGES.get(lang, cls.LANGUAGES["en"])
