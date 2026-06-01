from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_conn
import config

router = Router()

SUPER_ADMIN_ID = 6302553503


def is_super(telegram_id):
    return telegram_id == SUPER_ADMIN_ID


@router.message(Command("stats"))
async def stats(msg: Message):
    if not is_super(msg.from_user.id):
        return
    conn = get_conn()
    users = conn.execute("SELECT COUNT(*) FROM users WHERE status='approved'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM users WHERE status='pending'").fetchone()[0]
    blocked = conn.execute("SELECT COUNT(*) FROM users WHERE status='blocked'").fetchone()[0]
    bl = conn.execute("SELECT COUNT(*) FROM blacklist").fetchone()[0]
    prods = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    await msg.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Компаний активных: {users}\n"
        f"⏳ Ожидают одобрения: {pending}\n"
        f"🚫 Заблокированных: {blocked}\n"
        f"🔴 Записей в ЧС: {bl}\n"
        f"📦 Товаров в базе: {prods}",
        parse_mode="HTML"
    )


@router.message(Command("users"))
async def list_users(msg: Message):
    if not is_super(msg.from_user.id):
        return
    conn = get_conn()
    users = conn.execute("SELECT * FROM users ORDER BY registered_at DESC").fetchall()
    conn.close()
    if not users:
        await msg.answer("Пользователей нет.")
        return
    text = "👥 <b>Все компании:</b>\n\n"
    for u in users:
        status_emoji = {"approved": "✅", "pending": "⏳", "rejected": "❌", "blocked": "🚫"}.get(u["status"], "❓")
        text += (
            f"{status_emoji} <b>{u['full_name']}</b>\n"
            f"🏢 {u['company'] or '—'}\n"
            f"📱 {u['phone']}\n"
            f"🆔 <code>{u['telegram_id']}</code>\n"
            f"{'─' * 20}\n"
        )
    await msg.answer(text, parse_mode="HTML")


@router.message(Command("block"))
async def block_user(msg: Message):
    if not is_super(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /block 123456789")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Неверный ID")
        return
    conn = get_conn()
    conn.execute("UPDATE users SET status='blocked' WHERE telegram_id=?", (user_id,))
    conn.commit()
    conn.close()
    await msg.answer(f"🚫 Пользователь <code>{user_id}</code> заблокирован.", parse_mode="HTML")
    try:
        await msg.bot.send_message(user_id, "🚫 Ваш аккаунт заблокирован администратором.")
    except Exception:
        pass


@router.message(Command("unblock"))
async def unblock_user(msg: Message):
    if not is_super(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /unblock 123456789")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Неверный ID")
        return
    conn = get_conn()
    conn.execute("UPDATE users SET status='approved' WHERE telegram_id=?", (user_id,))
    conn.commit()
    conn.close()
    await msg.answer(f"✅ Пользователь <code>{user_id}</code> разблокирован.", parse_mode="HTML")
    try:
        await msg.bot.send_message(user_id, "✅ Ваш аккаунт разблокирован.")
    except Exception:
        pass


