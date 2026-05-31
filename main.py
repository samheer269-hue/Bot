import os
import logging
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client
from pyrogram.types import Message
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

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

shortcuts_db = {}
user_states = {}
shortcut_stats = {}

async def reply(message, text):
    """Edit text message in place. For media, edit caption."""
    try:
        if message.text:
            await message.edit_text(text)
        else:
            await message.edit_caption(text)
    except Exception as e:
        logger.error(f"Reply failed: {e}")

async def schedule_send(client, chat_id, shortcut_name, delay):
    await asyncio.sleep(delay)
    if shortcut_name in shortcuts_db:
        data = shortcuts_db[shortcut_name]
        try:
            await client.copy_message(
                chat_id=chat_id,
                from_chat_id=data["chat_id"],
                message_id=data["message_id"]
            )
            shortcut_stats[shortcut_name] = shortcut_stats.get(shortcut_name, 0) + 1
        except Exception as e:
            logger.error(f"Schedule send error: {e}")

@app.on_message()
async def handle(client, message: Message):
    if not message.from_user or not message.from_user.is_self:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    text = (message.text or message.caption or "").strip()

    # --- SAVE STATE: accept any message (text or media) ---
    if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[user_id]["shortcut_name"]
        del user_states[user_id]

        # Save the reference
        shortcuts_db[shortcut_name] = {
            "chat_id": message.chat.id,
            "message_id": message.id
        }
        shortcut_stats[shortcut_name] = 0

        # Send confirmation as new message, then delete after 3s
        try:
            confirm = await client.send_message(chat_id, f"✅ **Saved!** Use `.{shortcut_name}` anywhere.")
            await asyncio.sleep(3)
            await confirm.delete()
        except Exception as e:
            logger.error(f"Confirm error: {e}")
        return

    if not text:
        return

    # --- .alive ---
    if text.lower() == ".alive":
        await reply(message, "✨ **Zyron Userbot** is Active!")
        return

    # --- .help ---
    if text.lower() == ".help":
        await reply(message, (
            "🤖 **Zyron Userbot — Commands**\n\n"
            "`.alive` — Status check\n"
            "`.a <name>` — Save shortcut\n"
            "`.list` — All shortcuts\n"
            "`.stats` — Usage count\n"
            "`.del <name>` — Delete shortcut\n"
            "`.rename <old> <new>` — Rename shortcut\n"
            "`.clear` — Clear all shortcuts\n"
            "`.s <name> <10s/5m/2h>` — Schedule shortcut\n"
            "`.calc <expr>` — Calculator\n"
            "`.block` — Block replied user\n"
            "`.c` — Clear chat history\n"
            "`.help` — This menu\n\n"
            "**Shortcut trigger:** Type `.name`"
        ))
        return

    # --- .list ---
    if text.lower() == ".list":
        if not shortcuts_db:
            await reply(message, "❌ No shortcuts found! Use `.a <name>` to create one.")
        else:
            items = "\n".join([f"🔹 `.{k}`" for k in shortcuts_db])
            await reply(message, f"📋 **Shortcuts ({len(shortcuts_db)}):**\n\n{items}")
        return

    # --- .stats ---
    if text.lower() == ".stats":
        if not shortcut_stats:
            await reply(message, "📊 No usage data yet.")
        else:
            s = sorted(shortcut_stats.items(), key=lambda x: x[1], reverse=True)
            txt = "\n".join([f"🔹 `.{k}` — **{v}** use(s)" for k, v in s])
            await reply(message, f"📊 **Usage Stats:**\n\n{txt}")
        return

    # --- .clear ---
    if text.lower() == ".clear":
        count = len(shortcuts_db)
        if count == 0:
            await reply(message, "❌ No shortcuts to clear!")
        else:
            shortcuts_db.clear()
            shortcut_stats.clear()
            await reply(message, f"🗑️ **{count} shortcut(s) cleared!**")
        return

    # --- .c (clear chat history) ---
    if text.lower() == ".c":
        try:
            await message.delete()
            await client.delete_chat_history(chat_id)
        except Exception as e:
            logger.error(f"Clear chat error: {e}")
        return

    # --- .block ---
    if text.lower() == ".block":
        if not message.reply_to_message:
            await reply(message, "⚠️ Reply to a user to block them.")
            return
        target = message.reply_to_message.from_user
        if not target:
            await reply(message, "❌ Could not identify user.")
            return
        try:
            await client.block_user(target.id)
            await reply(message, f"🚫 **{target.first_name}** blocked.")
        except Exception as e:
            logger.error(f"Block error: {e}")
            await reply(message, "❌ Failed to block.")
        return

    # --- .calc ---
    if text.startswith(".calc "):
        try:
            expr = text.split(" ", 1)[1].strip()
            if not all(c in "0123456789+-*/(). %" for c in expr):
                await reply(message, "❌ Invalid characters.")
                return
            result = eval(expr, {"__builtins__": {}})
            await reply(message, f"🧮 `{expr}` = **{result}**")
        except ZeroDivisionError:
            await reply(message, "❌ Division by zero!")
        except Exception:
            await reply(message, "❌ Invalid expression.")
        return

    # --- .del <name> ---
    if text.startswith(".del "):
        name = text.split(" ", 1)[1].lower().strip()
        if name in shortcuts_db:
            del shortcuts_db[name]
            shortcut_stats.pop(name, None)
            await reply(message, f"✅ `.{name}` deleted.")
        else:
            await reply(message, f"❌ `.{name}` not found!")
        return

    # --- .rename <old> <new> ---
    if text.startswith(".rename "):
        parts = text.split(" ")
        if len(parts) < 3:
            await reply(message, "⚠️ Usage: `.rename <old> <new>`")
            return
        old, new = parts[1].lower(), parts[2].lower()
        if old not in shortcuts_db:
            await reply(message, f"❌ `.{old}` not found!")
            return
        if new in shortcuts_db:
            await reply(message, f"❌ `.{new}` already exists!")
            return
        shortcuts_db[new] = shortcuts_db.pop(old)
        shortcut_stats[new] = shortcut_stats.pop(old, 0)
        await reply(message, f"✅ `.{old}` → `.{new}`")
        return

    # --- .a <name> ---
    if text.startswith(".a "):
        name = text.split(" ", 1)[1].lower().strip()
        user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": name}
        await reply(message, f"📝 **Send the message or photo to save as `.{name}`**")
        return

    # --- .s <name> <time> ---
    if text.startswith(".s "):
        parts = text.split(" ")
        if len(parts) < 3:
            await reply(message, "⚠️ Usage: `.s <name> <10s/5m/2h>`")
            return
        name = parts[1].lower()
        time_str = parts[2].lower()
        if name not in shortcuts_db:
            await reply(message, f"❌ `.{name}` not found!")
            return
        try:
            if time_str.endswith("s"):
                delay = int(time_str[:-1])
            elif time_str.endswith("m"):
                delay = int(time_str[:-1]) * 60
            elif time_str.endswith("h"):
                delay = int(time_str[:-1]) * 3600
            else:
                await reply(message, "⚠️ Format: `10s`, `5m`, `2h`")
                return
            await reply(message, f"⏳ `.{name}` sending in **{time_str}**.")
            asyncio.create_task(schedule_send(client, chat_id, name, delay))
        except Exception:
            await reply(message, "❌ Invalid time.")
        return

    # --- SHORTCUT TRIGGER ---
    if text.startswith("."):
        trigger = text[1:].lower().strip()
        if trigger in shortcuts_db:
            data = shortcuts_db[trigger]
            reply_to = message.reply_to_message.id if message.reply_to_message else None
            try:
                await message.delete()
                await client.copy_message(
                    chat_id=chat_id,
                    from_chat_id=data["chat_id"],
                    message_id=data["message_id"],
                    reply_to_message_id=reply_to
                )
                shortcut_stats[trigger] = shortcut_stats.get(trigger, 0) + 1
            except Exception as e:
                logger.error(f"Trigger error: {e}")
                try:
                    await client.send_message(chat_id, f"❌ Could not send `.{trigger}`. Original may be deleted.")
                except:
                    pass
        return

if __name__ == "__main__":
    logger.info("Starting Zyron Userbot...")
    app.run()
