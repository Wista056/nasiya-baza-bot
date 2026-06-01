from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚫 Чёрный список"), KeyboardButton(text="📦 База товаров")],
        [KeyboardButton(text="ℹ️ Мой профиль")],
    ], resize_keyboard=True)


def admin_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚫 Чёрный список"), KeyboardButton(text="📦 База товаров")],
        [KeyboardButton(text="👥 Заявки"), KeyboardButton(text="ℹ️ Мой профиль")],
    ], resize_keyboard=True)


def blacklist_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Добавить в ЧС"), KeyboardButton(text="🔍 Проверить по ЧС")],
        [KeyboardButton(text="🏠 Главное меню")],
    ], resize_keyboard=True)


def blacklist_add_method():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✍️ Ввести вручную"), KeyboardButton(text="📷 Сканировать паспорт")],
        [KeyboardButton(text="🏠 Главное меню")],
    ], resize_keyboard=True)


def products_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Добавить товар"), KeyboardButton(text="🔍 Проверить товар")],
        [KeyboardButton(text="🏠 Главное меню")],
    ], resize_keyboard=True)


def product_add_method():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✍️ Ввести вручную"), KeyboardButton(text="📷 Сканировать паспорт")],
        [KeyboardButton(text="🏠 Главное меню")],
    ], resize_keyboard=True)


def cancel_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True)


def confirm_passport_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Верно", callback_data="passport_ok"),
            InlineKeyboardButton(text="✏️ Исправить", callback_data="passport_edit"),
        ]
    ])


def approve_user_keyboard(telegram_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve:{telegram_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{telegram_id}"),
        ]
    ])


def choose_destination_keyboard():
    """Куда добавить клиента из паспорта"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 В чёрный список", callback_data="dest_blacklist")],
        [InlineKeyboardButton(text="📦 В базу товаров", callback_data="dest_products")],
    ])
