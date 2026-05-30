import os
import logging
import asyncio
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

# --- RAILWAY AUTO-PORT FIX ---
def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    try:
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        logger.info(f"Railway port verification active on port {port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")

Thread(target=run_fake_server, daemon=True).start()

# --- ENVIRONMENT VARIABLES ---
API_ID = int(os.environ.get("API_ID", 32571771))
API_HASH = os.environ.get("API_HASH", "aaa4fc6eccc428e8ef2baa5e894d92f8")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Storage session error se bachne ke liye in_memory=True kiya hai
app = Client(
    "my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING.strip(),
    in_memory=True
)

shortcuts_db = {}
user_states = {}

# --- BINA FILTERS KE RAW HANDLER ---
@app.on_message()
async def handle_all_messages(client, message: Message):
    # Check 1: Text hona chahiye
    if not message.text:
        return
        
    # Check 2: Sirf aapka message hona chahiye
    if not message.from_user or not message.from_user.is_self:
        return

    text = message.text.strip()
    user_id = message.from_user.id

    # 1. COMMAND: .add sam
    if text.startswith(".add ") or text.startswith("/add "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower()
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
            await message.edit_text(f"📝 **Send message for add:**\nAb wo message bhejiye jo `.{shortcut_name}` par save karna hai (Bold, Mono, Italic sab support hai).")
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
            await message.delete()  # Purana .sam delete
            await client.send_message(message.chat.id, saved_reply, parse_mode="markdown")
            return

if __name__ == "__main__":
    logger.info("Starting Pyrogram Userbot...")
    app.run()
    
