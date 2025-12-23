"""Handlers for /start command and language selection."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from db import async_session_maker, UserRepository
from services import Localization
from keyboards import get_language_keyboard
from utils import logger


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_or_create_user(user_id)
        
        logger.info(f"User {user_id} started the bot")
        
        # Ask for language selection
        await message.answer(
            text=Localization.get("choose_language", user.language),
            reply_markup=get_language_keyboard()
        )


@router.callback_query(F.data.startswith("lang:"))
async def process_language_selection(callback: CallbackQuery):
    """Handle language selection callback."""
    user_id = callback.from_user.id
    language = callback.data.split(":")[1]
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        await user_repo.update_language(user_id, language)
        
        logger.info(f"User {user_id} selected language: {language}")
    
    # Send welcome message in selected language
    # Send welcome message in selected language
    from config import Config
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        text=Localization.get("welcome", language, bot_username=Config.BOT_USERNAME)
    )
    
    await callback.answer(
        text=Localization.get("language_changed", language)
    )


@router.callback_query(F.data == "change_lang")
async def process_change_language(callback: CallbackQuery):
    """Handle change language button."""
    user_id = callback.from_user.id
    
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_user(user_id)
        
        if not user:
            user = await user_repo.create_user(user_id)
    
    await callback.message.edit_text(
        text=Localization.get("choose_language", user.language),
        reply_markup=get_language_keyboard()
    )
    
    await callback.answer()
