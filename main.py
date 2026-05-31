import os
import logging
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
SESSION_STRING = os.environ.get("SESSION_STRING", "")

app = Client(
    "my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING.strip() if SESSION_STRING else None,
    in_memory=True
)

# In-Memory Database (Isme chat_id aur message_id save hogi stable photo fetch ke liye)
shortcuts_db = {}
user_states = {}

@app.on_message()
async def handle_all_messages(client, message: Message):
    # Text ya Caption dono me se kuch ek hona chahiye process karne ke liye
    if not message.text and not message.caption:
        # Agar state me waiting hai toh bina text ke bhi media accept karenge
        if not (message.from_user and message.from_user.is_self and message.from_user.id in user_states):
            return
        
    if not message.from_user or not message.from_user.is_self:
        return

    # Check karne ke liye ki text hai ya caption
    raw_text = message.text or message.caption or ""
    text = raw_text.strip()
    user_id = message.from_user.id
    chat_id = message.chat.id

    # --- HANDLING SAVE STATE ---
    if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[user_id]["shortcut_name"]
        
        # Stability fix: Photo baar-baar gayab na ho, isliye chat_id aur message_id structure save kiya
        shortcuts_db[shortcut_name] = {
            "chat_id": message.chat.id,
            "message_id": message.id
        }
        del user_states[user_id]
        
        # Fresh confirmation message
        await message.delete()
        await client.send_message(chat_id, f"✅ **Saved successfully!**\nYou can now use `.{shortcut_name}` anywhere.")
        return

    # --- COMMAND 1: .alive ---
    if text.lower() == ".alive":
        await message.edit_text("✨ Zyron Userbot is Active and Running Smoothly!")
        return

    # --- COMMAND 2: .list ---
    if text.lower() == ".list":
        if not shortcuts_db:
            await message.edit_text("❌ No shortcuts found! Use `.a <name>` to create one.")
        else:
            shortcuts_list = "\n".join([f"🔹 .{k}" for k in shortcuts_db.keys()])
            await message.edit_text(f"📋 **Your Saved Shortcuts:**\n\n{shortcuts_list}")
        return

    # --- COMMAND 3: .del <name> ---
    if text.startswith(".del "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower().strip()
            if shortcut_name in shortcuts_db:
                del shortcuts_db[shortcut_name]
                await message.edit_text(f"✅ Shortcut `.{shortcut_name}` has been deleted successfully.")
            else:
                await message.edit_text(f"❌ Shortcut `.{shortcut_name}` not found!")
        except Exception as e:
            logger.error(f"Error in del command: {e}")
        return

    # --- COMMAND 4: .a <name> ---
    if text.startswith(".a ") or text.startswith("/a "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower().strip()
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
            await message.edit_text(f"📝 **Send the message/photo you want to save for `.{shortcut_name}`**\n*(Photo, Media, and formatting are fully supported)*")
        except Exception as e:
            logger.error(f"Error in add command: {e}")
        return

    # --- TRIGGERING THE SHORTCUT ---
    if text.startswith("."):
        shortcut_trigger = text[1:].lower().strip()
        if shortcut_trigger in shortcuts_db:
            data = shortcuts_db[shortcut_trigger]
            reply_to_id = message.reply_to_message.id if message.reply_to_message else None
            
            try:
                # Naya message send karne ki jagah pehle purane ko delete karke direct fetch karega
                await message.delete()
                
                await client.copy_message(
                    chat_id=chat_id,
                    from_chat_id=data["chat_id"],
                    message_id=data["message_id"],
                    reply_to_message_id=reply_to_id
                )
            except Exception as e:
                logger.error(f"Error in sending shortcut: {e}")
                # Agar error aaye toh naya status send hoga, taaki system crash na ho
                await client.send_message(chat_id, f"❌ **Error:** Unable to fetch `.{shortcut_trigger}`. original message shayad delete ho gaya hai.")
            return

if __name__ == "__main__":
    logger.info("Starting Fully Loaded Userbot...")
    app.run()
