"""Advertisement creation and management handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db import async_session_maker, AdRepository, AdType
from handlers.admin import is_admin
from utils import logger


router = Router()


class AdCreationStates(StatesGroup):
    """States for ad creation."""
    waiting_for_type = State()
    waiting_for_text = State()
    waiting_for_photo = State()
    waiting_for_video = State()
    waiting_for_button = State()


@router.message(Command("newad"))
async def cmd_new_ad(message: Message, state: FSMContext):
    """Start ad creation process."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    await message.answer(
        "📢 <b>YANGI REKLAMA YARATISH</b>\n\n"
        "Reklama turini tanlang:\n\n"
        "1️⃣ /ad_text - Matnli reklama\n"
        "2️⃣ /ad_photo - Rasmli reklama\n"
        "3️⃣ /ad_video - Videoli reklama\n\n"
        "Bekor qilish: /cancel"
    )


@router.message(Command("ad_text"))
async def create_text_ad(message: Message, state: FSMContext):
    """Create text advertisement."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    await state.update_data(ad_type="text")
    await state.set_state(AdCreationStates.waiting_for_text)
    
    await message.answer(
        "✍️ Reklama matnini yuboring:\n\n"
        "Misol:\n"
        "🎉 Yangi kanalimizga a'zo bo'ling!\n"
        "@mykanalchannel\n\n"
        "Bekor qilish: /cancel"
    )


@router.message(Command("ad_photo"))
async def create_photo_ad(message: Message, state: FSMContext):
    """Create photo advertisement."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    await state.update_data(ad_type="photo")
    await state.set_state(AdCreationStates.waiting_for_photo)
    
    await message.answer(
        "📸 Rasm yuboring:\n\n"
        "Rasm bilan birga caption ham yozishingiz mumkin.\n\n"
        "Bekor qilish: /cancel"
    )


