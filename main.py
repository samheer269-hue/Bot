import os
import logging
import asyncio
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

# --- RAILWAY AUTO-PORT FIX ---
# Ye code Railway ke port ko verify karega taaki status kabhi 'Crashed' na aaye
def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    try:
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        logger.info(f"Railway verification active on port {port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")

# Background me server start karna
Thread(target=run_fake_server, daemon=True).start()

# --- ENVIRONMENT VARIABLES ---
API_ID = int(os.environ.get("API_ID", 32571771))
API_HASH = os.environ.get("API_HASH", "aaa4fc6eccc428e8ef2baa5e894d92f8")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Telethon Client Initialization
bot = TelegramClient(
    None, 
    api_id=API_ID, 
    api_hash=API_HASH
)

shortcuts_db = {}
user_states = {}

# --- USERBOT LOGIC ---
@bot.on(events.NewMessage(outgoing=True))
async def handle_messages(event):
    if not event.text:
        return

    text = event.text.strip()
    chat_id = event.chat_id

    # 1. COMMAND: .add sam
    if text.startswith(".add ") or text.startswith("/add "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower()
            user_states[chat_id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
            await event.edit(f"📝 **Send message for add:**\nAb wo message bhejiye jo `.{shortcut_name}` par save karna hai (Bold, Mono, Italic sab support hai).")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            return

    # 2. SAVING WITH FORMATTING
    if chat_id in user_states and user_states[chat_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[chat_id]["shortcut_name"]
        
        shortcuts_db[shortcut_name] = {
            "text": event.message.text,
            "entities": event.message.entities
        }
        
        del user_states[chat_id]
        await event.respond(f"✅ **Saved successfully!**\nAb aap `.{shortcut_name}` use kar sakte hain.")
        return

    # 3. TRIGGER: .sam
    if text.startswith("."):
        shortcut_trigger = text[1:].lower()
        if shortcut_trigger in shortcuts_db:
            saved_data = shortcuts_db[shortcut_trigger]
            
            await event.delete() # Purana .sam delete karna
            
            await bot.send_message(
                chat_id, 
                message=saved_data["text"], 
                formatting_entities=saved_data["entities"]
            )
            return

async def main():
    logger.info("Starting Telethon Userbot...")
    await bot.start()
    logger.info("Userbot is online and running successfully!")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    # Python 3.13 async handle fix
    asyncio.run(main())
    
