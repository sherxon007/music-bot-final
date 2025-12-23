"""Admin panel handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from db import (
    async_session_maker, AdminRepository, StatisticsRepository,
    AdRepository, UserRepository, AdType
)
from config import Config
from utils import logger


router = Router()



async def is_super_admin(user_id: int) -> bool:
    """Check if user is super admin."""
    # Check config first
    if user_id in Config.SUPER_ADMIN_IDS:
        return True
    
    # Check DB
    async with async_session_maker() as session:
        admin_repo = AdminRepository(session)
        return await admin_repo.is_super_admin(user_id)


async def is_admin(user_id: int) -> bool:
    """Check if user is admin (super or regular)."""
    # Check config (super admins are admins)
    if user_id in Config.SUPER_ADMIN_IDS:
        return True
    
    # Check DB
    async with async_session_maker() as session:
        admin_repo = AdminRepository(session)
        return await admin_repo.is_admin(user_id)

def get_admin_keyboard(is_super: bool = False) -> InlineKeyboardMarkup:
    """Get main admin panel keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats"),
            InlineKeyboardButton(text="📢 Reklamalar", callback_data="admin:ads")
        ],
        # Admin management only for Super Admins
        ([InlineKeyboardButton(text="👥 Adminlar", callback_data="admin:admins")] if is_super else []),
        [
            InlineKeyboardButton(text="📨 Xabar yuborish", callback_data="admin:broadcast"),
             InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin:refresh")
        ]
    ]
    # Remove empty lists if any
    keyboard = [row for row in keyboard if row]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("addadmin"))
