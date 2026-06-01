import config

async def notify_blacklist(bot, data: dict, added_by_name: str, added_by_company: str):
    text = (
        f"🚨 <b>Новая запись в чёрном списке!</b>\n\n"
        f"👤 ФИО: <b>{data.get('full_name', '—')}</b>\n"
        f"📅 Дата рождения: {data.get('birth_date', '—') or '—'}\n"
        f"📄 Паспорт: {data.get('passport_number', '—') or '—'}\n"
        f"🔢 ПИНФЛ: {data.get('pinfl', '—') or '—'}\n"
        f"🏠 Адрес: {data.get('address', '—') or '—'}\n"
        f"📱 Телефон: {data.get('phone', '—') or '—'}\n"
        f"📝 Причина: {data.get('reason', '—')}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏢 Компания: {added_by_company or '—'}\n"
        f"👤 Сотрудник: {added_by_name or '—'}"
    )
    try:
        await bot.send_message(config.CHANNEL_ID, text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка отправки в канал: {e}")


async def notify_product(bot, data: dict, added_by_name: str, added_by_company: str):
    text = (
        f"📦 <b>Новый товар в рассрочку!</b>\n\n"
        f"🔢 Серийный номер: <code>{data.get('serial_number', '—')}</code>\n"
        f"📱 Товар: {data.get('product_name', '—')}\n"
        f"👤 Покупатель: {data.get('buyer_name', '—')}\n"
        f"📱 Телефон: {data.get('buyer_phone', '—') or '—'}\n"
        f"📄 Паспорт: {data.get('buyer_passport', '—') or '—'}\n"
        f"🔢 ПИНФЛ: {data.get('buyer_pinfl', '—') or '—'}\n"
        f"💰 Сумма: {data.get('total_amount', 0):,.0f}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏢 Компания: {added_by_company or '—'}\n"
        f"👤 Сотрудник: {added_by_name or '—'}"
    )
    try:
        await bot.send_message(config.CHANNEL_ID, text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка отправки в канал: {e}")
