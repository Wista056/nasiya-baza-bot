from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import get_pending_users, update_user_status, get_user
from keyboards import approve_user_keyboard, admin_menu, main_menu
import config

router = Router()


@router.message(F.text == "👥 Заявки")
async def pending_list(msg: Message):
    if msg.from_user.id not in config.ADMIN_IDS:
        return
    users = get_pending_users()
    if not users:
        await msg.answer("✅ Нет ожидающих заявок.")
        return
    for u in users:
        text = (
            f"📋 <b>Заявка на регистрацию</b>\n\n"
            f"👤 Имя: {u['full_name']}\n"
            f"📱 Телефон: {u['phone']}\n"
            f"🏢 Компания: {u['company'] or '—'}\n"
            f"🆔 ID: <code>{u['telegram_id']}</code>"
        )
        await msg.answer(text, parse_mode="HTML",
                         reply_markup=approve_user_keyboard(u["telegram_id"]))


@router.callback_query(F.data.startswith("approve:"))
async def approve_user(call: CallbackQuery):
    if call.from_user.id not in config.ADMIN_IDS:
        await call.answer("Нет доступа", show_alert=True)
        return
    user_id = int(call.data.split(":")[1])
    update_user_status(user_id, "approved")
    await call.message.edit_text(call.message.text + "\n\n✅ <b>ОДОБРЕН</b>", parse_mode="HTML")
    await call.answer("Пользователь одобрен!")
    try:
        await call.bot.send_message(
            user_id,
            "🎉 <b>Ваша заявка одобрена!</b>\n\nТеперь вы можете пользоваться всеми функциями бота.",
            parse_mode="HTML", reply_markup=main_menu()
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject:"))
async def reject_user(call: CallbackQuery):
    if call.from_user.id not in config.ADMIN_IDS:
        await call.answer("Нет доступа", show_alert=True)
        return
    user_id = int(call.data.split(":")[1])
    update_user_status(user_id, "rejected")
    await call.message.edit_text(call.message.text + "\n\n❌ <b>ОТКЛОНЁН</b>", parse_mode="HTML")
    await call.answer("Пользователь отклонён.")
    try:
        await call.bot.send_message(
            user_id,
            "❌ <b>Ваша заявка отклонена.</b>\n\nОбратитесь к администратору.",
            parse_mode="HTML"
        )
    except Exception:
        pass
