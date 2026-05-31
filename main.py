import os
import logging
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client, errors
from pyrogram.types import Message
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Userbot")

def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
        logger.info(f"Port {port} active")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Server error: {e}")

Thread(target=run_fake_server, daemon=True).start()

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()

if not API_ID or not API_HASH or not SESSION_STRING:
    logger.error("API_ID, API_HASH or SESSION_STRING missing!")
    exit(1)

app = Client(
    "zyron",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True
)

shortcuts_db = {}
user_states = {}
shortcut_stats = {}
ME = None

async def reply(message, text):
    try:
        if message.text:
            await message.edit_text(text)
        else:
            await message.edit_caption(text)
    except Exception as e:
        logger.error(f"Reply failed: {e}")

async def schedule_send(client, chat_id, name, delay):
    await asyncio.sleep(delay)
    if name in shortcuts_db:
        data = shortcuts_db[name]
        try:
            await client.copy_message(
                chat_id=chat_id,
                from_chat_id=data["saved_chat_id"],
                message_id=data["saved_msg_id"]
            )
            shortcut_stats[name] = shortcut_stats.get(name, 0) + 1
        except Exception as e:
            logger.error(f"Schedule error: {e}")

@app.on_message()
async def handle(client, message: Message):
    global ME
    try:
        if not message.from_user or not message.from_user.is_self:
            return

        if ME is None:
            me = await client.get_me()
            ME = me.id

        user_id = message.from_user.id
        chat_id = message.chat.id
        text = (message.text or message.caption or "").strip()

        # --- SAVE STATE ---
        if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
            shortcut_name = user_states[user_id]["shortcut_name"]
            del user_states[user_id]
            try:
                fwd = await client.copy_message(
                    chat_id=ME,
                    from_chat_id=message.chat.id,
                    message_id=message.id
                )
                shortcuts_db[shortcut_name] = {
                    "saved_chat_id": ME,
                    "saved_msg_id": fwd.id
                }
                shortcut_stats[shortcut_name] = 0
                await reply(message, f"✅ **Saved!** Use `.{shortcut_name}` anywhere.")
            except Exception as e:
                logger.error(f"Save error: {e}")
                await reply(message, "❌ Failed to save. Try again.")
            return

        if not text:
            return

        # --- .alive ---
        if text.lower() == ".alive":
            await reply(message, "✨ **Zyron Userbot** is Active and Running!")
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
                "`.block` — Block replied user + clear DM\n"
                "`.c` — Clear current chat history\n"
                "`.leave` — Leave current group\n"
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

        # --- .c (clear current chat history) ---
        if text.lower() == ".c":
            try:
                await message.delete()
                await client.delete_chat_history(chat_id)
            except Exception as e:
                logger.error(f"Clear chat error: {e}")
            return

        # --- .block (block + clear DM + delete tag msg in group) ---
        if text.lower() == ".block":
            if not message.reply_to_message:
                await reply(message, "⚠️ Reply to a user's message to block them.")
                return
            target = message.reply_to_message.from_user
            if not target:
                await reply(message, "❌ Could not identify user.")
                return
            try:
                # Block the user
                await client.block_user(target.id)

                # Clear DM with that user
                try:
                    await client.delete_chat_history(target.id)
                except Exception as e:
                    logger.error(f"DM clear error: {e}")

                await reply(message, f"🚫 **{target.first_name}** blocked and DM cleared.")
            except Exception as e:
                logger.error(f"Block error: {e}")
                await reply(message, "❌ Failed to block.")
            return

        # --- .leave (leave current group) ---
        if text.lower() == ".leave":
            try:
                await reply(message, "👋 **Leaving this group...**")
                await asyncio.sleep(1)
                await client.leave_chat(chat_id)
            except Exception as e:
                logger.error(f"Leave error: {e}")
                await reply(message, "❌ Failed to leave group.")
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

        # --- .del ---
        if text.startswith(".del "):
            name = text.split(" ", 1)[1].lower().strip()
            if name in shortcuts_db:
                del shortcuts_db[name]
                shortcut_stats.pop(name, None)
                await reply(message, f"✅ `.{name}` deleted.")
            else:
                await reply(message, f"❌ `.{name}` not found!")
            return

        # --- .rename ---
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

        # --- .a ---
        if text.startswith(".a "):
            name = text.split(" ", 1)[1].lower().strip()
            if not name:
                await reply(message, "⚠️ Usage: `.a <name>`")
                return
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": name}
            await reply(message, f"📝 **Send the message or photo to save as `.{name}`**")
            return

        # --- .s ---
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
                await reply(message, "❌ Invalid time format.")
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
                        from_chat_id=data["saved_chat_id"],
                        message_id=data["saved_msg_id"],
                        reply_to_message_id=reply_to
                    )
                    shortcut_stats[trigger] = shortcut_stats.get(trigger, 0) + 1
                except Exception as e:
                    logger.error(f"Trigger error: {e}")
                    try:
                        await client.send_message(chat_id, f"❌ Could not send `.{trigger}`.")
                    except Exception:
                        pass

    except errors.FloodWait as e:
        logger.warning(f"FloodWait: sleeping {e.value}s")
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Handler error: {e}")

if __name__ == "__main__":
    logger.info("Starting Zyron Userbot...")
    app.run()
