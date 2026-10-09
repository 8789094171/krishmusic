import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatAction, Chat
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import yt_dlp

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
}

# Bot owner ID (change this to your Telegram user ID)
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))

# Data storage
user_data: Dict[int, Dict[str, any]] = {}
groups: Dict[int, Dict[str, any]] = {}
broadcast_list: List[int] = []
clone_bots: Dict[str, str] = {}  # clone_name: bot_token


def get_audio_info(url: str) -> Optional[dict]:
    """Fetch audio info from YouTube URL"""
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            return {
                "title": info.get("title", "Unknown Track"),
                "url": info.get("webpage_url") or url,
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader", "Unknown"),
            }
    except Exception as e:
        logger.exception("Failed to fetch YouTube info: %s", e)
        return None


def is_admin(user_id: int, chat_id: int) -> bool:
    """Check if user is bot owner or group admin"""
    return user_id == BOT_OWNER_ID


def get_user_data(user_id: int) -> Dict:
    """Get or create user data"""
    if user_id not in user_data:
        user_data[user_id] = {
            "queue": [],
            "current": None,
            "playing": False,
        }
    return user_data[user_id]


def get_group_data(group_id: int) -> Dict:
    """Get or create group data"""
    if group_id not in groups:
        groups[group_id] = {
            "queue": [],
            "current": None,
            "playing": False,
            "dj": None,
            "admins": [],
        }
    return groups[group_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command with main menu"""
    user_id = update.effective_user.id
    is_owner = user_id == BOT_OWNER_ID

    buttons = [
        [InlineKeyboardButton("🎵 Play Song", callback_data="play_song")],
        [InlineKeyboardButton("📋 My Queue", callback_data="my_queue")],
        [InlineKeyboardButton("❓ Help", callback_data="show_help")],
    ]

    if is_owner:
        buttons.append([InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(buttons)

    welcome_text = (
        "🎵 <b>Welcome to Advanced Music Bot!</b>\n\n"
        "Send me a YouTube link and I'll add it to your queue.\n\n"
        "<b>Quick Commands:</b>\n"
        "• /play <url> - Add song\n"
        "• /queue - View queue\n"
        "• /clear - Clear queue\n"
        "• /help - Full help\n\n"
        "<i>Works in groups and personal chats!</i>"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin panel"""
    user_id = update.effective_user.id

    if user_id != BOT_OWNER_ID:
        await update.message.reply_text(
            "❌ <b>Access Denied!</b>\nOnly bot owner can access admin panel.",
            parse_mode="HTML"
        )
        return

    buttons = [
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_menu")],
        [InlineKeyboardButton("🤖 Clone Bot", callback_data="clone_bot_menu")],
        [InlineKeyboardButton("👥 Users List", callback_data="users_list")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    admin_text = (
        "👨‍💼 <b>Admin Panel</b>\n\n"
        "<b>Available Options:</b>\n"
        "📢 Broadcast - Send message to all users\n"
        "🤖 Clone Bot - Create bot clones\n"
        "👥 Users List - View active users\n"
        "📊 Bot Stats - Get bot statistics"
    )
    await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode="HTML")


async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start broadcast command"""
    user_id = update.effective_user.id

    if user_id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    await update.message.reply_text(
        "📢 <b>Broadcast Mode</b>\n\n"
        "Send the message you want to broadcast to all users.\n"
        "Use /broadcast_send to send or /cancel to exit.",
        parse_mode="HTML"
    )
    context.user_data["broadcast_mode"] = True


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send broadcast message"""
    user_id = update.effective_user.id

    if user_id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "❌ <b>Usage:</b> Reply to the message you want to broadcast with /broadcast_send",
            parse_mode="HTML"
        )
        return

    broadcast_message = update.message.reply_to_message
    sent = 0
    failed = 0

    # Send to all users in broadcast list
    for user_id_target in set(list(user_data.keys()) + broadcast_list):
        try:
            await context.bot.forward_message(
                chat_id=user_id_target,
                from_chat_id=broadcast_message.chat_id,
                message_id=broadcast_message.message_id
            )
            sent += 1
        except Exception as e:
            logger.exception("Failed to send broadcast: %s", e)
            failed += 1

    await update.message.reply_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"✓ Sent: {sent}\n"
        f"✗ Failed: {failed}",
        parse_mode="HTML"
    )
    context.user_data["broadcast_mode"] = False


async def clone_bot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clone bot creation menu"""
    user_id = update.effective_user.id

    if user_id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    buttons = [
        [InlineKeyboardButton("➕ Add Clone", callback_data="add_clone")],
        [InlineKeyboardButton("📋 List Clones", callback_data="list_clones")],
        [InlineKeyboardButton("🗑️ Remove Clone", callback_data="remove_clone")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    clone_text = (
        "🤖 <b>Clone Bot Manager</b>\n\n"
        "Create and manage bot clones for multi-channel deployment.\n\n"
        "<b>Instructions:</b>\n"
        "1. Get a bot token from @BotFather\n"
        "2. Use 'Add Clone' to register it\n"
        "3. Monitor all clones from here"
    )
    await update.message.reply_text(clone_text, reply_markup=reply_markup, parse_mode="HTML")


async def add_clone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a new clone bot"""
    user_id = update.effective_user.id

    if user_id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    await update.message.reply_text(
        "🤖 <b>Add New Clone Bot</b>\n\n"
        "Send the clone bot token:\n"
        "(Get it from @BotFather)",
        parse_mode="HTML"
    )
    context.user_data["adding_clone"] = True


