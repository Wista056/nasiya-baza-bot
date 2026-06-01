import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

import config
from database import init_db, get_user, get_user_lang
from keyboards import main_menu, admin_menu
from translations import t
from handlers.registration import lang_keyboard
from handlers import registration, blacklist, products, admin, superadmin

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    is_admin = msg.from_user.id in config.ADMIN_IDS

    if is_admin:
        await msg.answer(
            "👋 <b>Добро пожаловать, администратор!</b>\n\n🤖 Nasiya Baza Bot готов к работе.",
            parse_mode="HTML", reply_markup=admin_menu()
        )
        return

    user = get_user(msg.from_user.id)
    lang = get_user_lang(msg.from_user.id) if user else "ru"

    if user is None:
        await msg.answer(
            "🌐 Выберите язык / Tilni tanlang:",
            reply_markup=lang_keyboard()
        )
    elif user["status"] == "pending":
        await msg.answer(t(lang, "pending"))
    elif user["status"] == "blocked":
        await msg.answer(t(lang, "blocked"))
    elif user["status"] == "rejected":
        await msg.answer(t(lang, "rejected"))
    else:
        await msg.answer(t(lang, "welcome_back", name=user["full_name"]), reply_markup=main_menu())


@dp.message(F.text.in_({"ℹ️ Мой профиль", "ℹ️ Mening profilim"}))
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
    lang = get_user_lang(msg.from_user.id)
    await msg.answer(
        f"👤 <b>{'Mening profilim' if lang == 'uz' else 'Мой профиль'}</b>\n\n"
        f"👤 {'Ism' if lang == 'uz' else 'Имя'}: {user['full_name']}\n"
        f"📱 {'Telefon' if lang == 'uz' else 'Телефон'}: {user['phone']}\n"
        f"🏢 {'Kompaniya' if lang == 'uz' else 'Компания'}: {user['company'] or '—'}\n"
        f"📅 {'Ro'yxatdan o'tgan' if lang == 'uz' else 'Регистрация'}: {user['registered_at'][:10]}",
        parse_mode="HTML"
    )


@dp.message(F.text.in_({"🏠 Главное меню", "🏠 Asosiy menyu"}))
async def go_home(msg: Message, state: FSMContext):
    await state.clear()
    kb = admin_menu() if msg.from_user.id in config.ADMIN_IDS else main_menu()
    lang = get_user_lang(msg.from_user.id)
    await msg.answer(t(lang, "main_menu"), reply_markup=kb)


async def main():
    init_db()
    dp.include_router(registration.router)
    dp.include_router(superadmin.router)
    dp.include_router(admin.router)
    dp.include_router(blacklist.router)
    dp.include_router(products.router)
    print("🤖 Nasiya Baza Bot запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
