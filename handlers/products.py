from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states import ProductManualStates, ProductPassportStates, ProductSearchStates
from database import add_product, search_product, get_user
from keyboards import (products_menu, product_add_method,
                       cancel_keyboard, confirm_passport_keyboard)
from ai_passport import extract_passport_data

router = Router()


def get_user_info(telegram_id):
    user = get_user(telegram_id)
    if user:
        return user["full_name"], user["company"] or "", user["phone"]
    return "", "", ""


@router.message(F.text == "📦 База товаров")
async def products_main(msg: Message):
    await msg.answer("📦 <b>База товаров в рассрочку</b>\n\nВыберите действие:",
                     reply_markup=products_menu(), parse_mode="HTML")


@router.message(F.text == "➕ Добавить товар")
async def prod_add_choose(msg: Message):
    await msg.answer("Как хотите добавить покупателя?", reply_markup=product_add_method())


# ══════════ РУЧНОЙ ВВОД ══════════

@router.message(F.text == "✍️ Ввести вручную")
async def prod_manual_start(msg: Message, state: FSMContext):
    await msg.answer("🔢 Введите <b>серийный номер</b> товара:", parse_mode="HTML",
                     reply_markup=cancel_keyboard())
    await state.set_state(ProductManualStates.serial_number)


@router.message(ProductManualStates.serial_number)
async def pm_serial(msg: Message, state: FSMContext):
    await state.update_data(serial_number=msg.text.strip())
    await msg.answer("📱 Название товара:")
    await state.set_state(ProductManualStates.product_name)


@router.message(ProductManualStates.product_name)
async def pm_prod_name(msg: Message, state: FSMContext):
    await state.update_data(product_name=msg.text.strip())
    await msg.answer("👤 ФИО покупателя:")
    await state.set_state(ProductManualStates.buyer_name)


@router.message(ProductManualStates.buyer_name)
async def pm_buyer_name(msg: Message, state: FSMContext):
    await state.update_data(buyer_name=msg.text.strip())
    await msg.answer("📱 Телефон покупателя:")
    await state.set_state(ProductManualStates.buyer_phone)


@router.message(ProductManualStates.buyer_phone)
async def pm_buyer_phone(msg: Message, state: FSMContext):
    await state.update_data(buyer_phone=msg.text.strip())
    await msg.answer("📄 Номер паспорта покупателя (или '-'):")
    await state.set_state(ProductManualStates.buyer_passport)


@router.message(ProductManualStates.buyer_passport)
async def pm_buyer_passport(msg: Message, state: FSMContext):
    val = msg.text.strip()
    await state.update_data(buyer_passport="" if val == "-" else val)
    await msg.answer("🔢 ПИНФЛ покупателя (или '-'):")
    await state.set_state(ProductManualStates.buyer_pinfl)


@router.message(ProductManualStates.buyer_pinfl)
async def pm_buyer_pinfl(msg: Message, state: FSMContext):
    val = msg.text.strip()
    await state.update_data(buyer_pinfl="" if val == "-" else val)
    await msg.answer("💰 Полная сумма рассрочки (или '-'):")
    await state.set_state(ProductManualStates.total_amount)


@router.message(ProductManualStates.total_amount)
async def pm_total(msg: Message, state: FSMContext):
    try:
        val = float(msg.text.strip()) if msg.text.strip() != "-" else 0
    except ValueError:
        await msg.answer("⚠️ Введите число или '-':")
        return
    await state.update_data(total_amount=val)
    await msg.answer("💳 Уже оплаченная сумма (или '-'):")
    await state.set_state(ProductManualStates.paid_amount)


@router.message(ProductManualStates.paid_amount)
async def pm_paid(msg: Message, state: FSMContext):
    try:
        val = float(msg.text.strip()) if msg.text.strip() != "-" else 0
    except ValueError:
        await msg.answer("⚠️ Введите число или '-':")
        return
    await state.update_data(paid_amount=val)
    await msg.answer("📝 Примечание (или '-'):")
    await state.set_state(ProductManualStates.notes)


