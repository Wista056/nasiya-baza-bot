from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states import BlacklistManualStates, BlacklistPassportStates, BlacklistSearchStates
from database import add_to_blacklist, search_blacklist, get_user
from keyboards import (blacklist_menu, blacklist_add_method,
                       cancel_keyboard, confirm_passport_keyboard)
from ai_passport import extract_passport_data
from notifications import notify_blacklist

router = Router()


def get_user_info(telegram_id):
    user = get_user(telegram_id)
    if user:
        return user["full_name"], user["company"] or "", user["phone"]
    return "", "", ""


def is_allowed(telegram_id):
    import config
    if telegram_id in config.ADMIN_IDS:
        return True
    user = get_user(telegram_id)
    return user is not None and user["status"] == "approved"


def photo_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📷 Да, прикрепить фото", callback_data="bl_add_photo"),
            InlineKeyboardButton(text="✅ Нет, сохранить", callback_data="bl_save_no_photo"),
        ]
    ])


def final_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="bl_confirm_save"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="bl_cancel_save"),
        ]
    ])


@router.message(F.text == "🚫 Чёрный список")
async def blacklist_main(msg: Message):
    if not is_allowed(msg.from_user.id):
        await msg.answer("❌ Нет доступа.")
        return
    await msg.answer("🚫 <b>Чёрный список</b>\n\nВыберите действие:",
                     reply_markup=blacklist_menu(), parse_mode="HTML")


@router.message(F.text == "➕ Добавить в ЧС")
async def bl_add_choose(msg: Message):
    if not is_allowed(msg.from_user.id):
        return
    await msg.answer("Как хотите добавить клиента?", reply_markup=blacklist_add_method())


# ══════════ РУЧНОЙ ВВОД ══════════

@router.message(F.text == "✍️ Ввести вручную")
async def bl_manual_start(msg: Message, state: FSMContext):
    if not is_allowed(msg.from_user.id):
        return
    await msg.answer("👤 Введите <b>ФИО</b> клиента:", parse_mode="HTML", reply_markup=cancel_keyboard())
    await state.set_state(BlacklistManualStates.full_name)


@router.message(BlacklistManualStates.full_name)
async def bl_m_name(msg: Message, state: FSMContext):
    await state.update_data(full_name=msg.text.strip())
    await msg.answer("📅 Дата рождения (ДД.ММ.ГГГГ) или '-':")
    await state.set_state(BlacklistManualStates.birth_date)


@router.message(BlacklistManualStates.birth_date)
async def bl_m_birth(msg: Message, state: FSMContext):
    val = msg.text.strip()
    await state.update_data(birth_date="" if val == "-" else val)
    await msg.answer("📄 Номер паспорта или '-':")
    await state.set_state(BlacklistManualStates.passport_number)


@router.message(BlacklistManualStates.passport_number)
async def bl_m_passport(msg: Message, state: FSMContext):
    val = msg.text.strip()
    await state.update_data(passport_number="" if val == "-" else val)
    await msg.answer("🔢 <b>ПИНФЛ</b> (14 цифр) — обязательно:", parse_mode="HTML")
    await state.set_state(BlacklistManualStates.pinfl)


@router.message(BlacklistManualStates.pinfl)
async def bl_m_pinfl(msg: Message, state: FSMContext):
    val = msg.text.strip()
    if val == "-" or len(val) < 5:
        await msg.answer("⚠️ ПИНФЛ обязателен! Введите ПИНФЛ (14 цифр):")
        return
    await state.update_data(pinfl=val)
    await msg.answer("🏠 Адрес прописки или '-':")
    await state.set_state(BlacklistManualStates.address)


@router.message(BlacklistManualStates.address)
async def bl_m_address(msg: Message, state: FSMContext):
    val = msg.text.strip()
    await state.update_data(address="" if val == "-" else val)
    await msg.answer("📱 Номер телефона клиента или '-':")
    await state.set_state(BlacklistManualStates.phone)


@router.message(BlacklistManualStates.phone)
async def bl_m_phone(msg: Message, state: FSMContext):
    val = msg.text.strip()
    await state.update_data(phone="" if val == "-" else val)
    await msg.answer("📝 Причина добавления в чёрный список:")
    await state.set_state(BlacklistManualStates.reason)


@router.message(BlacklistManualStates.reason)
async def bl_m_reason(msg: Message, state: FSMContext):
    data = await state.get_data()
    data["reason"] = msg.text.strip()
    await state.update_data(reason=msg.text.strip())

    # Показываем итог и спрашиваем про фото
    text = (
        f"📋 <b>Проверьте данные:</b>\n\n"
        f"👤 ФИО: <b>{data['full_name']}</b>\n"
        f"📅 Дата рождения: {data.get('birth_date') or '—'}\n"
        f"📄 Паспорт: {data.get('passport_number') or '—'}\n"
        f"🔢 ПИНФЛ: {data.get('pinfl')}\n"
        f"🏠 Адрес: {data.get('address') or '—'}\n"
        f"📱 Телефон: {data.get('phone') or '—'}\n"
        f"📝 Причина: {msg.text.strip()}\n\n"
        f"📷 Прикрепить фото паспорта?"
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=photo_confirm_keyboard())
    await state.set_state(BlacklistManualStates.confirm)


