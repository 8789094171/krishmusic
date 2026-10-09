import logging
import os
from typing import Optional
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
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

# Store user music data
user_data = {}


def get_audio_info(url: str) -> Optional[dict]:
    """Fetch audio info from YouTube URL"""
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "url": info["url"],
                "title": info.get("title", "Unknown Track"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", None),
            }
    except Exception as e:
        logger.exception("Failed to fetch audio: %s", e)
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command"""
    keyboard = [
        [InlineKeyboardButton("🎵 Play Song", callback_data="play")],
        [InlineKeyboardButton("📋 Queue", callback_data="queue")],
        [InlineKeyboardButton("⏸ Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎵 Welcome to Music Bot!\n\n"
        "Send me a YouTube URL to play music.\n"
        "or use /play <url> command.",
        reply_markup=reply_markup,
    )


async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Play command with URL"""
    if not context.args:
        await update.message.reply_text("Usage: /play <YouTube URL>")
        return

    url = context.args[0]
    user_id = update.effective_user.id

    await update.message.reply_text("🔍 Fetching song info...")

    audio_info = get_audio_info(url)
    if not audio_info:
        await update.message.reply_text("❌ Could not fetch song. Check the URL.")
        return

    # Store in user queue
    if user_id not in user_data:
        user_data[user_id] = {"queue": []}

    user_data[user_id]["queue"].append(audio_info)

    keyboard = [
        [InlineKeyboardButton("⬇️ Download", callback_data=f"download_{len(user_data[user_id]['queue']) - 1}")],
        [InlineKeyboardButton("📋 Queue", callback_data="show_queue")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Added to queue:\n\n"
        f"<b>{audio_info['title']}</b>\n"
        f"Duration: {audio_info['duration']//60}:{audio_info['duration']%60:02d}",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle URL from message"""
    url = update.message.text
    user_id = update.effective_user.id

    if not url.startswith(("http://", "https://", "www.")):
        return

    await update.message.reply_text("🔍 Fetching song info...")

    audio_info = get_audio_info(url)
    if not audio_info:
        await update.message.reply_text("❌ Could not fetch song. Try another URL.")
        return

    if user_id not in user_data:
        user_data[user_id] = {"queue": []}

    user_data[user_id]["queue"].append(audio_info)

    keyboard = [
        [InlineKeyboardButton("⬇️ Download MP3", callback_data=f"download_{len(user_data[user_id]['queue']) - 1}")],
        [InlineKeyboardButton("📋 My Queue", callback_data="show_queue")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Added to queue:\n\n"
        f"<b>{audio_info['title']}</b>\n"
        f"Duration: {audio_info['duration']//60}:{audio_info['duration']%60:02d}",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if data == "help":
        await query.edit_message_text(
            "🎵 <b>Music Bot Help</b>\n\n"
            "Commands:\n"
            "/play <URL> - Play a YouTube song\n"
            "/queue - Show your queue\n"
            "/clear - Clear your queue\n\n"
            "Or just send a YouTube URL directly!",
            parse_mode="HTML",
        )

    elif data == "show_queue":
        if user_id not in user_data or not user_data[user_id]["queue"]:
            await query.edit_message_text("📋 Your queue is empty.")
            return

        queue_text = "📋 <b>Your Queue:</b>\n\n"
        for i, song in enumerate(user_data[user_id]["queue"], 1):
            queue_text += f"{i}. {song['title']}\n"

        await query.edit_message_text(queue_text, parse_mode="HTML")

    elif data.startswith("download_"):
        idx = int(data.split("_")[1])
        if user_id not in user_data or idx >= len(user_data[user_id]["queue"]):
            await query.edit_message_text("❌ Song not found.")
            return

        song = user_data[user_id]["queue"][idx]
        await query.edit_message_text(
            f"⬇️ <b>Download Link:</b>\n\n"
            f"<a href='{song['url']}'>Click here to download</a>\n\n"
            f"Song: {song['title']}",
            parse_mode="HTML",
        )


async def queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show queue"""
    user_id = update.effective_user.id

    if user_id not in user_data or not user_data[user_id]["queue"]:
        await update.message.reply_text("📋 Your queue is empty.")
        return

    queue_text = "📋 <b>Your Queue:</b>\n\n"
    for i, song in enumerate(user_data[user_id]["queue"], 1):
        queue_text += f"{i}. {song['title']}\n"

    await update.message.reply_text(queue_text, parse_mode="HTML")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear queue"""
    user_id = update.effective_user.id

    if user_id in user_data:
        user_data[user_id]["queue"] = []

    await update.message.reply_text("✅ Queue cleared.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command"""
    await update.message.reply_text(
        "🎵 <b>Music Bot Commands</b>\n\n"
        "/start - Start the bot\n"
        "/play <URL> - Play a YouTube song\n"
        "/queue - Show your queue\n"
        "/clear - Clear your queue\n"
        "/help - Show this help message\n\n"
        "📌 Just send a YouTube URL and I'll fetch it for you!",
        parse_mode="HTML",
    )


def main():
    """Start the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Add it to your .env file.")

    application = Application.builder().token(token).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("play", play_command))
    application.add_handler(CommandHandler("queue", queue_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot started...")
    application.run_polling()


if __name__ == "__main__":
    main()