@router.message(Command("deletebl"))
async def delete_bl(msg: Message):
    if not is_super(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /deletebl ID")
        return
    try:
        record_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Неверный ID")
        return
    conn = get_conn()
    conn.execute("DELETE FROM blacklist WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
    await msg.answer(f"✅ Запись #{record_id} удалена из чёрного списка.")


@router.message(Command("deleteprod"))
async def delete_prod(msg: Message):
    if not is_super(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /deleteprod ID")
        return
    try:
        record_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Неверный ID")
        return
    conn = get_conn()
    conn.execute("DELETE FROM products WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
    await msg.answer(f"✅ Товар #{record_id} удалён из базы.")


@router.message(Command("help"))
async def help_cmd(msg: Message):
    if not is_super(msg.from_user.id):
        return
    await msg.answer(
        "🔑 <b>Команды супер-администратора:</b>\n\n"
        "/stats — статистика\n"
        "/users — все компании\n"
        "/block ID — заблокировать\n"
        "/unblock ID — разблокировать\n"
        "/deletebl ID — удалить из ЧС\n"
        "/deleteprod ID — удалить товар",
        parse_mode="HTML"
    )
EOFcd ~/nasiya_bot && cat > handlers/superadmin.py << 'EOF'
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import get_conn
import config

router = Router()

SUPER_ADMIN_ID = 6302553503


def is_super(telegram_id):
    return telegram_id == SUPER_ADMIN_ID


@router.message(Command("stats"))
async def stats(msg: Message):
    if not is_super(msg.from_user.id):
        return
    conn = get_conn()
    users = conn.execute("SELECT COUNT(*) FROM users WHERE status='approved'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM users WHERE status='pending'").fetchone()[0]
    blocked = conn.execute("SELECT COUNT(*) FROM users WHERE status='blocked'").fetchone()[0]
    bl = conn.execute("SELECT COUNT(*) FROM blacklist").fetchone()[0]
    prods = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    await msg.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Компаний активных: {users}\n"
        f"⏳ Ожидают одобрения: {pending}\n"
        f"🚫 Заблокированных: {blocked}\n"
        f"🔴 Записей в ЧС: {bl}\n"
        f"📦 Товаров в базе: {prods}",
        parse_mode="HTML"
    )


@router.message(Command("users"))
async def list_users(msg: Message):
    if not is_super(msg.from_user.id):
        return
    conn = get_conn()
    users = conn.execute("SELECT * FROM users ORDER BY registered_at DESC").fetchall()
    conn.close()
    if not users:
        await msg.answer("Пользователей нет.")
        return
    text = "👥 <b>Все компании:</b>\n\n"
    for u in users:
        status_emoji = {"approved": "✅", "pending": "⏳", "rejected": "❌", "blocked": "🚫"}.get(u["status"], "❓")
        text += (
            f"{status_emoji} <b>{u['full_name']}</b>\n"
            f"🏢 {u['company'] or '—'}\n"
            f"📱 {u['phone']}\n"
            f"🆔 <code>{u['telegram_id']}</code>\n"
            f"{'─' * 20}\n"
        )
    await msg.answer(text, parse_mode="HTML")


@router.message(Command("block"))
async def block_user(msg: Message):
    if not is_super(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /block 123456789")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Неверный ID")
        return
    conn = get_conn()
    conn.execute("UPDATE users SET status='blocked' WHERE telegram_id=?", (user_id,))
    conn.commit()
    conn.close()
    await msg.answer(f"🚫 Пользователь <code>{user_id}</code> заблокирован.", parse_mode="HTML")
    try:
        await msg.bot.send_message(user_id, "🚫 Ваш аккаунт заблокирован администратором.")
    except Exception:
        pass


@router.message(Command("unblock"))
async def unblock_user(msg: Message):
    if not is_super(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /unblock 123456789")
        return
    try:
        user_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Неверный ID")
        return
    conn = get_conn()
    conn.execute("UPDATE users SET status='approved' WHERE telegram_id=?", (user_id,))
    conn.commit()
    conn.close()
    await msg.answer(f"✅ Пользователь <code>{user_id}</code> разблокирован.", parse_mode="HTML")
    try:
        await msg.bot.send_message(user_id, "✅ Ваш аккаунт разблокирован.")
    except Exception:
        pass


@router.message(Command("deletebl"))
async def delete_bl(msg: Message):
    if not is_super(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /deletebl ID")
        return
    try:
        record_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Неверный ID")
        return
    conn = get_conn()
    conn.execute("DELETE FROM blacklist WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
    await msg.answer(f"✅ Запись #{record_id} удалена из чёрного списка.")


@router.message(Command("deleteprod"))
async def delete_prod(msg: Message):
    if not is_super(msg.from_user.id):
        return
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer("Использование: /deleteprod ID")
        return
    try:
        record_id = int(args[1])
    except ValueError:
        await msg.answer("❌ Неверный ID")
        return
    conn = get_conn()
    conn.execute("DELETE FROM products WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
    await msg.answer(f"✅ Товар #{record_id} удалён из базы.")


@router.message(Command("help"))
async def help_cmd(msg: Message):
    if not is_super(msg.from_user.id):
        return
    await msg.answer(
        "🔑 <b>Команды супер-администратора:</b>\n\n"
        "/stats — статистика\n"
        "/users — все компании\n"
        "/block ID — заблокировать\n"
        "/unblock ID — разблокировать\n"
        "/deletebl ID — удалить из ЧС\n"
        "/deleteprod ID — удалить товар",
        parse_mode="HTML"
    )
