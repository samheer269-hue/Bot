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

async def safe_reply(client, message, text):
    """Only for pure text command messages — edit in place."""
    if message.text:
        try:
            await message.edit_text(text)
            return
        except Exception as e:
            logger.error(f"Edit failed: {e}")
    else:
        try:
            await message.edit_caption(text)
            return
        except Exception as e:
            logger.error(f"Caption edit failed: {e}")
    logger.warning("Could not respond — slow mode or media restriction.")

async def safe_confirm(client, chat_id, text):
    """For confirmations after save/delete — always sends a fresh message."""
    try:
        sent = await client.send_message(chat_id, text)
        # Auto delete confirmation after 4 seconds
        await asyncio.sleep(4)
        await sent.delete()
    except Exception as e:
        logger.error(f"Confirm send failed: {e}")

async def schedule_send(client, chat_id, shortcut_name, delay_seconds):
    await asyncio.sleep(delay_seconds)
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
            logger.error(f"Scheduled send error: {e}")

@app.on_message()
async def handle_all_messages(client, message: Message):
    if not message.from_user or not message.from_user.is_self:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    raw_text = message.text or message.caption or ""
    text = raw_text.strip()

    # --- STATE: WAITING FOR MESSAGE TO SAVE ---
    if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
        shortcut_name = user_states[user_id]["shortcut_name"]

        shortcuts_db[shortcut_name] = {
            "chat_id": message.chat.id,
            "message_id": message.id
        }
        shortcut_stats[shortcut_name] = 0
        del user_states[user_id]

        # Send fresh confirmation — dont touch saved message
        asyncio.create_task(safe_confirm(client, chat_id, f"✅ **Saved!** Use `.{shortcut_name}` anywhere."))
        return

    if not text:
        return

    # --- .alive ---
    if text.lower() == ".alive":
        await safe_reply(client, message, "✨ **Zyron Userbot** is Active and Running Smoothly!")
        return

    # --- .help ---
    if text.lower() == ".help":
        help_text = (
            "🤖 **Zyron Userbot — Commands**\n\n"
            "`.alive` — Check bot status\n"
            "`.a <name>` — Create a new shortcut\n"
            "`.list` — View all shortcuts\n"
            "`.del <name>` — Delete a shortcut\n"
            "`.rename <old> <new>` — Rename a shortcut\n"
            "`.clear` — Delete all shortcuts\n"
            "`.stats` — View shortcut usage count\n"
            "`.s <name> <Xs/Xm/Xh>` — Schedule a shortcut\n"
            "`.block` — Block the replied user\n"
            "`.c` — Clear current chat history\n"
            "`.calc <expression>` — Calculator\n"
            "`.help` — Show this menu\n\n"
            "**To use a shortcut:** Just type `.name`"
        )
        await safe_reply(client, message, help_text)
        return

    # --- .list ---
    if text.lower() == ".list":
        if not shortcuts_db:
            msg = "❌ No shortcuts found! Use `.a <name>` to create one."
        else:
            shortcuts_list = "\n".join([f"🔹 `.{k}`" for k in shortcuts_db.keys()])
            msg = f"📋 **Your Saved Shortcuts ({len(shortcuts_db)}):**\n\n{shortcuts_list}"
        await safe_reply(client, message, msg)
        return

    # --- .stats ---
    if text.lower() == ".stats":
        if not shortcut_stats:
            await safe_reply(client, message, "📊 No usage data yet.")
        else:
            sorted_stats = sorted(shortcut_stats.items(), key=lambda x: x[1], reverse=True)
            stats_text = "\n".join([f"🔹 `.{k}` — used **{v}** time(s)" for k, v in sorted_stats])
            await safe_reply(client, message, f"📊 **Shortcut Usage Stats:**\n\n{stats_text}")
        return

    # --- .clear ---
    if text.lower() == ".clear":
        count = len(shortcuts_db)
        if count == 0:
            await safe_reply(client, message, "❌ No shortcuts to clear!")
        else:
            shortcuts_db.clear()
            shortcut_stats.clear()
            await safe_reply(client, message, f"🗑️ **{count} shortcut(s) deleted!** Database cleared.")
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
        try:
            if not message.reply_to_message:
                await safe_reply(client, message, "⚠️ Reply to a user's message to block them.")
                return
            target_user = message.reply_to_message.from_user
            if not target_user:
                await safe_reply(client, message, "❌ Could not identify the user.")
                return
            await client.block_user(target_user.id)
            await safe_reply(client, message, f"🚫 **{target_user.first_name}** has been blocked.")
        except Exception as e:
            logger.error(f"Block error: {e}")
            await safe_reply(client, message, "❌ Failed to block user.")
        return

    # --- .calc ---
    if text.startswith(".calc "):
        try:
            expression = text.split(" ", 1)[1].strip()
            allowed = set("0123456789+-*/(). %")
            if not all(c in allowed for c in expression):
                await safe_reply(client, message, "❌ Invalid characters in expression.")
                return
            result = eval(expression, {"__builtins__": {}})
            await safe_reply(client, message, f"🧮 `{expression}` = **{result}**")
        except ZeroDivisionError:
            await safe_reply(client, message, "❌ Division by zero!")
        except Exception:
            await safe_reply(client, message, "❌ Invalid expression.")
        return

    # --- .del <name> ---
    if text.startswith(".del "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower().strip()
            if shortcut_name in shortcuts_db:
                del shortcuts_db[shortcut_name]
                shortcut_stats.pop(shortcut_name, None)
                msg = f"✅ `.{shortcut_name}` deleted successfully."
            else:
                msg = f"❌ `.{shortcut_name}` not found!"
        except Exception as e:
            logger.error(f"Del error: {e}")
            msg = "❌ An error occurred."
        await safe_reply(client, message, msg)
        return

    # --- .rename <old> <new> ---
    if text.startswith(".rename "):
        try:
            parts = text.split(" ")
            if len(parts) < 3:
                await safe_reply(client, message, "⚠️ Usage: `.rename <old_name> <new_name>`")
                return
            old_name = parts[1].lower().strip()
            new_name = parts[2].lower().strip()
            if old_name not in shortcuts_db:
                await safe_reply(client, message, f"❌ `.{old_name}` not found!")
                return
            if new_name in shortcuts_db:
                await safe_reply(client, message, f"❌ `.{new_name}` already exists! Delete it first.")
                return
            shortcuts_db[new_name] = shortcuts_db.pop(old_name)
            if old_name in shortcut_stats:
                shortcut_stats[new_name] = shortcut_stats.pop(old_name)
            await safe_reply(client, message, f"✅ `.{old_name}` renamed to `.{new_name}` successfully.")
        except Exception as e:
            logger.error(f"Rename error: {e}")
            await safe_reply(client, message, "❌ An error occurred.")
        return

    # --- .a <name> ---
    if text.startswith(".a ") or text.startswith("/a "):
        try:
            shortcut_name = text.split(" ", 1)[1].lower().strip()
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": shortcut_name}
            await safe_reply(client, message, f"📝 **Send the message or photo to save as `.{shortcut_name}`**\n*(Supports photos, media, and formatting)*")
        except Exception as e:
            logger.error(f"Add error: {e}")
        return

    # --- .s <name> <time> ---
    if text.startswith(".s "):
        try:
            parts = text.split(" ")
            if len(parts) < 3:
                await safe_reply(client, message, "⚠️ Usage: `.s <name> <10s / 5m / 2h>`")
                return
            shortcut_name = parts[1].lower().strip()
            time_str = parts[2].lower().strip()

            if shortcut_name not in shortcuts_db:
                await safe_reply(client, message, f"❌ `.{shortcut_name}` not found!")
                return

            if time_str.endswith("s"):
                delay = int(time_str[:-1])
            elif time_str.endswith("m"):
                delay = int(time_str[:-1]) * 60
            elif time_str.endswith("h"):
                delay = int(time_str[:-1]) * 3600
            else:
                await safe_reply(client, message, "⚠️ Time format: `10s`, `5m`, `2h`")
                return

            await safe_reply(client, message, f"⏳ `.{shortcut_name}` will be sent in **{time_str}**.")
            asyncio.create_task(schedule_send(client, chat_id, shortcut_name, delay))
        except Exception as e:
            logger.error(f"Schedule error: {e}")
            await safe_reply(client, message, "❌ An error occurred.")
        return

    # --- SHORTCUT TRIGGER ---
    if text.startswith("."):
        shortcut_trigger = text[1:].lower().strip()
        if shortcut_trigger in shortcuts_db:
            data = shortcuts_db[shortcut_trigger]
            reply_to_id = message.reply_to_message.id if message.reply_to_message else None
            try:
                await message.delete()
                await client.copy_message(
                    chat_id=chat_id,
                    from_chat_id=data["chat_id"],
                    message_id=data["message_id"],
                    reply_to_message_id=reply_to_id
                )
                shortcut_stats[shortcut_trigger] = shortcut_stats.get(shortcut_trigger, 0) + 1
            except Exception as e:
                logger.error(f"Shortcut error: {e}")
                try:
                    await message.edit_text(f"❌ Could not send `.{shortcut_trigger}`. Original message may have been deleted.")
                except:
                    pass
            return

if __name__ == "__main__":
    logger.info("Starting Fully Loaded Userbot...")
    app.run()
