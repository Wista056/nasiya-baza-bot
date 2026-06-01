from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from states import RegisterStates
from database import add_user, get_user, get_user_lang, set_user_lang
from keyboards import main_menu, admin_menu, cancel_keyboard
from translations import t
import config

router = Router()


class LangStates(StatesGroup):
    choosing = State()


def lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz"),
        ]
    ])


def phone_keyboard(lang="ru"):
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=t(lang, "send_phone_btn"), request_contact=True)],
        [KeyboardButton(text=t(lang, "cancel_btn"))],
    ], resize_keyboard=True)


@router.message(F.text.in_({"❌ Отмена", "❌ Bekor qilish"}))
async def cancel_handler(msg: Message, state: FSMContext):
    await state.clear()
    user = get_user(msg.from_user.id)
    lang = get_user_lang(msg.from_user.id) if user else "ru"
    is_admin = msg.from_user.id in config.ADMIN_IDS
    if is_admin:
        await msg.answer(t(lang, "cancelled"), reply_markup=admin_menu())
    elif user and user["status"] == "approved":
        await msg.answer(t(lang, "cancelled"), reply_markup=main_menu())
    else:
        await msg.answer(t(lang, "cancelled"))


@router.callback_query(F.data.in_({"lang_ru", "lang_uz"}))
async def choose_lang(call: CallbackQuery, state: FSMContext):
    lang = "ru" if call.data == "lang_ru" else "uz"
    await state.update_data(lang=lang)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await call.message.answer(t(lang, "enter_name"), reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "cancel_btn"))]], resize_keyboard=True
    ))
    await state.set_state(RegisterStates.full_name)


@router.message(RegisterStates.full_name)
async def reg_full_name(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.update_data(full_name=msg.text.strip())
    await msg.answer(t(lang, "enter_phone"), reply_markup=phone_keyboard(lang))
    await state.set_state(RegisterStates.phone)


@router.message(RegisterStates.phone, F.contact)
async def reg_phone_contact(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    phone = msg.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(phone=phone)
    await msg.answer(t(lang, "enter_company"), reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "cancel_btn"))]], resize_keyboard=True
    ))
    await state.set_state(RegisterStates.company)


@router.message(RegisterStates.phone, F.text)
async def reg_phone_text(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.update_data(phone=msg.text.strip())
    await msg.answer(t(lang, "enter_company"), reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "cancel_btn"))]], resize_keyboard=True
    ))
    await state.set_state(RegisterStates.company)


@router.message(RegisterStates.company)
async def reg_company(msg: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    company = msg.text.strip() if msg.text.strip() not in ["-", "—"] else ""
    add_user(msg.from_user.id, data["full_name"], data["phone"], company)
    set_user_lang(msg.from_user.id, lang)
    await state.clear()
    await msg.answer(t(lang, "reg_sent"))

    from keyboards import approve_user_keyboard
    text = (
        f"📋 <b>Новая заявка на регистрацию</b>\n\n"
        f"👤 Имя: {data['full_name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🏢 Компания: {company or '—'}\n"
        f"🌐 Язык: {('🇷🇺 Русский' if lang == 'ru' else '🇺🇿 Ozbek')}\n"
        f"🆔 ID: <code>{msg.from_user.id}</code>"
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await msg.bot.send_message(admin_id, text, parse_mode="HTML",
                                       reply_markup=approve_user_keyboard(msg.from_user.id))
        except Exception:
            pass