@router.message(ProductManualStates.notes)
async def pm_notes(msg: Message, state: FSMContext):
    data = await state.get_data()
    notes = "" if msg.text.strip() == "-" else msg.text.strip()
    await state.clear()

    name, company, _ = get_user_info(msg.from_user.id)
    success = add_product(
        serial_number=data["serial_number"],
        product_name=data["product_name"],
        buyer_name=data["buyer_name"],
        buyer_phone=data["buyer_phone"],
        total_amount=data.get("total_amount", 0),
        paid_amount=data.get("paid_amount", 0),
        notes=notes,
        added_by_telegram_id=msg.from_user.id,
        buyer_passport=data.get("buyer_passport", ""),
        buyer_pinfl=data.get("buyer_pinfl", ""),
        added_by_name=name,
        added_by_company=company,
    )

    if success:
        remaining = data.get("total_amount", 0) - data.get("paid_amount", 0)
        await msg.answer(
            f"✅ <b>Товар добавлен в базу</b>\n\n"
            f"🔢 Серийный номер: <code>{data['serial_number']}</code>\n"
            f"📱 Товар: {data['product_name']}\n"
            f"👤 Покупатель: {data['buyer_name']}\n"
            f"📄 Паспорт: {data.get('buyer_passport') or '—'}\n"
            f"🔢 ПИНФЛ: {data.get('buyer_pinfl') or '—'}\n"
            f"💰 Сумма: {data.get('total_amount', 0):,.0f}\n"
            f"⏳ Остаток: {remaining:,.0f}",
            parse_mode="HTML", reply_markup=products_menu()
        )
    else:
        await msg.answer(
            f"⚠️ Товар с серийным номером <code>{data['serial_number']}</code> уже есть в базе!",
            parse_mode="HTML", reply_markup=products_menu()
        )


# ══════════ ПАСПОРТ + ИИ ══════════

