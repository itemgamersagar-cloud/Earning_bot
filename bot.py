import asyncio
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import aiosqlite
from config import *
from database import init_db

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# FORCE JOIN CHECK
async def check_force(user_id):
    for channel in FORCE_CHANNELS:
        member = await bot.get_chat_member(channel, user_id)
        if member.status in ["left", "kicked"]:
            return False
    return True

# START
@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()

    if not await check_force(user_id):
        return await message.answer("Join required channels first.")

    async with aiosqlite.connect("bot.db") as db:
        user = await db.execute_fetchone(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        )

        if not user:
            ref = int(args[1]) if len(args) > 1 else None

            await db.execute("""
            INSERT INTO users(user_id, ref_by, balance, total)
            VALUES(?,?,?,?)
            """, (user_id, ref, WELCOME_BONUS, WELCOME_BONUS))

            if ref:
                await db.execute("""
                UPDATE users
                SET balance = balance + ?, total = total + ?, referrals = referrals + 1
                WHERE user_id = ?
                """, (REFERRAL_BONUS, REFERRAL_BONUS, ref))

            await db.commit()

    await message.answer("Welcome! Use /menu")

# MENU
@dp.message(lambda m: m.text == "/menu")
async def menu(message: types.Message):
    await message.answer(
        "Choose:\n"
        "/daily - Daily Bonus\n"
        "/refer - Referral\n"
        "/wallet - Wallet\n"
        "/withdraw amount address"
    )

# DAILY BONUS
@dp.message(lambda m: m.text == "/daily")
async def daily(message: types.Message):
    user_id = message.from_user.id
    now = datetime.datetime.now()

    async with aiosqlite.connect("bot.db") as db:
        user = await db.execute_fetchone(
            "SELECT last_daily FROM users WHERE user_id=?", (user_id,)
        )

        if user[0]:
            last = datetime.datetime.fromisoformat(user[0])
            if (now - last).seconds < 86400:
                return await message.answer("Come back after 24 hours.")

        await db.execute("""
        UPDATE users
        SET balance = balance + ?, total = total + ?, last_daily = ?
        WHERE user_id = ?
        """, (DAILY_BONUS, DAILY_BONUS, now.isoformat(), user_id))

        await db.commit()

    await message.answer(f"Daily bonus {DAILY_BONUS} added!")

# REFER
@dp.message(lambda m: m.text == "/refer")
async def refer(message: types.Message):
    link = f"https://t.me/{(await bot.me()).username}?start={message.from_user.id}"
    await message.answer(f"Your link:\n{link}")

# WALLET
@dp.message(lambda m: m.text == "/wallet")
async def wallet(message: types.Message):
    async with aiosqlite.connect("bot.db") as db:
        user = await db.execute_fetchone(
            "SELECT balance,total,referrals FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

    await message.answer(
        f"Balance: {user[0]}\n"
        f"Total Earned: {user[1]}\n"
        f"Referrals: {user[2]}"
    )

# WITHDRAW
@dp.message(lambda m: m.text.startswith("/withdraw"))
async def withdraw(message: types.Message):
    try:
        _, amount, address = message.text.split()
        amount = int(amount)
    except:
        return await message.answer("Usage: /withdraw amount address")

    async with aiosqlite.connect("bot.db") as db:
        bal = await db.execute_fetchone(
            "SELECT balance FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

        if bal[0] < MIN_WITHDRAW:
            return await message.answer("Minimum not reached.")

        if amount > bal[0]:
            return await message.answer("Not enough balance.")

        await db.execute("""
        INSERT INTO withdraw(user_id, amount, address)
        VALUES(?,?,?)
        """, (message.from_user.id, amount, address))

        await db.execute("""
        UPDATE users SET balance = balance - ?
        WHERE user_id=?
        """, (amount, message.from_user.id))

        await db.commit()

    await message.answer("Withdrawal requested.")

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
