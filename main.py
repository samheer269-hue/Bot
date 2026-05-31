import os
import logging
import asyncio
import time
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client, errors, enums
from pyrogram.types import Message

# Setup high-performance logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZyronPro")

# --- AUTO-UPTIME WEB SERVER ---
def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
        logger.info(f"Zyron Uptime Engine Active on Port {port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Uptime Server Error: {e}")

Thread(target=run_fake_server, daemon=True).start()

# --- CONFIGURATION ENGINE ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()

if not API_ID or not API_HASH or not SESSION_STRING:
    logger.error("CRITICAL ERROR: Environment Variables are Missing!")
    exit(1)

app = Client(
    "zyron",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True
)

# --- CORE HIGH-SPEED MEMORY CACHE ---
shortcuts_db = {}
user_states = {}
shortcut_stats = {}
ME = None

# --- CORE REPLY OPTIMIZER ---
async def reply(message, text):
    """Safely handles target messaging layers without crashing."""
    try:
        if message.text:
            await message.edit_text(text)
        else:
            await message.edit_caption(text)
    except Exception as e:
        logger.error(f"Execution Error in reply abstract: {e}")

async def schedule_send(client, chat_id, name, delay):
    """Asynchronous pipeline for deferred shortcut deployment."""
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
            logger.error(f"Scheduler failed to forward target payload: {e}")