@router.callback_query(F.data == "bl_add_photo", BlacklistManualStates.confirm)
async def bl_ask_photo(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await call.message.answer("📷 Отправьте фото паспорта:", reply_markup=cancel_keyboard())
    await state.set_state(BlacklistManualStates.photo)


@router.message(BlacklistManualStates.photo, F.photo)
async def bl_m_photo(msg: Message, state: FSMContext):
    photo = msg.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    data = await state.get_data()

    text = (
        f"✅ <b>Фото получено! Подтвердите сохранение:</b>\n\n"
        f"👤 {data['full_name']}\n"
        f"🔢 ПИНФЛ: {data['pinfl']}\n"
        f"📝 Причина: {data['reason']}"
    )
    await msg.answer_photo(photo.file_id, caption=text, parse_mode="HTML",
                           reply_markup=final_confirm_keyboard())


@router.callback_query(F.data == "bl_save_no_photo", BlacklistManualStates.confirm)
async def bl_save_no_photo(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    data = await state.get_data()
    text = (
        f"✅ <b>Подтвердите сохранение без фото:</b>\n\n"
        f"👤 {data['full_name']}\n"
        f"🔢 ПИНФЛ: {data['pinfl']}\n"
        f"📝 Причина: {data['reason']}"
    )
    await call.message.answer(text, parse_mode="HTML", reply_markup=final_confirm_keyboard())


@router.callback_query(F.data == "bl_confirm_save")
async def bl_confirm_save(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    data = await state.get_data()
    await state.clear()

    name, company, phone = get_user_info(call.from_user.id)
    add_to_blacklist(
        full_name=data["full_name"],
        phone=data.get("phone", ""),
        reason=data["reason"],
        added_by_telegram_id=call.from_user.id,
        birth_date=data.get("birth_date", ""),
        passport_number=data.get("passport_number", ""),
        pinfl=data.get("pinfl", ""),
        address=data.get("address", ""),
        added_by_name=name,
        added_by_company=company,
        added_by_phone=phone,
    )

    await call.message.answer(
        f"✅ <b>Клиент добавлен в чёрный список</b>",
        parse_mode="HTML", reply_markup=blacklist_menu()
    )

    # Отправляем в канал
    photo_file_id = data.get("photo_file_id")
    import config
    caption = (
        f"🚨 <b>Новая запись в ЧС!</b>\n\n"
        f"👤 {data['full_name']}\n"
        f"📅 {data.get('birth_date') or '—'}\n"
        f"📄 {data.get('passport_number') or '—'}\n"
        f"🔢 {data['pinfl']}\n"
        f"🏠 {data.get('address') or '—'}\n"
        f"📱 {data.get('phone') or '—'}\n"
        f"📝 {data['reason']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏢 {company or '—'} / {name}"
    )
    try:
        if photo_file_id:
            await call.bot.send_photo(config.CHANNEL_ID, photo_file_id, caption=caption, parse_mode="HTML")
        else:
            await call.bot.send_message(config.CHANNEL_ID, caption, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка отправки в канал: {e}")


@router.callback_query(F.data == "bl_cancel_save")
async def bl_cancel_save(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await state.clear()
    await call.message.answer("❌ Отменено.", reply_markup=blacklist_menu())


# ══════════ ПАСПОРТ + ИИ ══════════

@router.message(F.text == "📷 Сканировать паспорт")
async def bl_passport_start(msg: Message, state: FSMContext):
    if not is_allowed(msg.from_user.id):
        return
    await msg.answer(
        "📷 Отправьте <b>фото паспорта</b> клиента.\n\nИИ автоматически извлечёт все данные.",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.set_state(BlacklistPassportStates.photo)


@router.message(BlacklistPassportStates.photo, F.photo)
async def bl_passport_photo(msg: Message, state: FSMContext):
    await msg.answer("⏳ Анализирую паспорт...")
    photo = msg.photo[-1]
    file_id = photo.file_id
    file = await msg.bot.get_file(photo.file_id)
    photo_bytes = await msg.bot.download_file(file.file_path)
    try:
        data = await extract_passport_data(photo_bytes.read())
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}")
        await state.clear()
        return
    data["photo_file_id"] = file_id
    await state.update_data(passport_data=data)
    text = (
        f"📋 <b>Данные из паспорта:</b>\n\n"
        f"👤 ФИО: <b>{data.get('full_name') or '—'}</b>\n"
        f"📅 Дата рождения: {data.get('birth_date') or '—'}\n"
        f"📄 Паспорт: {data.get('passport_number') or '—'}\n"
        f"🔢 ПИНФЛ: {data.get('pinfl') or '—'}\n"
        f"🏠 Адрес: {data.get('address') or '—'}\n\nДанные верны?"
    )
    await msg.answer_photo(file_id, caption=text, parse_mode="HTML",
                           reply_markup=confirm_passport_keyboard())
    await state.set_state(BlacklistPassportStates.confirm)


@router.callback_query(F.data == "passport_ok", BlacklistPassportStates.confirm)
async def bl_passport_confirmed(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await call.message.answer("📱 Введите номер телефона клиента (или '-'):",
                              reply_markup=cancel_keyboard())
    await state.set_state(BlacklistPassportStates.phone)


@router.callback_query(F.data == "passport_edit", BlacklistPassportStates.confirm)
async def bl_passport_edit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    passport_data = data.get("passport_data", {})
    # Сохраняем photo_file_id чтобы не слетело
    await state.update_data(passport_data=passport_data)
    await call.message.answer(
        "📷 Отправьте новое фото паспорта:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(BlacklistPassportStates.photo)


@router.message(BlacklistPassportStates.phone)
async def bl_passport_phone(msg: Message, state: FSMContext):
    val = msg.text.strip()
    await state.update_data(phone="" if val == "-" else val)
    await msg.answer("📝 Укажите причину добавления:")
    await state.set_state(BlacklistPassportStates.reason)


@router.message(BlacklistPassportStates.reason)
async def bl_passport_reason(msg: Message, state: FSMContext):
    data = await state.get_data()
    passport_data = data.get("passport_data", {})
    reason = msg.text.strip()
    await state.clear()

    name, company, user_phone = get_user_info(msg.from_user.id)
    add_to_blacklist(
        full_name=passport_data.get("full_name", ""),
        phone=data.get("phone", ""),
        reason=reason,
        added_by_telegram_id=msg.from_user.id,
        birth_date=passport_data.get("birth_date", ""),
        passport_number=passport_data.get("passport_number", ""),
        pinfl=passport_data.get("pinfl", ""),
        address=passport_data.get("address", ""),
        added_by_name=name,
        added_by_company=company,
        added_by_phone=user_phone,
    )

    await msg.answer(
        f"✅ <b>Клиент добавлен в чёрный список</b>\n\n"
        f"👤 {passport_data.get('full_name') or '—'}\n"
        f"📄 Паспорт: {passport_data.get('passport_number') or '—'}\n"
        f"📝 Причина: {reason}\n"
        f"🏢 Добавил: {company or name}",
        parse_mode="HTML", reply_markup=blacklist_menu()
    )

    # Отправляем фото паспорта в канал
    photo_file_id = passport_data.get("photo_file_id")
    import config
    caption = (
        f"🚨 <b>Новая запись в ЧС!</b>\n\n"
        f"👤 {passport_data.get('full_name') or '—'}\n"
        f"📅 {passport_data.get('birth_date') or '—'}\n"
        f"📄 {passport_data.get('passport_number') or '—'}\n"
        f"🔢 {passport_data.get('pinfl') or '—'}\n"
        f"🏠 {passport_data.get('address') or '—'}\n"
        f"📱 {data.get('phone', '') or '—'}\n"
        f"📝 {reason}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏢 {company or '—'} / {name}"
    )
    try:
        if photo_file_id:
            await msg.bot.send_photo(config.CHANNEL_ID, photo_file_id, caption=caption, parse_mode="HTML")
        else:
            await msg.bot.send_message(config.CHANNEL_ID, caption, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка: {e}")


# ══════════ ПОИСК ══════════

@router.message(F.text == "🔍 Проверить по ЧС")
async def bl_search_start(msg: Message, state: FSMContext):
    if not is_allowed(msg.from_user.id):
        return
    await msg.answer("🔍 Введите ФИО, телефон, номер паспорта или ПИНФЛ:",
                     reply_markup=cancel_keyboard())
    await state.set_state(BlacklistSearchStates.query)


@router.message(BlacklistSearchStates.query)
async def bl_search_do(msg: Message, state: FSMContext):
    await state.clear()
    results = search_blacklist(msg.text.strip())
    if not results:
        await msg.answer("✅ <b>Клиент не найден в чёрном списке</b>",
                         parse_mode="HTML", reply_markup=blacklist_menu())
        return
    text = f"🚫 <b>Найдено в чёрном списке: {len(results)}</b>\n\n"
    for r in results:
        text += (
            f"👤 <b>{r['full_name']}</b>\n"
            f"📅 {r['birth_date'] or '—'}\n"
            f"📄 {r['passport_number'] or '—'}\n"
            f"🔢 {r['pinfl'] or '—'}\n"
            f"📱 {r['phone'] or '—'}\n"
            f"📝 {r['reason']}\n"
            f"🏢 {r['added_by_company'] or '—'} / {r['added_by_name'] or '—'}\n"
            f"📅 {r['added_at'][:10]}\n"
            f"{'─' * 25}\n"
        )
    await msg.answer(text, parse_mode="HTML", reply_markup=blacklist_menu())