async def list_clones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all clone bots"""
    user_id = update.effective_user.id

    if user_id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Admin only!")
        return

    if not clone_bots:
        await update.message.reply_text(
            "📋 <b>Clone Bots</b>\n\n"
            "No clones registered yet.",
            parse_mode="HTML"
        )
        return

    clone_list = "📋 <b>Registered Clones:</b>\n\n"
    for idx, (name, token) in enumerate(clone_bots.items(), 1):
        masked_token = token[:10] + "..." + token[-10:]
        clone_list += f"{idx}. <b>{name}</b>\n   Token: {masked_token}\n\n"

    await update.message.reply_text(clone_list, parse_mode="HTML")


async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Play command - add song by URL"""
    if not context.args:
        await update.message.reply_text(
            "❌ <b>Usage:</b> /play <YouTube URL>",
            parse_mode="HTML"
        )
        return

    url = context.args[0]
    user_id = update.effective_user.id

    await update.message.chat.send_action(ChatAction.TYPING)
    await update.message.reply_text("🔍 <b>Fetching song info...</b>", parse_mode="HTML")

    song = get_audio_info(url)
    if not song:
        await update.message.reply_text(
            "❌ <b>Could not fetch this song.</b>\n"
            "Make sure it's a valid YouTube URL.",
            parse_mode="HTML"
        )
        return

    data = get_user_data(user_id)
    data["queue"].append(song)
    queue_pos = len(data["queue"])

    buttons = [
        [InlineKeyboardButton("📋 View Queue", callback_data="my_queue")],
        [InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_all")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    response = (
        f"✅ <b>Song Added to Queue!</b>\n\n"
        f"<b>Title:</b> {song['title']}\n"
        f"<b>Duration:</b> {song['duration']//60}:{song['duration']%60:02d}\n"
        f"<b>Uploader:</b> {song['uploader']}\n"
        f"<b>Position:</b> #{queue_pos}"
    )
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="HTML")


