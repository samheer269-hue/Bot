import os
import logging
import asyncio
import time
from threading import Thread
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pyrogram import Client, errors, enums
from pyrogram.types import Message

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZyronX")

# --- FAKE SERVER FOR UPTIME PINGS ---
def run_fake_server():
    port = int(os.environ.get("PORT", 8080))
    try:
        httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
        logger.info(f"Uptime port {port} activated successfully.")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Server initialization error: {e}")

Thread(target=run_fake_server, daemon=True).start()

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "").strip()

if not API_ID or not API_HASH or not SESSION_STRING:
    logger.error("API_ID, API_HASH or SESSION_STRING missing! Exiting...")
    exit(1)

app = Client(
    "zyron",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    in_memory=True
)

# --- IN-MEMORY STORAGE ---
shortcuts_db = {}
user_states = {}
shortcut_stats = {}
ME = None

# --- HELPER FUNCTIONS ---
async def reply(message, text):
    """Edits text if message has text, otherwise edits the media caption cleanly."""
    try:
        if message.text:
            await message.edit_text(text)
        else:
            await message.edit_caption(text)
    except Exception as e:
        logger.error(f"Reply abstraction failed: {e}")

async def schedule_send(client, chat_id, name, delay):
    """Executes deferred message delivery for scheduled shortcuts."""
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
            logger.error(f"Schedule engine exception: {e}")

