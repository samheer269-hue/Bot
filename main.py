import os
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import Message

# Environments variables se data nikalna (Railway par set karenge)
API_ID = int(os.environ.get("API_ID", 3257177))
API_HASH = os.environ.get("API_HASH", "aaa4fc6eccc428e8ef2baa5e894d92f8")
SESSION_STRING = os.environ.get("SESSION_STRING")

# Database Setup (Taaki data save rahe)
db_path = "shortcuts.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS notes (keyword TEXT UNIQUE, reply TEXT)")
conn.commit()

# Userbot Client Initialization
app = Client("my_userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# State tracker temporary memory me rakhne ke liye
user_states = {}

# --- COMMAND: .add (Sirf aapke liye kaam karega) ---
@app.on_message(filters.command("add", prefixes=[".", "/"]) & filters.me)
async def add_shortcut(client, message: Message):
    if len(message.command) < 2:
        await message.edit_text("❌ Please specify a shortcut name.\nExample: `.add sam`")
        return
    
    shortcut_name = message.command[1].lower()
    user_states[message.from_user.id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
    
    await message.edit_text(f"📝 Reply ya Send karein wo message jo `.{shortcut_name}` ke liye save karna hai:")

# --- SAVING MESSAGE ---
@app.on_message(filters.me & ~filters.command(["add"]))
async def save_message(client, message: Message):
    user_id = message.from_user.id
    
    if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[user_id]["shortcut_name"]
        
        if message.text:
            # Database me save/update karna
            cursor.execute("INSERT OR REPLACE INTO notes (keyword, reply) VALUES (?, ?)", (shortcut_name, message.text))
            conn.commit()
            await message.reply_text(f"✅ Saved! Now whenever you type `.{shortcut_name}`, it will trigger.")
        else:
            await message.reply_text("❌ Only text messages are supported currently.")
        
        del user_states[user_id]

# --- TRIGGER: Jab aap chat me '.sam' likhein ---
@app.on_message(filters.text & filters.me & ~filters.edited)
async def trigger_shortcut(client, message: Message):
    text = message.text.strip()
    
    if text.startswith("."):
        shortcut_trigger = text[1:].lower()
        
        # Database se check karna
        cursor.execute("SELECT reply FROM notes WHERE keyword=?", (shortcut_trigger,))
        row = cursor.fetchone()
        
        if row:
            # Pehle '.sam' wale message ko delete karega fir saved text bhejega
            await message.delete()
            await client.send_message(message.chat.id, row[0])

if __name__ == "__main__":
    print("Userbot starting...")
    app.run()
            
