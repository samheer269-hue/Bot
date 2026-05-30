import os
import logging
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

# --- RAILWAY CRASH FIX (Fake Web Server) ---
# Ye Railway ko khush rakhne ke liye hai taaki wo port error se crash na kare
def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    logger.info(f"Fake server started on port {port} to prevent Railway crash.")
    httpd.serve_forever()

# Background me server chalao
Thread(target=run_fake_server, daemon=True).start()

# --- PYROGRAM USERBOT SETUP ---
API_ID = int(os.environ.get("API_ID", 3257177))
API_HASH = os.environ.get("API_HASH", "aaa4fc6eccc428e8ef2baa5e894d92f8")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Shortcuts memory (Isme raw entities save hongi taaki bold/mono text sahi se kaam kare)
shortcuts_db = {}
user_states = {}

app = Client(
    "my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# --- USERBOT LOGIC ---
@app.on_message(filters.me & filters.text & ~filters.edited)
async def handle_my_messages(client, message: Message):
    text = message.text.strip()
    user_id = message.from_user.id

    # 1. COMMAND: .add sam ya /add sam
    if text.startswith(".add ") or text.startswith("/add "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower()
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
            await message.edit_text(f"📝 **Send message for add:**\nAb wo message bhejiye jo `.{shortcut_name}` par save karna hai (Bold, Mono, Italic sab chalega!).")
            return
        except Exception as e:
            logger.error(f"Error in add command: {e}")
            return

    # 2. SAVING STATE (Saves formatting like bold, mono, etc.)
    if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[user_id]["shortcut_name"]
        
        # message.text.markdown se bold, italic, mono jaisa ka taisa copy ho jata hai
        shortcuts_db[shortcut_name] = message.text.markdown
        
        del user_states[user_id]
        await message.reply_text(f"✅ **Saved successfully with formatting!**\nAb aap `.{shortcut_name}` use kar sakte hain.")
        return

    # 3. TRIGGER: .sam
    if text.startswith("."):
        shortcut_trigger = text[1:].lower()
        if shortcut_trigger in shortcuts_db:
            saved_reply = shortcuts_db[shortcut_trigger]
            await message.delete()  # Purana '.sam' delete
            
            # Naya message parse_mode="markdown" ke sath jayega taaki bold/mono dikhe
            await client.send_message(message.chat.id, saved_reply, parse_mode="markdown")
            return

if __name__ == "__main__":
    logger.info("Userbot starting...")
    app.run()
    