# --- MAIN MESSAGE HANDLER ---
@app.on_message()
async def handle(client, message: Message):
    global ME
    try:
        # Strict validation: Only processing messages triggered by the account owner
        if not message.from_user or not message.from_user.is_self:
            return

        # Dynamically cache personal User ID
        if ME is None:
            me = await client.get_me()
            ME = me.id

        user_id = message.from_user.id
        chat_id = message.chat.id
        text = (message.text or message.caption or "").strip()

        # --- STATE MACHINE: INTERCEPT & SAVE SHORTCUT ---
        if user_id in user_states and user_states[user_id]["action"] == "waiting_for_msg":
            shortcut_name = user_states[user_id]["shortcut_name"]
            del user_states[user_id]
            try:
                # Store the reference safely within account cloud 'Saved Messages'
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
                
                # Context-Aware Confirmation Logic (Fixes Media vs Text glitch)
                conf_text = f"✅ **Saved Successfully!** Use `.{shortcut_name}` anywhere."
                if message.text:
                    await message.edit_text(conf_text)
                else:
                    await message.delete()
                    await client.send_message(chat_id, conf_text)

            except Exception as e:
                logger.error(f"Interception engine save crash: {e}")
                err_msg = "❌ **Failed to register shortcut. Try again.**"
                if message.text:
                    await message.edit_text(err_msg)
                else:
                    await message.delete()
                    await client.send_message(chat_id, err_msg)
            return

        if not text:
            return

        # --- COMMAND: .alive ---
        if text.lower() == ".alive":
            await reply(message, "✨ **Zyron Userbot v2.0** is operational and cruising smoothly!")
            return

        # --- COMMAND: .ping (NEW FUNCTIONALITY) ---
        if text.lower() == ".ping":
            start_time = time.time()
            await message.edit_text("⚡ *Checking structural synchronization...*")
            end_time = time.time()
            latency = round((end_time - start_time) * 1000)
            await message.edit_text(f"🚀 **Pong!**\n📶 Latency: `{latency}ms` ")
            return

        # --- COMMAND: .help ---
        if text.lower() == ".help":
            await reply(message, (
                "🤖 **Zyron Userbot — Enhanced Command Desk**\n\n"
                "🔹 **Core Navigation**\n"
                "`.alive` — Quick status ping\n"
                "`.ping` — Measure framework latency\n"
                "`.help` — Open this interactive diagnostic menu\n\n"
                "🔹 **Shortcut Manager**\n"
                "`.a <name>` — Hook incoming item to a trigger shortcut\n"
                "`.list` — Index all active bindings\n"
                "`.stats` — Review shortcut performance analytics\n"
                "`.del <name>` — Sever target shortcut binding\n"
                "`.rename <old> <new>` — Hot-swap identifier tags\n"
                "`.clear` — Flush full dictionary index\n"
                "`.s <name> <time>` — Queue shortcut delivery (e.g., `10s`, `5m`, `2h`)\n\n"
                "🔹 **Moderation & Utility Extensions**\n"
                "`.block` — Autonomous target isolation (Bina reply ke DM block!)\n"
                "`.c` — Nuke present window log memory\n"
                "`.purgeme <count>` — Self-destruct last 'N' sent texts\n"
                "`.tagall <text>` — Tag group members instantly\n"
                "`.leave` — Evacuate current chat matrix\n"
                "`.calc <expr>` — Clean arithmetic processing engine\n\n"
                "👉 **Shortcut Deployment:** Simply type `.<name>` anywhere."
            ))
            return

        # --- COMMAND: .list ---
        if text.lower() == ".list":
            if not shortcuts_db:
                await reply(message, "❌ **No active bindings discovered.** Initialize one with `.a <name>`")
            else:
                items = "\n".join([f"🔹 `.{k}`" for k in shortcuts_db])
                await reply(message, f"📋 **Active Bindings Database ({len(shortcuts_db)}):**\n\n{items}")
            return

        # --- COMMAND: .stats ---
        if text.lower() == ".stats":
            if not shortcut_stats:
                await reply(message, "📊 **No analytical usage telemetry records available yet.**")
            else:
                s = sorted(shortcut_stats.items(), key=lambda x: x[1], reverse=True)
                txt = "\n".join([f"🔹 `.{k}` — **{v}** call(s)" for k, v in s])
                await reply(message, f"📊 **Shortcut Structural Performance Metrics:**\n\n{txt}")
            return

        # --- COMMAND: .clear ---
        if text.lower() == ".clear":
            count = len(shortcuts_db)
            if count == 0:
                await reply(message, "❌ **Dictionary mapping index is already barren.**")
            else:
                shortcuts_db.clear()
                shortcut_stats.clear()
                await reply(message, f"🗑️ **Successfully flushed {count} tracking record allocations!**")
            return

        # --- COMMAND: .c (Clear History) ---
        if text.lower() == ".c":
            try:
                await message.delete()
                await client.delete_chat_history(chat_id)
            except Exception as e:
                logger.error(f"History purge failure: {e}")
            return

        # --- COMMAND: .purgeme (NEW FUNCTIONALITY) ---
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
                logger.error(f"Self-clean operation error: {e}")
            return

        # --- COMMAND: .tagall (NEW FUNCTIONALITY) ---
        if text.startswith(".tagall"):
            try:
                args = text.split(" ", 1)
                announcement = args[1] if len(args) > 1 else "Attention Required!"
                await message.delete()
                
                mentions = ""
                counter = 0
                async for member in client.get_chat_members(chat_id):
                    if member.user.is_bot or member.user.is_deleted:
                        continue
                    mentions += f"[{member.user.first_name}](tg://user?id={member.user.id}) "
                    counter += 1
                    
                    if counter >= 5: # Batches tags to bypass severe spam filters smoothly
                        await client.send_message(chat_id, f"📢 {announcement}\n\n{mentions}")
                        mentions = ""
                        counter = 0
                        await asyncio.sleep(1)
                if mentions:
                    await client.send_message(chat_id, f"📢 {announcement}\n\n{mentions}")
            except Exception as e:
                logger.error(f"Broadcast operation failed: {e}")
            return

        # --- COMMAND: .block (RE-ENGINEERED SMART INTERACTION) ---
        if text.lower() == ".block":
            target_id = None
            target_name = "User"
            
            # Smart Choice: Direct DM check vs Reply system block
            if message.chat.type == enums.ChatType.PRIVATE:
                target_id = chat_id
                chat_info = await client.get_chat(chat_id)
                target_name = chat_info.first_name or "Targeted Identity"
            elif message.reply_to_message and message.reply_to_message.from_user:
                target_id = message.reply_to_message.from_user.id
                target_name = message.reply_to_message.from_user.first_name

            if not target_id:
                await reply(message, "⚠️ **Context Ambiguous:** Either run this command directly inside a private DM, or reply to a member's comment inside a community.")
                return

            try:
                await client.block_user(target_id)
                try:
                    await client.delete_chat_history(target_id)
                except Exception as dm_err:
                    logger.error(f"Isolated history purge bypass: {dm_err}")
                
                if message.chat.type == enums.ChatType.PRIVATE:
                    # DM context handles direct notifications safely
                    await client.send_message(ME, f"🚫 **{target_name}** successfully blacklisted and logs cleared.")
                else:
                    await reply(message, f"🚫 **{target_name}** blacklisted and localized history purged.")
            except Exception as e:
                logger.error(f"Blacklist structural execution error: {e}")
                await reply(message, "❌ **Account isolation parameters rejected. Operation aborted.**")
            return

        # --- COMMAND: .leave ---
        if text.lower() == ".leave":
            try:
                await reply(message, "👋 **Evacuating chat coordinates immediately...**")
                await asyncio.sleep(1)
                await client.leave_chat(chat_id)
            except Exception as e:
                logger.error(f"Evacuation operation crashed: {e}")
                await reply(message, "❌ **Matrix failure: Unable to break active group connection.**")
            return

        # --- COMMAND: .calc ---
        if text.startswith(".calc "):
            try:
                expr = text.split(" ", 1)[1].strip()
                if not all(c in "0123456789+-*/(). %" for c in expr):
                    await reply(message, "❌ **Security Breach: Disallowed arithmetic operators injected.**")
                    return
                result = eval(expr, {"__builtins__": {}})
                await reply(message, f"🧮 Logic Engine Result:\n`{expr}` = **{result}**")
            except ZeroDivisionError:
                await reply(message, "❌ **Mathematical Singularity: Division by Zero detected.**")
            except Exception:
                await reply(message, "❌ **Syntax Parsing Failure: Evaluate expression configurations again.**")
            return

        # --- COMMAND: .del ---
        if text.startswith(".del "):
            name = text.split(" ", 1)[1].lower().strip()
            if name in shortcuts_db:
                del shortcuts_db[name]
                shortcut_stats.pop(name, None)
                await reply(message, f"✅ Target binding trace `.{name}` dropped.")
            else:
                await reply(message, f"❌ Trigger key `.{name}` not registered.")
            return

        # --- COMMAND: .rename ---
        if text.startswith(".rename "):
            parts = text.split(" ")
            if len(parts) < 3:
                await reply(message, "⚠️ **Syntax Error:** Proper signature layout is `.rename <old> <new>`")
                return
            old, new = parts[1].lower(), parts[2].lower()
            if old not in shortcuts_db:
                await reply(message, f"❌ Identifier key `.{old}` does not exist.")
                return
            if new in shortcuts_db:
                await reply(message, f"❌ Collision warning: Target slot `.{new}` already occupied.")
                return
            shortcuts_db[new] = shortcuts_db.pop(old)
            shortcut_stats[new] = shortcut_stats.pop(old, 0)
            await reply(message, f"✅ Successful migration: `.{old}` smoothly assigned to `.{new}`")
            return

        # --- COMMAND: .a (Assign Shortcut) ---
        if text.startswith(".a "):
            name = text.split(" ", 1)[1].lower().strip()
            if not name:
                await reply(message, "⚠️ **Syntax Error:** Signature layout is `.a <name>`")
                return
            user_states[user_id] = {"action": "waiting_for_msg", "shortcut_name": name}
            await reply(message, f"📝 **Awaiting target structural item delivery... Send or forward the file/text to mount as `.{name}`**")
            return

        # --- COMMAND: .s (Schedule Delivery) ---
        if text.startswith(".s "):
            parts = text.split(" ")
            if len(parts) < 3:
                await reply(message, "⚠️ **Syntax Error:** Signature layout is `.s <name> <10s/5m/2h>`")
                return
            name = parts[1].lower()
            time_str = parts[2].lower()
            if name not in shortcuts_db:
                await reply(message, f"❌ Verification failure: Trigger key `.{name}` not indexed.")
                return
            try:
                if time_str.endswith("s"):
                    delay = int(time_str[:-1])
                elif time_str.endswith("m"):
                    delay = int(time_str[:-1]) * 60
                elif time_str.endswith("h"):
                    delay = int(time_str[:-1]) * 3600
                else:
                    await reply(message, "⚠️ **Invalid Time Variable Format:** Use suffixes matching `10s`, `5m`, or `2h`")
                    return
                await reply(message, f"⏳ **Task Scheduled:** Dispatching `.{name}` automatically in **{time_str}**.")
                asyncio.create_task(schedule_send(client, chat_id, name, delay))
            except Exception:
                await reply(message, "❌ **Payload operational parameters failed. Check configurations.**")
            return

        # --- GENERAL SHORTCUT TRIGGER DEPLOYER ---
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
                    logger.error(f"Deployment matrix exception: {e}")
                    try:
                        await client.send_message(chat_id, f"❌ **Unable to properly deploy content cluster for payload mapping `.{trigger}`.**")
                    except Exception:
                        pass

    except errors.FloodWait as e:
        logger.warning(f"Rate Limiter warning hit! Pausing operations for {e.value}s")
        await asyncio.sleep(e.value)
    except Exception as e:
        logger.error(f"Global thread runner exception: {e}")

if __name__ == "__main__":
    logger.info("Initializing Zyron Framework Modules...")
    app.run()
