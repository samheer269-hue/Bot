import os
import logging
import asyncio
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import AuthKeyInvalid, UserDeactivated

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

# --- RAILWAY CRASH FIX (Fake Web Server) ---
def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    try:
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        logger.info(f"Fake server running on port {port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Web server error: {e}")

Thread(target=run_fake_server, daemon=True).start()

# --- FETCH ENVIRONMENT VARIABLES ---
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Check if variables exist
if not API_ID or not API_HASH or not SESSION_STRING:
    logger.critical("❌ ERROR: Railway me API_ID, API_HASH ya SESSION_STRING missing hai!")
    # System ko crash hone se bachane ke liye loop me daal rahe hain
    while True: asyncio.run(asyncio.sleep(3600))

# Shortcuts database
shortcuts_db = {}
user_states = {}

# Client Initialization
app = Client(
    "my_userbot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

@app.on_message(filters.me & filters.text & ~filters.edited)
async def handle_my_messages(client, message: Message):
    text = message.text.strip()
    user_id = message.from_user.id

    # 1. COMMAND: .add sam
    if text.startswith(".add ") or text.startswith("/add "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower()
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
            await message.edit_text(f"📝 **Send message for add:**\nAb wo message bhejiye jo `.{shortcut_name}` par save karna hai (Bold/Mono text formatting support ke sath).")
            return
        except Exception as e:
            logger.error(f"Error in add command: {e}")
            return

    # 2. SAVING WITH FORMATTING
    if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[user_id]["shortcut_name"]
        shortcuts_db[shortcut_name] = message.text.markdown
        del user_states[user_id]
        await message.reply_text(f"✅ **Saved successfully!**\nAb aap `.{shortcut_name}` use kar sakte hain.")
        return

    # 3. TRIGGER: .sam
    if text.startswith("."):
        shortcut_trigger = text[1:].lower()
        if shortcut_trigger in shortcuts_db:
            saved_reply = shortcuts_db[shortcut_trigger]
            await message.delete()
            await client.send_message(message.chat.id, saved_reply, parse_mode="markdown")
            return

if __name__ == "__main__":
    try:
        logger.info("Starting Userbot...")
        app.run()
    except (AuthKeyInvalid, UserDeactivated):
        logger.critical("❌ CRITICAL: Aapki SESSION_STRING invalid ho chuki hai ya expire ho gayi hai! Kripya nayi string generate karein.")
        # Bot ko tight loop me rakhna taaki Railway use crash na dikhaye
        while True: asyncio.run(asyncio.sleep(3600))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        while True: asyncio.run(asyncio.sleep(3600))
        
