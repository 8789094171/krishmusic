import logging
import os
from typing import Dict, List, Optional
import asyncio

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatAction
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

user_data: Dict[int, Dict[str, any]] = {}
groups: Dict[int, Dict[str, any]] = {}


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
        }
    return groups[group_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command with inline menu"""
    keyboard = [
        [InlineKeyboardButton("🎵 Play Song", callback_data="play_song")],
        [InlineKeyboardButton("📋 My Queue", callback_data="my_queue")],
        [InlineKeyboardButton("❓ Help", callback_data="show_help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "🎵 <b>Welcome to Music Bot!</b>\n\n"
        "Send me a YouTube link and I'll add it to your queue.\n\n"
        "<b>Quick Commands:</b>\n"
        "• /play &lt;url&gt; - Add song\n"
        "• /queue - View queue\n"
        "• /clear - Clear queue\n"
        "• /help - Full help\n\n"
        "<i>Works in groups and personal chats!</i>"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help"""
    help_text = (
        "🎵 <b>Music Bot - Full Guide</b>\n\n"
        "<b>Commands:</b>\n"
        "/start - Start menu\n"
        "/play &lt;URL&gt; - Add YouTube song\n"
        "/queue - Show your queue\n"
        "/clear - Clear your queue\n"
        "/help - This message\n\n"
        "<b>How to Use:</b>\n"
        "1️⃣ Send a YouTube URL directly\n"
        "2️⃣ Or use /play &lt;YouTube URL&gt;\n"
        "3️⃣ Check /queue\n"
        "4️⃣ Use buttons for quick actions\n\n"
        "<b>Features:</b>\n"
        "✅ YouTube song queue\n"
        "✅ Works in groups\n"
        "✅ Personal queues\n"
        "✅ Song info (title, duration, uploader)\n\n"
        "<b>Get YouTube Link:</b>\n"
        "Just copy any YouTube video URL and send it!"
    )
    await update.message.reply_text(help_text, parse_mode="HTML")


async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Play command - add song by URL"""
    if not context.args:
        await update.message.reply_text(
            "❌ <b>Usage:</b> /play &lt;YouTube URL&gt;",
            parse_mode="HTML"
        )
        return

    url = context.args[0]
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Show loading status
    await update.message.chat.send_action(ChatAction.TYPING)
    await update.message.reply_text("🔍 <b>Fetching song info...</b>", parse_mode="HTML")

    # Fetch audio info
    song = get_audio_info(url)
    if not song:
        await update.message.reply_text(
            "❌ <b>Could not fetch this song.</b>\n"
            "Make sure it's a valid YouTube URL.",
            parse_mode="HTML"
        )
        return

    # Add to user's queue
    data = get_user_data(user_id)
    data["queue"].append(song)
    queue_pos = len(data["queue"])

    # Prepare response with buttons
    keyboard = [
        [InlineKeyboardButton("📋 View Queue", callback_data="my_queue")],
        [InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_all")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    response = (
        f"✅ <b>Song Added to Queue!</b>\n\n"
        f"<b>Title:</b> {song['title']}\n"
        f"<b>Duration:</b> {song['duration']//60}:{song['duration']%60:02d}\n"
        f"<b>Uploader:</b> {song['uploader']}\n"
        f"<b>Position in Queue:</b> #{queue_pos}"
    )
    await update.message.reply_text(response, reply_markup=reply_markup, parse_mode="HTML")


async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle direct URL messages"""
    text = update.message.text.strip()
    
    # Check if it's a URL
    if not any(text.startswith(prefix) for prefix in ["http://", "https://", "www.", "youtube.com", "youtu.be"]):
        return

    user_id = update.effective_user.id
    await update.message.chat.send_action(ChatAction.TYPING)

    # Fetch audio info
    song = get_audio_info(text)
    if not song:
        await update.message.reply_text(
            "❌ <b>Could not fetch this song.</b>\n"
            "Make sure it's a valid YouTube URL.",
            parse_mode="HTML"
        )
        return

    # Add to queue
    data = get_user_data(user_id)
    data["queue"].append(song)
    queue_pos = len(data["queue"])

    # Prepare response
    keyboard = [
        [InlineKeyboardButton("📋 View Queue", callback_data="my_queue")],
        [InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_all")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

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

    # Build queue message
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

    keyboard = [
        [InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_all")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

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
            "<b>Send a YouTube URL</b> → Auto add\n"
            "<b>/play &lt;URL&gt;</b> → Add song\n"
            "<b>/queue</b> → View songs\n"
            "<b>/clear</b> → Remove all\n\n"
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

    elif action == "play_song":
        await query.edit_message_text(
            "🎵 <b>Send a YouTube URL!</b>\n\n"
            "Or use /play &lt;URL&gt;"
        )


def main() -> None:
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "❌ TELEGRAM_BOT_TOKEN is missing!\n"
            "Add it to your .env file."
        )

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("play", play_command))
    application.add_handler(CommandHandler("queue", queue_command))
    application.add_handler(CommandHandler("clear", clear_command))

    # Message handler for URLs
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url_message))

    # Button callbacks
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("🎵 Bot started successfully!")
    application.run_polling()


if __name__ == "__main__":
    main()
