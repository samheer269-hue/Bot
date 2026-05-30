import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

API_ID = int(os.environ.get("API_ID", 3257177))
API_HASH = os.environ.get("API_HASH", "aaa4fc6eccc428e8ef2baa5e894d92f8")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Memory database
shortcuts_db = {}
user_states = {}

app = Client(
    "my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# --- JAB BHI AAP KOI MESSAGE BHEJO ---
@app.on_message(filters.me & filters.text & ~filters.edited)
async def handle_my_messages(client, message: Message):
    text = message.text.strip()
    user_id = message.from_user.id

    # 1. CHECK FOR ADD COMMAND (e.g., .add sam ya /add sam)
    if text.startswith(".add ") or text.startswith("/add "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower()
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
            await message.edit_text(f"📝 **Send message for add:**\nAb wo message bhejiye jo `.{shortcut_name}` par save karna hai.")
            return
        except Exception as e:
            logger.error(f"Error in add command: {e}")
            return

    # 2. CHECK IF WAITING FOR MESSAGE TO SAVE
    if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[user_id]["shortcut_name"]
        shortcuts_db[shortcut_name] = text
        del user_states[user_id]
        await message.reply_text(f"✅ **Saved successfully!**\nAb aap `.{shortcut_name}` use kar sakte hain.")
        return

    # 3. CHECK FOR TRIGGER (e.g., .sam)
    if text.startswith("."):
        shortcut_trigger = text[1:].lower()
        if shortcut_trigger in shortcuts_db:
            saved_reply = shortcuts_db[shortcut_trigger]
            await message.delete()  # Purana message delete
            await client.send_message(message.chat.id, saved_reply) # Naya message send
            return

if __name__ == "__main__":
    logger.info("Userbot running...")
    app.run()
    