# --- MAIN ENGINE HANDLER ---
@app.on_message()
async def handle(client, message: Message):
    global ME
    try:
        # Strict security validation (Only self-triggered executions processed)
        if not message.from_user or not message.from_user.is_self:
            return

        if ME is None:
            me = await client.get_me()
            ME = me.id

        user_id = message.from_user.id
        chat_id = message.chat.id
        text = (message.text or message.caption or "").strip()

        # --- STATE MACHINE: SHORTCUT CAPTURE FIX ---
        if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
            shortcut_name = user_states[user_id]["shortcut_name"]
            del user_states[user_id]
            try:
                # Instantly sync to private Telegram Cloud storage
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
                
                # FIXED RESPONSE HANDLING (No freezing or missed replies)
                success_log = f"✅ **Saved Successfully!** Use `.{shortcut_name}` anywhere."
                if message.text:
                    await message.edit_text(success_log)
                else:
                    await message.delete()
                    await client.send_message(chat_id, success_log)
            except Exception as e:
                logger.error(f"Save shortcut exception: {e}")
                fail_log = "❌ **Failed to map shortcut. Please try again.**"
                if message.text:
                    await message.edit_text(fail_log)
                else:
                    await message.delete()
                    await client.send_message(chat_id, fail_log)
            return

        if not text:
            return

        # --- COMMAND: .alive ---
        if text.lower() == ".alive":
            await reply(message, "⚡ **Zyron Ultra Pro v3.0** is online and running at full power!")
            return

        # --- COMMAND: .ping ---
        if text.lower() == ".ping":
            start_time = time.time()
            await message.edit_text("⚡ *Measuring matrix latency...*")
            end_time = time.time()
            latency = round((end_time - start_time) * 1000)
            await message.edit_text(f"🚀 **Pong!**\n📶 Speed: `{latency}ms` ")
            return

        # --- COMMAND: .help ---
        if text.lower() == ".help":
            await reply(message, (
                "🦾 **Zyron Pro Userbot — Premium Control Hub**\n\n"
                "🔹 **System Core**\n"
                "`.alive` — Status confirmation\n"
                "`.ping` — Measure exact server response latency\n"
                "`.help` — Open this interactive panel\n\n"
                "🔹 **Shortcut Sub-System**\n"
                "`.a <name>` — Initialize a tracking binding\n"
                "`.list` — Index current active shortcuts\n"
                "`.stats` — Analyze payload delivery metrics\n"
                "`.del <name>` — Delete selected shortcut\n"
                "`.rename <old> <new>` — Change shortcut names instantly\n"
                "`.clear` — Flush all mapped bindings\n"
                "`.s <name> <time>` — Deferred delivery (e.g., `10s`, `5m`, `2h`)\n\n"
                "🔹 **Massive Utility & Destruction**\n"
                "`.block` — Autonomous blocking & wiping (DM/Group Context aware)\n"
                "`.c` — Nuke present chat history completely (BOTH SIDES)\n"
                "`.purgeme <count>` — Self-destruct last 'N' sent texts\n"
                "`.tagall` — Mentions all members using ONLY clean usernames\n"
                "`.leave` — Evacuate current group instantly\n"
                "`.calc <expr>` — High-speed math parsing module\n\n"
                "👉 **Execution Signature:** Type `.<name>` anywhere to trigger."
            ))
            return

        # --- COMMAND: .list ---
        if text.lower() == ".list":
            if not shortcuts_db:
                await reply(message, "❌ **No mapped shortcuts found.** Setup via `.a <name>`")
            else:
                items = "\n".join([f"🔹 `.{k}`" for k in shortcuts_db])
                await reply(message, f"📋 **Current Active Database Index ({len(shortcuts_db)}):**\n\n{items}")
            return

        # --- COMMAND: .stats ---
        if text.lower() == ".stats":
            if not shortcut_stats:
                await reply(message, "📊 **Telemetry logs are completely empty.**")
            else:
                s = sorted(shortcut_stats.items(), key=lambda x: x[1], reverse=True)
                txt = "\n".join([f"🔹 `.{k}` — **{v}** executions" for k, v in s])
                await reply(message, f"📊 **Shortcut Delivery Performance Logs:**\n\n{txt}")
            return

        # --- COMMAND: .clear ---
        if text.lower() == ".clear":
            count = len(shortcuts_db)
            if count == 0:
                await reply(message, "❌ **The indexing database is already clean.**")
            else:
                shortcuts_db.clear()
                shortcut_stats.clear()
                await reply(message, f"🗑️ **Successfully purged all {count} shortcut structures!**")
            return

        # --- COMMAND: .c (BOTH SIDES FULL CHAT NUKE) ---
        if text.lower() == ".c":
            try:
                await message.delete()
                # Deletes the complete structural history for both sides
                await client.delete_chat_history(chat_id, revoke=True)
            except Exception as e:
                logger.error(f"Failed to fully purge chat architecture: {e}")
            return

        # --- COMMAND: .purgeme ---
        if text.startswith(".purgeme "):
            try:
                args = text.split(" ", 1)
                limit = int(args[1]) if len(args) > 1 else 10
                await message.delete()
                
                async for msg in client.get_chat_history(chat_id):
                    if limit <= 0:
                        break
                    if msg.from_user and msg.from_user.is_self:
                        await msg.delete()
                        limit -= 1
            except Exception as e:
                logger.error(f"Purge logic runtime failure: {e}")
            return

        # --- COMMAND: .tagall (FIXED: USERNAME ONLY FORMAT) ---
        if text.lower() == ".tagall":
            try:
                await message.delete()
                mentions = []
                
                async for member in client.get_chat_members(chat_id):
                    if member.user.is_bot or member.user.is_deleted:
                        continue
                    if member.user.username:
                        mentions.append(f"@{member.user.username}")
                
                if not mentions:
                    return
                
                # Batch usernames into groups of 5 to protect account from direct spam filters
                for i in range(0, len(mentions), 5):
                    batch = " ".join(mentions[i:i+5])
                    await client.send_message(chat_id, batch)
                    await asyncio.sleep(0.8)
            except Exception as e:
                logger.error(f"Mass tag handler failed: {e}")
            return

        # --- COMMAND: .block ---
        if text.lower() == ".block":
            target_id = None
            target_name = "User"
            
            if message.chat.type == enums.ChatType.PRIVATE:
                target_id = chat_id
                chat_info = await client.get_chat(chat_id)
                target_name = chat_info.first_name or "Target"
            elif message.reply_to_message and message.reply_to_message.from_user:
                target_id = message.reply_to_message.from_user.id
                target_name = message.reply_to_message.from_user.first_name

            if not target_id:
                await reply(message, "⚠️ **Context Ambiguous:** Run inside a Direct DM or reply to a user's group chat message.")
                return

            try:
                await client.block_user(target_id)
                try:
                    await client.delete_chat_history(target_id, revoke=True)
                except Exception as dm_err:
                    logger.error(f"DM wipe layer bypassed: {dm_err}")
                
                if message.chat.type == enums.ChatType.PRIVATE:
                    await client.send_message(ME, f"🚫 **{target_name}** blacklisted and full logs wiped permanently.")
                else:
                    await reply(message, f"🚫 **{target_name}** blacklisted and full logs wiped permanently.")
            except Exception as e:
                logger.error(f"Failed to isolate target node: {e}")
                await reply(message, "❌ **Error: Execution parameters rejected by API server.**")
            return

        # --- COMMAND: .leave ---
        if text.lower() == ".leave":
            try:
                await reply(message, "👋 **Evacuating chat coordinates immediately...**")
                await asyncio.sleep(1)
                await client.leave_chat(chat_id)
            except Exception as e:
                logger.error(f"Evacuation routine failure: {e}")
                await reply(message, "❌ **Error: Core matrix link could not be severed.**")
            return

        # --- COMMAND: .calc ---
        if text.startswith(".calc "):
            try:
                expr = text.split(" ", 1)[1].strip()
                if not all(c in "0123456789+-*/(). %" for c in expr):
                    await reply(message, "❌ **Security Warning: Blocked disallowed operators.**")
                    return
                result = eval(expr, {"__builtins__": {}})
                await reply(message, f"🧮 Parsing Output:\n`{expr}` = **{result}**")
            except ZeroDivisionError:
                await reply(message, "❌ **Math Singularity: Division by zero triggered.**")
            except Exception:
                await reply(message, "❌ **Syntax Failure: Expression formatting error.**")
            return

        # --- COMMAND: .del ---
        if text.startswith(".del "):
            name = text.split(" ", 1)[1].lower().strip()
            if name in shortcuts_db:
                del shortcuts_db[name]
                shortcut_stats.pop(name, None)
                await reply(message, f"✅ Shortcut key `.{name}` unmapped.")
            else:
                await reply(message, f"❌ Trigger key `.{name}` does not exist.")
            return

        # --- COMMAND: .rename ---
        if text.startswith(".rename "):
            parts = text.split(" ")
            if len(parts) < 3:
                await reply(message, "⚠️ **Syntax Error:** Signature signature is `.rename <old> <new>`")
                return
            old, new = parts[1].lower(), parts[2].lower()
            if old not in shortcuts_db:
                await reply(message, f"❌ Key matching `.{old}` missing from database.")
                return
            if new in shortcuts_db:
                await reply(message, f"❌ Conflict: Target database slot `.{new}` already active.")
                return
            shortcuts_db[new] = shortcuts_db.pop(old)
            shortcut_stats[new] = shortcut_stats.pop(old, 0)
            await reply(message, f"✅ Successfully updated shortcut label: `.{old}` → `.{new}`")
            return

        # --- COMMAND: .a ---
        if text.startswith(".a "):
            name = text.split(" ", 1)[1].lower().strip()
            if not name:
                await reply(message, "⚠️ **Syntax Error:** Signature signature is `.a <name>`")
                return
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": name}
            await reply(message, f"📝 **Listening... Send or forward the payload item you want mapped to `.{name}`**")
            return

        # --- COMMAND: .s ---
        if text.startswith(".s "):
            parts = text.split(" ")
            if len(parts) < 3:
                await reply(message, "⚠️ **Syntax Error:** Signature layout is `.s <name> <10s/5m/2h>`")
                return
            name = parts[1].lower()
            time_str = parts[2].lower()
            if name not in shortcuts_db:
                await reply(message, f"❌ Verification Error: Key `.{name}` unmapped.")
                return
            try:
                if time_str.endswith("s"):
                    delay = int(time_str[:-1])
                elif time_str.endswith("m"):
                    delay = int(time_str[:-1]) * 60
                elif time_str.endswith("h"):
                    delay = int(time_str[:-1]) * 3600
                else:
                    await reply(message, "⚠️ **Invalid Suffix Variable:** Target format requires `10s`, `5m`, or `2h` layouts.")
                    return
                await reply(message, f"⏳ **Task Cached:** Injecting payload `.{name}` automatically in **{time_str}**.")
                asyncio.create_task(schedule_send(client, chat_id, name, delay))
            except Exception:
                await reply(message, "❌ **Operational Execution Failure: Timed scheduler rejected structural configurations.**")
            return

        # --- ENHANCED GENERAL SHORTCUT INJECTOR ---
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
                    logger.error(f"Shortcut dispatcher execution failure: {e}")
                    try:
                        await client.send_message(chat_id, f"❌ **Error: Link failure, failed to mirror payload mapping `.{trigger}`**")
                    except Exception:
                        pass

    except errors.FloodWait as e:
        logger.warning(f"API Limit Hit! Cooling down execution layers for {e.value}s")
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Global thread execution error: {e}")

if __name__ == "__main__":
    logger.info("Assembling Zyron Framework Core Architecture...")
    app.run()
                
