from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from states import RegisterStates
from database import add_user, get_user
from keyboards import cancel_keyboard, main_menu, admin_menu
import config

router = Router()


def phone_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Отправить мой номер", request_contact=True)],
        [KeyboardButton(text="❌ Отмена")],
    ], resize_keyboard=True)


@router.message(F.text == "❌ Отмена")
async def cancel_handler(msg: Message, state: FSMContext):
    await state.clear()
    user = get_user(msg.from_user.id)
    is_admin = msg.from_user.id in config.ADMIN_IDS
    if is_admin:
        await msg.answer("Действие отменено.", reply_markup=admin_menu())
    elif user and user["status"] == "approved":
        await msg.answer("Действие отменено.", reply_markup=main_menu())
    else:
        await msg.answer("Действие отменено.")


@router.message(RegisterStates.full_name)
async def reg_full_name(msg: Message, state: FSMContext):
    await state.update_data(full_name=msg.text.strip())
    await msg.answer(
        "📱 Отправьте ваш номер телефона кнопкой ниже:",
        reply_markup=phone_keyboard()
    )
    await state.set_state(RegisterStates.phone)


@router.message(RegisterStates.phone, F.contact)
async def reg_phone_contact(msg: Message, state: FSMContext):
    phone = msg.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(phone=phone)
    await msg.answer("🏢 Введите название компании (или '-' если нет):", reply_markup=cancel_keyboard())
    await state.set_state(RegisterStates.company)


@router.message(RegisterStates.phone, F.text)
async def reg_phone_text(msg: Message, state: FSMContext):
    await state.update_data(phone=msg.text.strip())
    await msg.answer("🏢 Введите название компании (или '-' если нет):", reply_markup=cancel_keyboard())
    await state.set_state(RegisterStates.company)


@router.message(RegisterStates.company)
async def reg_company(msg: Message, state: FSMContext):
    data = await state.get_data()
    company = msg.text.strip() if msg.text.strip() != "-" else ""
    add_user(msg.from_user.id, data["full_name"], data["phone"], company)
    await state.clear()

    await msg.answer(
        "✅ Заявка отправлена!\n\n"
        "Ожидайте одобрения от администратора."
    )

    from keyboards import approve_user_keyboard
    text = (
        f"📋 <b>Новая заявка на регистрацию</b>\n\n"
        f"👤 Имя: {data['full_name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🏢 Компания: {company or '—'}\n"
        f"🆔 ID: <code>{msg.from_user.id}</code>"
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await msg.bot.send_message(admin_id, text, parse_mode="HTML",
                                       reply_markup=approve_user_keyboard(msg.from_user.id))
        except Exception:
            pass
