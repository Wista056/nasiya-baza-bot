import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

import config
from database import init_db, get_user
from keyboards import main_menu, admin_menu, cancel

cd ~/nasiya_bot && cat > bot.py << 'EOF'
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

import config
from database import init_db, get_user
from keyboards import main_menu, admin_menu, cancel_keyboard
from states import RegisterStates
from handlers import registration, blacklist, products, admin, superadmin

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def check_access(telegram_id: int) -> bool:
    if telegram_id in config.ADMIN_IDS:
        return True
    user = get_user(telegram_id)
    return user is not None and user["status"] == "approved"


@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    is_admin = msg.from_user.id in config.ADMIN_IDS
    if is_admin:
        await msg.answer(
            "👋 <b>Добро пожаловать, администратор!</b>\n\n"
            "🤖 Nasiya Baza Bot готов к работе.",
            parse_mode="HTML", reply_markup=admin_menu()
        )
        return
    user = get_user(msg.from_user.id)
    if user is None:
        await msg.answer(
            "👋 <b>Добро пожаловать в Nasiya Baza Bot!</b>\n\n"
            "Для доступа пройдите регистрацию.\n\n"
            "👤 Введите ваше полное имя (ФИО):",
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        await state.set_state(RegisterStates.full_name)
    elif user["status"] == "pending":
        await msg.answer("⏳ Ваша заявка ожидает одобрения администратора.")
    elif user["status"] == "blocked":
        await msg.answer("🚫 Ваш аккаунт заблокирован.")
    elif user["status"] == "rejected":
        await msg.answer("❌ Ваша заявка была отклонена.")
    else:
        await msg.answer(f"👋 С возвращением, {user['full_name']}!", reply_markup=main_menu())


@dp.message(F.text == "ℹ️ Мой профиль")
async def my_profile(msg: Message):
    if msg.from_user.id in config.ADMIN_IDS:
        await msg.answer(
            f"👤 <b>Профиль</b>\n\n🆔 ID: <code>{msg.from_user.id}</code>\n🔑 Роль: Администратор",
            parse_mode="HTML"
        )
        return
    user = get_user(msg.from_user.id)
    if not user:
        return
    await msg.answer(
        f"👤 <b>Мой профиль</b>\n\n"
        f"👤 Имя: {user['full_name']}\n"
        f"📱 Телефон: {user['phone']}\n"
        f"🏢 Компания: {user['company'] or '—'}\n"
        f"✅ Статус: Одобрен\n"
        f"📅 Регистрация: {user['registered_at'][:10]}",
        parse_mode="HTML"
    )


@dp.message(F.text == "🏠 Главное меню")
async def go_home(msg: Message, state: FSMContext):
    await state.clear()
    kb = admin_menu() if msg.from_user.id in config.ADMIN_IDS else main_menu()
    await msg.answer("🏠 Главное меню", reply_markup=kb)


async def main():
    init_db()
    dp.include_router(registration.router)
    dp.include_router(superadmin.router)
    dp.include_router(admin.router)
    dp.include_router(blacklist.router)
    dp.include_router(products.router)
    print("🤖 Nasiya Baza Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":    asyncio.run(main())