async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle direct URL messages"""
    text = update.message.text.strip()

    if not any(text.startswith(prefix) for prefix in ["http://", "https://", "www.", "youtube.com", "youtu.be"]):
        return

    user_id = update.effective_user.id
    await update.message.chat.send_action(ChatAction.TYPING)

    song = get_audio_info(text)
    if not song:
        await update.message.reply_text(
            "❌ <b>Could not fetch this song.</b>\n"
            "Make sure it's a valid YouTube URL.",
            parse_mode="HTML"
        )
        return

    data = get_user_data(user_id)
    data["queue"].append(song)
    queue_pos = len(data["queue"])

    buttons = [
        [InlineKeyboardButton("📋 View Queue", callback_data="my_queue")],
        [InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_all")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    response = (
        f"✅ <b>Song Added!</b>\n\n"
        f"🎵 <b>{song['title']}</b>\n"
        f"⏱️ {song['duration']//60}:{song['duration']%60:02d}\n"
        f"👤 {song['uploader']}\n"
        f"📍 Position: #{queue_pos}"
    )
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="HTML")


async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's queue"""
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    queue = data["queue"]

    if not queue:
        await update.message.reply_text(
            "📋 <b>Your queue is empty.</b>\n"
            "Send a YouTube URL to add songs!",
            parse_mode="HTML"
        )
        return

    lines = ["📋 <b>Your Queue:</b>\n"]
    total_duration = 0

    for i, song in enumerate(queue, 1):
        total_duration += song["duration"]
        duration_str = f"{song['duration']//60}:{song['duration']%60:02d}"
        lines.append(f"{i}. <b>{song['title']}</b>\n   ⏱️ {duration_str}\n")

    total_min = total_duration // 60
    total_sec = total_duration % 60
    lines.append(f"\n<b>Total Duration:</b> {total_min}:{total_sec:02d}")
    lines.append(f"<b>Songs:</b> {len(queue)}")

    buttons = [[InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_all")]]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text("\n".join(lines), reply_markup=reply_markup, parse_mode="HTML")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear user's queue"""
    user_id = update.effective_user.id
    data = get_user_data(user_id)
    data["queue"] = []
    data["current"] = None

    await update.message.reply_text(
        "✅ <b>Queue cleared!</b>",
        parse_mode="HTML"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help"""
    help_text = (
        "🎵 <b>Music Bot - Complete Guide</b>\n\n"
        "<b>User Commands:</b>\n"
        "/start - Main menu\n"
        "/play <URL> - Add YouTube song\n"
        "/queue - Show your queue\n"
        "/clear - Clear queue\n"
        "/help - This message\n\n"
        "<b>Admin Commands:</b>\n"
        "/admin - Admin panel\n"
        "/broadcast - Send broadcast\n"
        "/stats - Bot statistics\n\n"
        "<b>How to Use:</b>\n"
        "1️⃣ Send YouTube URL directly\n"
        "2️⃣ Or use /play <URL>\n"
        "3️⃣ Check /queue\n"
        "4️⃣ Use buttons for quick actions"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = get_user_data(user_id)
    action = query.data

    if action == "show_help":
        help_text = (
            "🎵 <b>Music Bot Help</b>\n\n"
            "Send a YouTube URL → Auto add\n"
            "/play <URL> → Add song\n"
            "/queue → View songs\n"
            "/clear → Remove all\n\n"
            "Works in groups too! 🎉"
        )
        await query.edit_message_text(help_text, parse_mode="HTML")

    elif action == "my_queue":
        queue = data["queue"]
        if not queue:
            await query.edit_message_text("📋 Queue is empty!")
            return

        lines = ["📋 <b>Your Queue:</b>\n"]
        total_duration = 0

        for i, song in enumerate(queue, 1):
            total_duration += song["duration"]
            duration_str = f"{song['duration']//60}:{song['duration']%60:02d}"
            lines.append(f"{i}. <b>{song['title']}</b> ({duration_str})\n")

        total_min = total_duration // 60
        total_sec = total_duration % 60
        lines.append(f"\n<b>Total:</b> {total_min}:{total_sec:02d} | <b>Count:</b> {len(queue)}")

        await query.edit_message_text("\n".join(lines), parse_mode="HTML")

    elif action == "clear_all":
        data["queue"] = []
        data["current"] = None
        await query.edit_message_text("✅ Queue cleared!")

    elif action == "admin_panel":
        if user_id != BOT_OWNER_ID:
            await query.answer("❌ Admin only!")
            return
        buttons = [
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_menu")],
            [InlineKeyboardButton("🤖 Clone Bot", callback_data="clone_bot_menu")],
            [InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "👨‍💼 <b>Admin Panel</b>\n\n"
            "📢 Broadcast - Send to all users\n"
            "🤖 Clone Bot - Manage clones\n"
            "📊 Stats - Bot statistics",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    elif action == "bot_stats":
        total_users = len(user_data)
        total_songs = sum(len(d.get("queue", [])) for d in user_data.values())
        total_clones = len(clone_bots)
        stats_text = (
            f"📊 <b>Bot Statistics</b>\n\n"
            f"👥 Active Users: {total_users}\n"
            f"🎵 Total Songs in Queues: {total_songs}\n"
            f"🤖 Active Clones: {total_clones}\n"
            f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await query.edit_message_text(stats_text, parse_mode="HTML")

    elif action == "broadcast_menu":
        if user_id != BOT_OWNER_ID:
            await query.answer("❌ Admin only!")
            return
        buttons = [
            [InlineKeyboardButton("📤 Send Broadcast", callback_data="send_broadcast")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "📢 <b>Broadcast Menu</b>\n\n"
            "Send a message to all users at once.",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    elif action == "clone_bot_menu":
        if user_id != BOT_OWNER_ID:
            await query.answer("❌ Admin only!")
            return
        buttons = [
            [InlineKeyboardButton("➕ Add Clone", callback_data="add_clone")],
            [InlineKeyboardButton("📋 List Clones", callback_data="list_clones")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "🤖 <b>Clone Bot Manager</b>\n\n"
            "Create and manage bot clones.",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

    elif action == "play_song":
        await query.edit_message_text(
            "🎵 <b>Play Song</b>\n\n"
            "Send a YouTube URL!\n"
            "Or use /play <URL>"
        )

    elif action == "back_to_start":
        buttons = [
            [InlineKeyboardButton("🎵 Play Song", callback_data="play_song")],
            [InlineKeyboardButton("📋 My Queue", callback_data="my_queue")],
            [InlineKeyboardButton("❓ Help", callback_data="show_help")],
        ]
        if user_id == BOT_OWNER_ID:
            buttons.append([InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="admin_panel")])
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(
            "🎵 <b>Welcome to Advanced Music Bot!</b>\n\n"
            "Send me a YouTube link and I'll add it to your queue.",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )


def main() -> None:
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "❌ TELEGRAM_BOT_TOKEN is missing!\n"
            "Add it to your .env file."
        )

    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("play", play_command))
    application.add_handler(CommandHandler("queue", queue_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("broadcast", broadcast_start))
    application.add_handler(CommandHandler("broadcast_send", broadcast_send))
    application.add_handler(CommandHandler("add_clone", add_clone))
    application.add_handler(CommandHandler("list_clones", list_clones))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message))

    # Button callbacks
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("🎵 Advanced Music Bot started successfully!")
    application.run_polling()


if __name__ == "__main__":
    main()
