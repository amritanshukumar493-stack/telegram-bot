import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# ---------- ENV ----------
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ---------- IMAGES ----------
BANNER = "https://t.me/LSVaultGiveaway/8?single"
QR_IMG = "https://t.me/LSVaultGiveaway/9?single"

# ---------- INIT ----------
app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["losted_db"]
users = db["users"]
votes = db["votes"]

# ---------- START ----------
@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user = message.from_user

    if len(message.command) > 1 and message.command[1].startswith("vote_"):
        target = int(message.command[1].split("_")[1])
        data = await users.find_one({"user_id": target})
        count = data.get("votes", 0) if data else 0

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")],
            [InlineKeyboardButton(f"🗳 Vote ({count})", callback_data=f"vote_{target}")]
        ])

        return await message.reply_photo(
            photo=BANNER,
            caption=f"👤 {user.first_name}\n🗳 Votes: {count}",
            reply_markup=btn
        )

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Participate", callback_data="reg")]
    ])

    await message.reply_photo(
        photo=BANNER,
        caption="🎉 Giveaway Join karo aur votes earn karo!",
        reply_markup=btn
    )

# ---------- CALLBACK ----------
@app.on_callback_query()
async def cb(client, query):
    uid = query.from_user.id
    data = query.data

    if data.startswith("vote_"):
        target = int(data.split("_")[1])

        try:
            await client.get_chat_member(CHANNEL_ID, uid)
        except:
            return await query.answer("❌ Pehle channel join karo!", show_alert=True)

        already = await votes.find_one({"voter": uid})
        if already:
            return await query.answer("❌ Already voted!", show_alert=True)

        await votes.insert_one({"voter": uid, "target": target})
        await users.update_one({"user_id": target}, {"$inc": {"votes": 1}}, upsert=True)

        await query.answer("✅ Vote added!")

    elif data == "reg":
        await users.update_one({"user_id": uid}, {"$set": {"username": query.from_user.username}}, upsert=True)

        botname = (await client.get_me()).username
        link = f"https://t.me/{botname}?start=vote_{uid}"

        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Share Link", url=f"https://t.me/share/url?url={link}")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="rank")]
        ])

        await query.message.edit_caption("✅ Registered!\nApna link share karo 🔥", reply_markup=btn)

    elif data == "rank":
        text = "🏆 Leaderboard\n\n"
        i = 1
        async for u in users.find().sort("votes", -1).limit(10):
            text += f"{i}. {u.get('username','user')} - {u.get('votes',0)}\n"
            i += 1

        await query.message.edit_caption(text)

# ---------- ADMIN ----------
@app.on_message(filters.command("add") & filters.user(ADMIN_ID))
async def add(client, message):
    try:
        uid = int(message.command[1])
        amt = int(message.command[2])
        await users.update_one({"user_id": uid}, {"$inc": {"votes": amt}}, upsert=True)
        await message.reply("✅ Votes added")
    except:
        await message.reply("Usage: /add user_id amount")

# ---------- RUN ----------
print("BOT STARTED 🔥")