@router.message(F.text == "📷 Сканировать паспорт")
async def prod_passport_start(msg: Message, state: FSMContext):
    await msg.answer(
        "📷 Отправьте <b>фото паспорта</b> покупателя.\n\nИИ автоматически извлечёт данные.",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.set_state(ProductPassportStates.photo)


@router.message(ProductPassportStates.photo, F.photo)
async def prod_passport_photo(msg: Message, state: FSMContext):
    await msg.answer("⏳ Анализирую паспорт...")

    photo = msg.photo[-1]
    file = await msg.bot.get_file(photo.file_id)
    photo_bytes = await msg.bot.download_file(file.file_path)

    try:
        data = await extract_passport_data(photo_bytes.read())
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {e}\n\nПопробуйте ещё раз или введите вручную.")
        await state.clear()
        return

    await state.update_data(passport_data=data)

    text = (
        f"📋 <b>Данные из паспорта покупателя:</b>\n\n"
        f"👤 ФИО: <b>{data.get('full_name') or '—'}</b>\n"
        f"📅 Дата рождения: {data.get('birth_date') or '—'}\n"
        f"📄 Паспорт: {data.get('passport_number') or '—'}\n"
        f"🔢 ПИНФЛ: {data.get('pinfl') or '—'}\n"
        f"🏠 Адрес: {data.get('address') or '—'}\n\n"
        f"Данные верны?"
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=confirm_passport_keyboard())
    await state.set_state(ProductPassportStates.confirm)


@router.callback_query(F.data == "passport_ok", ProductPassportStates.confirm)
async def prod_passport_confirmed(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await call.message.answer("🔢 Введите серийный номер товара:", reply_markup=cancel_keyboard())
    await state.set_state(ProductPassportStates.serial_number)


@router.callback_query(F.data == "passport_edit", ProductPassportStates.confirm)
async def prod_passport_edit(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("📷 Отправьте новое фото или нажмите ❌ Отмена.",
                              reply_markup=cancel_keyboard())
    await state.set_state(ProductPassportStates.photo)


@router.message(ProductPassportStates.serial_number)
async def pp_serial(msg: Message, state: FSMContext):
    await state.update_data(serial_number=msg.text.strip())
    await msg.answer("📱 Название товара:")
    await state.set_state(ProductPassportStates.product_name)


@router.message(ProductPassportStates.product_name)
async def pp_prod_name(msg: Message, state: FSMContext):
    await state.update_data(product_name=msg.text.strip())
    await msg.answer("💰 Полная сумма рассрочки (или '-'):")
    await state.set_state(ProductPassportStates.total_amount)


@router.message(ProductPassportStates.total_amount)
async def pp_total(msg: Message, state: FSMContext):
    try:
        val = float(msg.text.strip()) if msg.text.strip() != "-" else 0
    except ValueError:
        await msg.answer("⚠️ Введите число или '-':")
        return
    await state.update_data(total_amount=val)
    await msg.answer("💳 Уже оплаченная сумма (или '-'):")
    await state.set_state(ProductPassportStates.paid_amount)


@router.message(ProductPassportStates.paid_amount)
async def pp_paid(msg: Message, state: FSMContext):
    try:
        val = float(msg.text.strip()) if msg.text.strip() != "-" else 0
    except ValueError:
        await msg.answer("⚠️ Введите число или '-':")
        return
    await state.update_data(paid_amount=val)
    await msg.answer("📝 Примечание (или '-'):")
    await state.set_state(ProductPassportStates.notes)


@router.message(ProductPassportStates.notes)
async def pp_notes(msg: Message, state: FSMContext):
    data = await state.get_data()
    passport_data = data.get("passport_data", {})
    notes = "" if msg.text.strip() == "-" else msg.text.strip()
    await state.clear()

    name, company, _ = get_user_info(msg.from_user.id)
    success = add_product(
        serial_number=data["serial_number"],
        product_name=data["product_name"],
        buyer_name=passport_data.get("full_name", ""),
        buyer_phone="",
        total_amount=data.get("total_amount", 0),
        paid_amount=data.get("paid_amount", 0),
        notes=notes,
        added_by_telegram_id=msg.from_user.id,
        buyer_passport=passport_data.get("passport_number", ""),
        buyer_pinfl=passport_data.get("pinfl", ""),
        buyer_birth_date=passport_data.get("birth_date", ""),
        buyer_address=passport_data.get("address", ""),
        added_by_name=name,
        added_by_company=company,
    )

    if success:
        remaining = data.get("total_amount", 0) - data.get("paid_amount", 0)
        await msg.answer(
            f"✅ <b>Товар добавлен в базу</b>\n\n"
            f"🔢 <code>{data['serial_number']}</code>\n"
            f"📱 {data['product_name']}\n"
            f"👤 {passport_data.get('full_name') or '—'}\n"
            f"📄 Паспорт: {passport_data.get('passport_number') or '—'}\n"
            f"🔢 ПИНФЛ: {passport_data.get('pinfl') or '—'}\n"
            f"⏳ Остаток: {remaining:,.0f}",
            parse_mode="HTML", reply_markup=products_menu()
        )
    else:
        await msg.answer(
            f"⚠️ Серийный номер <code>{data['serial_number']}</code> уже есть в базе!",
            parse_mode="HTML", reply_markup=products_menu()
        )


# ══════════ ПОИСК ══════════

@router.message(F.text == "🔍 Проверить товар")
async def prod_search_start(msg: Message, state: FSMContext):
    await msg.answer("🔢 Введите серийный номер товара:", reply_markup=cancel_keyboard())
    await state.set_state(ProductSearchStates.serial_number)


@router.message(ProductSearchStates.serial_number)
async def prod_search_do(msg: Message, state: FSMContext):
    await state.clear()
    result = search_product(msg.text.strip())

    if not result:
        await msg.answer("✅ <b>Товар не найден в базе</b>\n\nТовар чист.",
                         parse_mode="HTML", reply_markup=products_menu())
        return

    remaining = (result["total_amount"] or 0) - (result["paid_amount"] or 0)
    await msg.answer(
        f"⚠️ <b>ТОВАР В РАССРОЧКЕ!</b>\n\n"
        f"🔢 <code>{result['serial_number']}</code>\n"
        f"📱 {result['product_name']}\n"
        f"👤 {result['buyer_name']}\n"
        f"📄 Паспорт: {result['buyer_passport'] or '—'}\n"
        f"🔢 ПИНФЛ: {result['buyer_pinfl'] or '—'}\n"
        f"📱 Телефон: {result['buyer_phone'] or '—'}\n"
        f"💰 Сумма: {result['total_amount']:,.0f}\n"
        f"💳 Оплачено: {result['paid_amount']:,.0f}\n"
        f"⏳ Остаток: {remaining:,.0f}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏢 Продавец: {result['added_by_company'] or '—'}\n"
        f"👤 Сотрудник: {result['added_by_name'] or '—'}\n"
        f"📅 Добавлен: {result['added_at'][:10]}"
        + (f"\n📝 {result['notes']}" if result['notes'] else ""),
        parse_mode="HTML", reply_markup=products_menu()
    )