@router.message(Command("ad_video"))
async def create_video_ad(message: Message, state: FSMContext):
    """Create video advertisement."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    await state.update_data(ad_type="video")
    await state.set_state(AdCreationStates.waiting_for_video)
    
    await message.answer(
        "🎥 Video yuboring:\n\n"
        "Video bilan birga caption ham yozishingiz mumkin.\n\n"
        "Bekor qilish: /cancel"
    )


@router.message(AdCreationStates.waiting_for_text)
async def process_ad_text(message: Message, state: FSMContext):
    """Process ad text."""
    text = message.text
    
    if not text:
        await message.answer("❌ Matn bo'sh bo'lishi mumkin emas!")
        return
    
    await state.update_data(text=text)
    await state.set_state(AdCreationStates.waiting_for_button)
    
    await message.answer(
        "🔘 Tugma qo'shasizmi?\n\n"
        "Tugma qo'shish uchun:\n"
        "<code>Tugma matni | https://link.com</code>\n\n"
        "Tugmasiz saqlash: /skip\n"
        "Bekor qilish: /cancel"
    )


@router.message(AdCreationStates.waiting_for_photo, F.photo)
async def process_ad_photo(message: Message, state: FSMContext):
    """Process ad photo."""
    photo = message.photo[-1]  # Get highest quality
    file_id = photo.file_id
    caption = message.caption or ""
    
    await state.update_data(file_id=file_id, text=caption)
    await state.set_state(AdCreationStates.waiting_for_button)
    
    await message.answer(
        "🔘 Tugma qo'shasizmi?\n\n"
        "Tugma qo'shish uchun:\n"
        "<code>Tugma matni | https://link.com</code>\n\n"
        "Tugmasiz saqlash: /skip\n"
        "Bekor qilish: /cancel"
    )


@router.message(AdCreationStates.waiting_for_video, F.video)
async def process_ad_video(message: Message, state: FSMContext):
    """Process ad video."""
    video = message.video
    file_id = video.file_id
    caption = message.caption or ""
    
    await state.update_data(file_id=file_id, text=caption)
    await state.set_state(AdCreationStates.waiting_for_button)
    
    await message.answer(
        "🔘 Tugma qo'shasizmi?\n\n"
        "Tugma qo'shish uchun:\n"
        "<code>Tugma matni | https://link.com</code>\n\n"
        "Tugmasiz saqlash: /skip\n"
        "Bekor qilish: /cancel"
    )


@router.message(AdCreationStates.waiting_for_button)
async def process_ad_button(message: Message, state: FSMContext):
    """Process ad button."""
    user_id = message.from_user.id
    
    if message.text == "/skip":
        # Save without button
        await save_ad(message, state, None, None)
        return
    
    # Parse button text and URL
    try:
        parts = message.text.split("|")
        if len(parts) != 2:
            await message.answer(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri format:\n"
                "<code>Tugma matni | https://link.com</code>"
            )
            return
        
        button_text = parts[0].strip()
        button_url = parts[1].strip()
        
        if not button_text or not button_url:
            await message.answer("❌ Tugma matni va link bo'sh bo'lishi mumkin emas!")
            return
        
        await save_ad(message, state, button_text, button_url)
        
    except Exception as e:
        logger.error(f"Error parsing button: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


async def save_ad(message: Message, state: FSMContext, button_text, button_url):
    """Save advertisement to database."""
    data = await state.get_data()
    
    async with async_session_maker() as session:
        ad_repo = AdRepository(session)
        
        ad = await ad_repo.create_ad(
            ad_type=data.get("ad_type", "text"),
            text=data.get("text"),
            file_id=data.get("file_id"),
            button_text=button_text,
            button_url=button_url,
            show_after_tracks=5
        )
        
        await message.answer(
            f"✅ <b>Reklama saqlandi!</b>\n\n"
            f"ID: {ad.id}\n"
            f"Turi: {ad.ad_type}\n"
            f"Holat: Faol\n\n"
            f"Reklamani boshqarish: /admin"
        )
        
        logger.info(f"New ad created: ID {ad.id} by user {message.from_user.id}")
    
    await state.clear()


@router.message(Command("cancel"))
async def cancel_ad_creation(message: Message, state: FSMContext):
    """Cancel ad creation."""
    await state.clear()
    await message.answer("❌ Reklama yaratish bekor qilindi.")


@router.message(Command("togglead"))
async def toggle_ad(message: Message):
    """Toggle ad active status."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    try:
        # Parse command: /togglead 123
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri: /togglead [ad_id]\n"
                "Misol: /togglead 1"
            )
            return
        
        ad_id = int(parts[1])
        
        async with async_session_maker() as session:
            ad_repo = AdRepository(session)
            ad = await ad_repo.get_ad(ad_id)
            
            if not ad:
                await message.answer(f"❌ ID {ad_id} reklama topilmadi!")
                return
            
            # Toggle status
            new_status = not ad.is_active
            await ad_repo.update_ad(ad_id, is_active=new_status)
            
            status_text = "✅ Faollashtirildi" if new_status else "❌ O'chirildi"
            await message.answer(
                f"{status_text}\n\n"
                f"Reklama ID: {ad_id}"
            )
            
    except ValueError:
        await message.answer("❌ ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Error toggling ad: {e}")
        await message.answer("❌ Xatolik yuz berdi!")


@router.message(Command("deletead"))
async def delete_ad(message: Message):
    """Delete advertisement."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    try:
        # Parse command: /deletead 123
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer(
                "❌ Noto'g'ri format!\n\n"
                "To'g'ri: /deletead [ad_id]\n"
                "Misol: /deletead 1"
            )
            return
        
        ad_id = int(parts[1])
        
        async with async_session_maker() as session:
            ad_repo = AdRepository(session)
            success = await ad_repo.delete_ad(ad_id)
            
            if success:
                await message.answer(f"✅ Reklama ID {ad_id} o'chirildi!")
            else:
                await message.answer(f"❌ ID {ad_id} reklama topilmadi!")
                
    except ValueError:
        await message.answer("❌ ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Error deleting ad: {e}")
        await message.answer("❌ Xatolik yuz berdi!")
