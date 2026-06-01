from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    full_name = State()
    phone = State()
    company = State()


# Чёрный список — ручной ввод
class BlacklistManualStates(StatesGroup):
    full_name = State()
    birth_date = State()
    passport_number = State()
    pinfl = State()
    address = State()
    phone = State()
    reason = State()


# Чёрный список — через паспорт (ИИ)
class BlacklistPassportStates(StatesGroup):
    photo = State()
    confirm = State()
    phone = State()
    reason = State()


class BlacklistSearchStates(StatesGroup):
    query = State()


# Товары — ручной ввод
class ProductManualStates(StatesGroup):
    serial_number = State()
    product_name = State()
    buyer_name = State()
    buyer_phone = State()
    buyer_passport = State()
    buyer_pinfl = State()
    total_amount = State()
    paid_amount = State()
    notes = State()


# Товары — через паспорт (ИИ)
class ProductPassportStates(StatesGroup):
    photo = State()
    confirm = State()
    serial_number = State()
    product_name = State()
    total_amount = State()
    paid_amount = State()
    notes = State()


class ProductSearchStates(StatesGroup):
    serial_number = State()
