# language: Python, file: ff_clan_bot.py, target: Python 3.10+, aiogram 3.x
# متطلبات التشغيل في التيرمنال: pip install aiogram

import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

# ضع التتوكن الخاص بك هنا الذي نسخته من BotFather
TOKEN = "8902526149:AAGOvXkT0-GznOevmHX7UYeB3LYicdYMU50"

# ضع الأيدي (Telegram ID) الخاص بك كأدمن لتتمكن من إضافة النقاط
ADMIN_IDS = [123456789]  

bot = Bot(token=TOKEN)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect("clan_glory.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS members (
                    telegram_id INTEGER PRIMARY KEY,
                    ign TEXT,
                    uid TEXT,
                    glory INTEGER DEFAULT 0
                )''')
    conn.commit()
    conn.close()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "⚡ **نظام تتبع كلوري كلأن فري فاير**\n\n"
        "الأوامر المتاحة:\n"
        "• `/register [اسمك] [UID]` - لتسجيل نفسك في النظام\n"
        "• `/leaderboard` - عرض ترتيب الأعضاء حسب الكلوري\n"
        "• `/addglory [UID] [النقاط]` - إضافة نقاط لأعضاء الكلأن (للإدارة فقط)\n"
        "• `/myglory` - عرض نقاطك الحالية",
        parse_mode="Markdown"
    )

@dp.message(Command("register"))
async def cmd_register(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ الاستخدام الصحيح: `/register [اسمك داخل اللعبة] [UID]`", parse_mode="Markdown")
        return
    
    ign, uid = args[1], args[2]
    conn = sqlite3.connect("clan_glory.db")
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO members (telegram_id, ign, uid, glory) 
            VALUES (?, ?, ?, COALESCE((SELECT glory FROM members WHERE telegram_id = ?), 0))
            ON CONFLICT(telegram_id) DO UPDATE SET ign=excluded.ign, uid=excluded.uid
        """, (message.from_user.id, ign, uid, message.from_user.id))
        conn.commit()
        await message.answer(f"✅ تم التسجيل بنجاح:\nالاسم: `{ign}`\nUID: `{uid}`", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ خطأ أثناء التسجيل: {e}")
    finally:
        conn.close()

@dp.message(Command("addglory"))
async def cmd_add_glory(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ هذا الأمر مخصص لإدارة الكلأن فقط.")
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.answer("⚠️ الاستخدام: `/addglory [UID] [النقاط]`", parse_mode="Markdown")
        return
    
    uid, points = args[1], int(args[2])
    conn = sqlite3.connect("clan_glory.db")
    c = conn.cursor()
    c.execute("UPDATE members SET glory = glory + ? WHERE uid = ?", (points, uid))
    conn.commit()
    changes = c.rowcount
    conn.close()
    
    if changes > 0:
        await message.answer(f"✅ تمت إضافة `{points}` نقطة للـ UID: `{uid}` بنجاح.", parse_mode="Markdown")
    else:
        await message.answer(f"⚠️ لم يتم العثور على عضو بهذا الـ UID مسجل في القاعدة.")

@dp.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    conn = sqlite3.connect("clan_glory.db")
    c = conn.cursor()
    c.execute("SELECT ign, uid, glory FROM members ORDER BY glory DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        await message.answer("📭 لا يوجد أعضاء مسجلين حتى الآن.")
        return
        
    text = "🏆 **لوحة الشرف - صدارة الكلوري:**\n\n"
    for idx, (ign, uid, glory) in enumerate(rows, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
        text += f"{medal} `{ign}` (UID: `{uid}`) ➔ **{glory}** نقطة\n"
        
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("myglory"))
async def cmd_my_glory(message: Message):
    conn = sqlite3.connect("clan_glory.db")
    c = conn.cursor()
    c.execute("SELECT ign, uid, glory FROM members WHERE telegram_id = ?", (message.from_user.id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        await message.answer("⚠️ أنت لست مسجلاً. استخدم `/register` أولاً.", parse_mode="Markdown")
        return
        
    ign, uid, glory = row
    await message.answer(f"📊 احصائياتك:\nالاسم: `{ign}`\nUID: `{uid}`\nمجموع الكلوري: **{glory}** نقطة", parse_mode="Markdown")

async def main():
    init_db()
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
