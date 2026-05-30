import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

# Logging setup (Railway logs me sab dikhne ke liye)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

# Environment variables se data nikalna
try:
    API_ID = int(os.environ.get("API_ID", 3257177))
    API_HASH = os.environ.get("API_HASH", "aaa4fc6eccc428e8ef2baa5e894d92f8")
    SESSION_STRING = os.environ.get("SESSION_STRING")
except Exception as e:
    logger.error(f"Error loading environment variables: {e}")

if not SESSION_STRING:
    logger.critical("SESSION_STRING missing hai! Railway variables me check karein.")

# Shortcuts ko temporary memory me save karne ke liye dictionary
shortcuts_db = {}
user_states = {}

# Client initialize karna
app = Client(
    "my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# --- COMMAND: .add ya /add (Sirf aapke account se chalega) ---
@app.on_message(filters.command("add", prefixes=[".", "/"]) & filters.me)
async def add_shortcut(client, message: Message):
    if len(message.command) < 2:
        await message.edit_text("❌ Please specify a shortcut name.\nExample: `.add sam`")
        return
    
    shortcut_name = message.command[1].lower()
    user_id = message.from_user.id
    
    # State set karna ki ab agla message save karna hai
    user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
    await message.edit_text(f"📝 **Send message for add:**\nAb wo message bhejiye ya reply kijiye jise `.{shortcut_name}` par save karna hai.")

# --- MESSAGE HANDLER: Agla message save karna ---
@app.on_message(filters.me & ~filters.command(["add"]))
async def save_message(client, message: Message):
    user_id = message.from_user.id
    
    if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[user_id]["shortcut_name"]
        
        if message.text:
            # Memory me save ho raha hai
            shortcuts_db[shortcut_name] = message.text
            await message.reply_text(f"✅ **Saved successfully!**\nAb jab bhi aap `.{shortcut_name}` likhenge, ye message chala jayega.")
        else:
            await message.reply_text("❌ Abhi sirf text messages supported hain.")
        
        # State clear karna
        del user_states[user_id]

# --- TRIGGER: Jab aap chat/DM me '.sam' likhein ---
@app.on_message(filters.text & filters.me & ~filters.edited)
async def trigger_shortcut(client, message: Message):
    text = message.text.strip()
    
    if text.startswith("."):
        shortcut_trigger = text[1:].lower()
        
        if shortcut_trigger in shortcuts_db:
            saved_reply = shortcuts_db[shortcut_trigger]
            # Purane '.sam' wale message ko delete karega taaki ganda na lage
            await message.delete()
            # Naya saved message aapki ID se bhej dega
            await client.send_message(message.chat.id, saved_reply)

if __name__ == "__main__":
    logger.info("Userbot start ho raha hai...")
    app.run()
    
