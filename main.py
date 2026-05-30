import os
import logging
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

# --- RAILWAY CRASH FIX (Fake Web Server) ---
def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    logger.info(f"Server running on port {port}")
    httpd.serve_forever()

Thread(target=run_fake_server, daemon=True).start()

# --- CODES ME SE SAB HATA DIYA ---
# Ab ye seedhe Railway ke Environment Variables se load hoga
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

shortcuts_db = {}
user_states = {}

app = Client(
    "my_userbot",
    api_id=API_ID,
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
            await message.edit_text(f"📝 **Send message for add:**\nAb wo message bhejiye jo `.{shortcut_name}` par save karna hai (Bold/Mono sab chalega).")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            return

    # 2. SAVING WITH FORMATTING (Bold, Mono, Italic)
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
    logger.info("Starting Userbot...")
    app.run()
    
