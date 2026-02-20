import aiosqlite
import datetime

DB = "bot.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            ref_by INTEGER,
            balance INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            referrals INTEGER DEFAULT 0,
            last_daily TEXT,
            banned INTEGER DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS withdraw(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            address TEXT,
            status TEXT DEFAULT 'pending'
        )
        """)
        await db.commit()
