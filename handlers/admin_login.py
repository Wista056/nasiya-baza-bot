from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

ADMIN_PASSWORD = "taqseet2026"
authorized_admins = set()

router = Router()


class AdminLoginStates(StatesGroup):
    waiting_password = State()


@router.message(Command("admin"))
async def admin_cmd(msg: Message, state: FSMContext):
    if msg.from_user.id in authorized_admins:
        from handlers.superadmin import super_menu
        await msg.answer("👑 <b>Панель супер-администратора</b>", parse_mode="HTML", reply_markup=super_menu())
        return
    await msg.answer("🔐 Введите пароль для входа:")
    await state.set_state(AdminLoginStates.waiting_password)


@router.message(AdminLoginStates.waiting_password)
async def check_password(msg: Message, state: FSMContext):
    await state.clear()
    if msg.text.strip() == ADMIN_PASSWORD:
        authorized_admins.add(msg.from_user.id)
        from handlers.superadmin import super_menu
        await msg.answer("✅ <b>Доступ разрешён!</b>", parse_mode="HTML", reply_markup=super_menu())
    else:
        await msg.answer("❌ Неверный пароль!")