async def cmd_add_admin(message: Message):
    """Add new admin (Super Admin only)."""
    user_id = message.from_user.id
    if not await is_super_admin(user_id):
        await message.answer("❌ Bu komanda faqat Super Adminlar uchun!")
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ ID kiritilmadi!\nFormat: `/addadmin 123456789`")
            return
            
        new_admin_id = int(args[1])
        
        async with async_session_maker() as session:
            admin_repo = AdminRepository(session)
            if await admin_repo.is_admin(new_admin_id):
                await message.answer("⚠️ Bu foydalanuvchi allaqachon admin!")
                return
            
            await admin_repo.add_admin(new_admin_id, username="Added via Command")
            await message.answer(f"✅ Yangi admin qo'shildi: `{new_admin_id}`")
            
    except ValueError:
        await message.answer("❌ ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        await message.answer("❌ Xatolik yuz berdi.")

@router.message(Command("deladmin"))
async def cmd_del_admin(message: Message):
    """Remove admin (Super Admin only)."""
    user_id = message.from_user.id
    if not await is_super_admin(user_id):
        await message.answer("❌ Bu komanda faqat Super Adminlar uchun!")
        return
    
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ ID kiritilmadi!\nFormat: `/deladmin 123456789`")
            return
            
        target_id = int(args[1])
        
        # Don't allow removing self or config super admins
        if target_id == user_id or target_id in Config.SUPER_ADMIN_IDS:
             await message.answer("❌ Super adminni o'chirish mumkin emas!")
             return

        async with async_session_maker() as session:
            admin_repo = AdminRepository(session)
            if await admin_repo.remove_admin(target_id):
                await message.answer(f"✅ Admin o'chirildi: `{target_id}`")
            else:
                await message.answer("❌ Bunday admin topilmadi.")
            
    except ValueError:
        await message.answer("❌ ID raqam bo'lishi kerak!")
    except Exception as e:
        logger.error(f"Error removing admin: {e}")
        await message.answer("❌ Xatolik yuz berdi.")

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    is_super = await is_super_admin(user_id)
    
    async with async_session_maker() as session:
        stats_repo = StatisticsRepository(session)
        total_users = await stats_repo.get_total_users()
        active_today = await stats_repo.get_active_users_today()
        searches_today = await stats_repo.get_searches_today()
        
        text = f"""
👨‍💼 <b>ADMIN PANEL</b>

📊 <b>Tezkor statistika:</b>
👥 Jami foydalanuvchilar: {total_users}
✅ Bugun faollar: {active_today}
🔍 Bugun qidiruvlar: {searches_today}

Adminlar uchun komandalar:
/broadcast - Xabar yuborish
{'/addadmin [id] - Admin qo\'shish' if is_super else ''}
{'/deladmin [id] - Admin o\'chirish' if is_super else ''}

Kerakli bo'limni tanlang:
        """
    
    await message.answer(
        text=text.strip(),
        reply_markup=get_admin_keyboard(is_super)
    )

@router.callback_query(F.data == "admin:main")
async def admin_main(callback: CallbackQuery):
    """Return to main admin panel."""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ Ruxsat yo'q!")
        return
    
    is_super = await is_super_admin(user_id)
    
    async with async_session_maker() as session:
        stats_repo = StatisticsRepository(session)
        total_users = await stats_repo.get_total_users()
        active_today = await stats_repo.get_active_users_today()
        searches_today = await stats_repo.get_searches_today()
        
        text = f"""
👨‍💼 <b>ADMIN PANEL</b>

📊 <b>Tezkor statistika:</b>
👥 Jami foydalanuvchilar: {total_users}
✅ Bugun faollar: {active_today}
🔍 Bugun qidiruvlar: {searches_today}

Kerakli bo'limni tanlang:
        """
    
    await callback.message.edit_text(
        text=text.strip(),
        reply_markup=get_admin_keyboard(is_super)
    )
    await callback.answer()
# ... (rest of the file as before, just need to make sure admin_admin* handlers check is_super)


def get_ads_keyboard() -> InlineKeyboardMarkup:
    """Get ads management keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Yangi reklama", callback_data="admin:ad:new"),
            InlineKeyboardButton(text="📋 Barcha reklamalar", callback_data="admin:ad:list")
        ],
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admins_keyboard() -> InlineKeyboardMarkup:
    """Get admins management keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="admin:admin:add"),
            InlineKeyboardButton(text="📋 Barcha adminlar", callback_data="admin:admin:list")
        ],
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    async with async_session_maker() as session:
        stats_repo = StatisticsRepository(session)
        user_repo = UserRepository(session)
        
        total_users = await stats_repo.get_total_users()
        active_today = await stats_repo.get_active_users_today()
        searches_today = await stats_repo.get_searches_today()
        
        text = f"""
👨‍💼 <b>ADMIN PANEL</b>

📊 <b>Tezkor statistika:</b>
👥 Jami foydalanuvchilar: {total_users}
✅ Bugun faollar: {active_today}
🔍 Bugun qidiruvlar: {searches_today}

Kerakli bo'limni tanlang:
        """
    
    await message.answer(
        text=text.strip(),
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin:main")
async def admin_main(callback: CallbackQuery):
    """Return to main admin panel."""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ Ruxsat yo'q!")
        return
    
    async with async_session_maker() as session:
        stats_repo = StatisticsRepository(session)
        
        total_users = await stats_repo.get_total_users()
        active_today = await stats_repo.get_active_users_today()
        searches_today = await stats_repo.get_searches_today()
        
        text = f"""
👨‍💼 <b>ADMIN PANEL</b>

📊 <b>Tezkor statistika:</b>
👥 Jami foydalanuvchilar: {total_users}
✅ Bugun faollar: {active_today}
🔍 Bugun qidiruvlar: {searches_today}

Kerakli bo'limni tanlang:
        """
    
    from aiogram.exceptions import TelegramBadRequest
    
    try:
        await callback.message.edit_text(
            text=text.strip(),
            reply_markup=get_admin_keyboard()
        )
    except TelegramBadRequest:
        # Ignore if text is not modified
        pass
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_statistics(callback: CallbackQuery):
    """Show detailed statistics."""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ Ruxsat yo'q!")
        return
    
    async with async_session_maker() as session:
        stats_repo = StatisticsRepository(session)
        ad_repo = AdRepository(session)
        
        # Get statistics
        total_users = await stats_repo.get_total_users()
        active_today = await stats_repo.get_active_users_today()
        active_week = await stats_repo.get_active_users_week()
        new_today = await stats_repo.get_new_users_today()
        new_week = await stats_repo.get_new_users_week()
        
        total_searches = await stats_repo.get_total_searches()
        total_downloads = await stats_repo.get_total_downloads()
        searches_today = await stats_repo.get_searches_today()
        downloads_today = await stats_repo.get_downloads_today()
        
        # Language distribution
        lang_dist = await stats_repo.get_language_distribution()
        lang_text = "\n".join([
            f"  • {item['language'].upper()}: {item['count']}"
            for item in lang_dist
        ])
        
        # Top queries
        top_queries = await stats_repo.get_top_queries(5)
        queries_text = "\n".join([
            f"  {i+1}. {item['query']} ({item['count']})"
            for i, item in enumerate(top_queries)
        ])
        
        # Ad statistics
        active_ads = await ad_repo.get_active_ads()
        total_impressions = sum(ad.impressions for ad in active_ads)
        total_clicks = sum(ad.clicks for ad in active_ads)
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        
        text = f"""
📊 <b>BATAFSIL STATISTIKA</b>

👥 <b>Foydalanuvchilar:</b>
  • Jami: {total_users}
  • Bugun faollar: {active_today}
  • Hafta faollar: {active_week}
  • Bugun yangilar: {new_today}
  • Hafta yangilar: {new_week}

🔍 <b>Qidiruvlar:</b>
  • Jami: {total_searches}
  • Bugun: {searches_today}
  • Yuklanishlar: {total_downloads}

🌐 <b>Tillar bo'yicha:</b>
{lang_text}

🔥 <b>Top 5 qidiruvlar:</b>
{queries_text if queries_text else "  Ma'lumot yo'q"}

📢 <b>Reklamalar:</b>
  • Faol: {len(active_ads)}
  • Ko'rishlar: {total_impressions}
  • Kliklar: {total_clicks}
  • CTR: {ctr:.2f}%
        """
    
    keyboard = [[InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")]]
    
    await callback.message.edit_text(
        text=text.strip(),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:ads")
async def admin_ads_menu(callback: CallbackQuery):
    """Show ads management menu."""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ Ruxsat yo'q!")
        return
    
    async with async_session_maker() as session:
        ad_repo = AdRepository(session)
        active_ads = await ad_repo.get_active_ads()
        all_ads = await ad_repo.get_all_ads()
    
    text = f"""
📢 <b>REKLAMA BOSHQARUVI</b>

📊 <b>Statistika:</b>
  • Jami reklamalar: {len(all_ads)}
  • Faol: {len(active_ads)}
  • O'chirilgan: {len(all_ads) - len(active_ads)}

Kerakli harakatni tanlang:
    """
    
    await callback.message.edit_text(
        text=text.strip(),
        reply_markup=get_ads_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:ad:list")
async def admin_ads_list(callback: CallbackQuery):
    """Show all advertisements."""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ Ruxsat yo'q!")
        return
    
    async with async_session_maker() as session:
        ad_repo = AdRepository(session)
        ads = await ad_repo.get_all_ads()
    
    if not ads:
        text = "📢 Hozircha reklamalar yo'q."
    else:
        text = "📢 <b>BARCHA REKLAMALAR:</b>\n\n"
        
        for ad in ads:
            status = "✅ Faol" if ad.is_active else "❌ O'chirilgan"
            ctr = (ad.clicks / ad.impressions * 100) if ad.impressions > 0 else 0
            
            text += f"""
<b>ID:</b> {ad.id}
<b>Turi:</b> {ad.ad_type}
<b>Holat:</b> {status}
<b>Ko'rishlar:</b> {ad.impressions}
<b>Kliklar:</b> {ad.clicks}
<b>CTR:</b> {ctr:.2f}%
<b>Matn:</b> {ad.text[:50] if ad.text else 'Yo\'q'}...
{'━' * 30}
            """
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:ads")]
    ]
    
    await callback.message.edit_text(
        text=text.strip(),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:admins")
async def admin_admins_menu(callback: CallbackQuery):
    """Show admins management menu."""
    user_id = callback.from_user.id
    
    if not await is_super_admin(user_id):
        await callback.answer("❌ Bu bo'lim faqat Super Adminlar uchun!", show_alert=True)
        return
    
    text = """
👥 <b>ADMINLAR BOSHQARUVI</b>

Admin qo'shish yoki ro'yxatni ko'rish uchun tugmani tanlang:
    """
    
    await callback.message.edit_text(
        text=text.strip(),
        reply_markup=get_admins_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin:admin:list")
async def admin_admins_list(callback: CallbackQuery):
    """Show all admins."""
    user_id = callback.from_user.id
    
    if not await is_super_admin(user_id):
        await callback.answer("❌ Bu bo'lim faqat Super Adminlar uchun!", show_alert=True)
        return
    
    async with async_session_maker() as session:
        admin_repo = AdminRepository(session)
        admins = await admin_repo.get_all_admins()
    
    text = "👥 <b>BARCHA ADMINLAR:</b>\n\n"
    
    # Add super admins from config
    text += "<b>Super Adminlar:</b>\n"
    for admin_id in Config.SUPER_ADMIN_IDS:
        text += f"  • ID: {admin_id}\n"
    
    if admins:
        text += "\n<b>Oddiy Adminlar:</b>\n"
        for admin in admins:
            role = "🔑 Super" if admin.is_super_admin else "👤 Oddiy"
            username = f"@{admin.username}" if admin.username else "Username yo'q"
            text += f"  • {role} - ID: {admin.id} ({username})\n"
    else:
        text += "\n<i>Hozircha oddiy adminlar yo'q</i>"
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:admins")]
    ]
    
    await callback.message.edit_text(
        text=text.strip(),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_menu(callback: CallbackQuery):
    """Show broadcast menu."""
    user_id = callback.from_user.id
    
    if not await is_admin(user_id):
        await callback.answer("❌ Ruxsat yo'q!")
        return
    
    text = """
📨 <b>XABAR YUBORISH</b>

Barcha foydalanuvchilarga xabar yuborish uchun:

1️⃣ Xabaringizni yozing
2️⃣ /broadcast [xabar] formatida yuboring

Misol:
/broadcast Yangilanish! Endi botda yangi imkoniyatlar mavjud! 🎉
    """
    
    keyboard = [
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin:main")]
    ]
    
    await callback.message.edit_text(
        text=text.strip(),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "admin:refresh")
async def admin_refresh(callback: CallbackQuery):
    """Refresh admin panel."""
    await admin_main(callback)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Broadcast message to all users."""
    user_id = message.from_user.id
    
    if not await is_admin(user_id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    # Get message text
    text = message.text.replace("/broadcast", "").strip()
    
    # Validation: Must have text OR be a reply
    if not text and not message.reply_to_message:
        await message.answer(
            "❌ Xatolik! Xabar yuborish uchun matn yozing yoki biror xabarga (rasm/video) reply qiling.\n\n"
            "Misol: <code>/broadcast Salom hammaga!</code>"
        )
        return
    
    # Get all users
    async with async_session_maker() as session:
        from db.user import User
        from sqlalchemy import select
        
        result = await session.execute(select(User))
        users = result.scalars().all()
    
    # Send broadcast
    sent = 0
    failed = 0
    
    status_msg = await message.answer(f"📨 Xabar yuborilmoqda...\n\n0/{len(users)}")
    
    for i, user in enumerate(users):
        try:
             # If replying to a message -> Copy it
            if message.reply_to_message:
                await message.reply_to_message.copy_to(chat_id=user.id)
            # Else -> Send text
            elif text:
                await message.bot.send_message(user.id, text)
            else:
                 # No content found
                break

            sent += 1
        except Exception as e:
            failed += 1
            # Don't log every error to avoid flooding logs
            if failed < 5: 
                logger.error(f"Broadcast error for user {user.id}: {e}")
        
        # Update status every 10 users
        if (i + 1) % 10 == 0:
             try:
                await status_msg.edit_text(
                    f"📨 Xabar yuborilmoqda...\n\n{i+1}/{len(users)}"
                )
             except: pass
    
    # Final status
    await status_msg.edit_text(
        f"✅ <b>Yuborish tugadi!</b>\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Xatolik: {failed}"
    )
    
    logger.info(f"Broadcast completed: {sent} sent, {failed} failed")
