"""
KrishMusic Bot v2 - Telegram Music Bot with Voice Chat Support
Built with Pyrogram + PyTgCalls + SQLite persistence
Compatible with Python 3.13, Android Termux, and Linux
"""

import logging
import os
import sys
import asyncio
from typing import Optional, Dict

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError
import yt_dlp

from config import settings, log_config
from database import db
from voice_handler import init_voice_manager

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# YT-DLP configuration
YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "socket_timeout": 30,
}


class MusicBot:
    """Main bot class using Pyrogram."""
    
    def __init__(self):
        """Initialize bot with Pyrogram client."""
        self.app = Client(
            "krishmusic",
            api_id=int(settings.api_id) if settings.api_id else 123456,
            api_hash=settings.api_hash or "abc123",
            bot_token=settings.telegram_bot_token,
        )
        
        self.voice_manager = None
        self.setup_handlers()
        logger.info("✅ Bot instance created")
    
    def setup_handlers(self):
        """Register message and callback handlers."""
        
        @self.app.on_message(filters.command("start"))
        async def start_handler(client, message: Message):
            await self.cmd_start(client, message)
        
        @self.app.on_message(filters.command("play"))
        async def play_handler(client, message: Message):
            await self.cmd_play(client, message)
        
        @self.app.on_message(filters.command("queue"))
        async def queue_handler(client, message: Message):
            await self.cmd_queue(client, message)
        
        @self.app.on_message(filters.command("clear"))
        async def clear_handler(client, message: Message):
            await self.cmd_clear(client, message)
        
        @self.app.on_message(filters.command("help"))
        async def help_handler(client, message: Message):
            await self.cmd_help(client, message)
        
        @self.app.on_message(filters.command("admin"))
        async def admin_handler(client, message: Message):
            await self.cmd_admin(client, message)
        
        @self.app.on_message(filters.command("voice"))
        async def voice_handler(client, message: Message):
            await self.cmd_voice_join(client, message)
        
        @self.app.on_message(filters.text & ~filters.command)
        async def text_handler(client, message: Message):
            await self.handle_text_message(client, message)
    
    async def cmd_start(self, client: Client, message: Message):
        """Handle /start command."""
        user_id = message.from_user.id
        user = db.get_user(user_id)
        
        text = (
            "🎵 <b>Welcome to KrishMusic Bot!</b>\n\n"
            "<b>Features:</b>\n"
            "✅ YouTube music queue (persistent)\n"
            "✅ Personal queues per user\n"
            "✅ Group voice chat playback\n"
            "✅ Admin broadcast & statistics\n\n"
            "<b>Commands:</b>\n"
            "/play <URL> - Add song\n"
            "/queue - View queue\n"
            "/clear - Clear queue\n"
            "/help - Full help\n"
        )
        
        if user_id == settings.bot_owner_id:
            text += "/admin - Admin panel\n"
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 Add Song", callback_data="play_song")],
            [InlineKeyboardButton("📋 My Queue", callback_data="my_queue")],
            [InlineKeyboardButton("❓ Help", callback_data="show_help")],
        ])
        
        if user_id == settings.bot_owner_id:
            buttons.append([InlineKeyboardButton("👨‍💼 Admin Panel", callback_data="admin_panel")])
        
        await message.reply_text(text, reply_markup=buttons, parse_mode="html")
        logger.info(f"User {user_id} started bot")
    
    async def cmd_play(self, client: Client, message: Message):
        """Handle /play <URL> command."""
        if not message.command or len(message.command) < 2:
            await message.reply_text(
                "❌ <b>Usage:</b> /play &lt;YouTube URL&gt;",
                parse_mode="html"
            )
            return
        
        url = message.command[1]
        user_id = message.from_user.id
        
        await message.reply_text("🔍 <b>Fetching song info...</b>", parse_mode="html")
        
        song_data = await self.get_audio_info(url)
        if not song_data:
            await message.reply_text(
                "❌ <b>Could not fetch song.</b>\n"
                "Ensure the URL is valid and from YouTube.",
                parse_mode="html"
            )
            return
        
        # Add to user's queue
        db.add_song_to_queue(user_id, song_data)
        user = db.get_user(user_id)
        queue_pos = len(user.queue) if user.queue else 0
        
        text = (
            f"✅ <b>Song Added!</b>\n\n"
            f"🎵 <b>{song_data['title']}</b>\n"
            f"⏱️ {song_data['duration']//60}:{song_data['duration']%60:02d}\n"
            f"👤 {song_data['uploader']}\n"
            f"📍 Position: #{queue_pos}"
        )
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 View Queue", callback_data="my_queue")],
            [InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_all")],
        ])
        
        await message.reply_text(text, reply_markup=buttons, parse_mode="html")
        logger.info(f"User {user_id} added song: {song_data['title']}")
    
    async def cmd_queue(self, client: Client, message: Message):
        """Handle /queue command."""
        user_id = message.from_user.id
        user = db.get_user(user_id)
        queue = user.queue or []
        
        if not queue:
            await message.reply_text(
                "📋 <b>Your queue is empty.</b>\n"
                "Send a YouTube URL or use /play to add songs!",
                parse_mode="html"
            )
            return
        
        lines = ["📋 <b>Your Queue:</b>\n"]
        total_duration = 0
        
        for i, song in enumerate(queue[:15], 1):
            total_duration += song.get("duration", 0)
            duration_str = f"{song['duration']//60}:{song['duration']%60:02d}"
            lines.append(f"{i}. <b>{song['title'][:40]}</b>\n   ⏱️ {duration_str}\n")
        
        if len(queue) > 15:
            lines.append(f"\n... and {len(queue) - 15} more songs")
        
        total_min = total_duration // 60
        total_sec = total_duration % 60
        lines.append(f"\n<b>Total Duration:</b> {total_min}:{total_sec:02d}")
        lines.append(f"<b>Songs:</b> {len(queue)}")
        
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ Clear Queue", callback_data="clear_all")]])
        
        await message.reply_text("\n".join(lines), reply_markup=buttons, parse_mode="html")
    
    async def cmd_clear(self, client: Client, message: Message):
        """Handle /clear command."""
        user_id = message.from_user.id
        db.update_user_queue(user_id, [])
        
        await message.reply_text("✅ <b>Queue cleared!</b>", parse_mode="html")
        logger.info(f"User {user_id} cleared queue")
    
    async def cmd_help(self, client: Client, message: Message):
        """Handle /help command."""
        text = (
            "🎵 <b>KrishMusic Bot - Complete Guide</b>\n\n"
            "<b>User Commands:</b>\n"
            "/start - Main menu\n"
            "/play &lt;URL&gt; - Add YouTube song\n"
            "/queue - Show your queue\n"
            "/clear - Clear queue\n"
            "/help - This message\n\n"
            "<b>How to Use:</b>\n"
            "1️⃣ Send YouTube URL directly or /play &lt;URL&gt;\n"
            "2️⃣ Check /queue anytime\n"
            "3️⃣ Use buttons for quick actions\n\n"
            "<b>💾 All queues are permanently saved!</b>\n"
            "Your songs stay even after bot restart."
        )
        
        if message.from_user.id == settings.bot_owner_id:
            text += "\n\n<b>Admin Commands:</b>\n/admin - Admin panel"
        
        await message.reply_text(text, parse_mode="html")
    
    async def cmd_voice_join(self, client: Client, message: Message):
        """Handle /voice command to join group voice chat."""
        if message.from_user.id != settings.bot_owner_id:
            await message.reply_text("❌ Only bot owner can join voice chats.", parse_mode="html")
            return
        
        if not self.voice_manager or not self.voice_manager.is_voice_chat_available():
            await message.reply_text(
                "❌ <b>Voice chat not available.</b>\n"
                "Ensure FFmpeg is installed and configured.",
                parse_mode="html"
            )
            return
        
        group_id = message.chat.id
        success = await self.voice_manager.join_voice_chat(group_id)
        
        if success:
            await message.reply_text(
                "✅ <b>Joined voice chat!</b>\n"
                "Send songs to queue and I'll play them.",
                parse_mode="html"
            )
            logger.info(f"Joined voice chat in group {group_id}")
        else:
            await message.reply_text(
                "❌ <b>Could not join voice chat.</b>\n"
                "Ensure there's an active voice chat in this group.",
                parse_mode="html"
            )
    
    async def cmd_admin(self, client: Client, message: Message):
        """Handle /admin command."""
        if message.from_user.id != settings.bot_owner_id:
            await message.reply_text("❌ Access denied!", parse_mode="html")
            return
        
        stats = db.get_statistics()
        text = (
            "👨‍💼 <b>Admin Panel</b>\n\n"
            f"👥 Total Users: {stats['total_users']}\n"
            f"👥 Total Groups: {stats['total_groups']}\n"
            f"🎵 Total Songs Added: {stats['total_songs_added']}\n"
            f"🎤 Active Voice Chats: {stats['active_voice_chats']}\n"
            f"📢 Broadcasts Sent: {stats['broadcasts_sent']}"
        )
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 Bot Info", callback_data="bot_info")],
            [InlineKeyboardButton("📊 Database Status", callback_data="db_status")],
        ])
        
        await message.reply_text(text, reply_markup=buttons, parse_mode="html")
    
    async def handle_text_message(self, client: Client, message: Message):
        """Handle direct URL messages."""
        if not message.text:
            return
        
        text = message.text.strip()
        
        # Check if message contains a URL
        if not any(text.startswith(prefix) for prefix in ["http://", "https://", "www.", "youtube.com", "youtu.be"]):
            return
        
        user_id = message.from_user.id
        
        await message.reply_text("🔍 <b>Processing...</b>", parse_mode="html")
        
        song_data = await self.get_audio_info(text)
        if not song_data:
            await message.reply_text(
                "❌ <b>Could not fetch song.</b>",
                parse_mode="html"
            )
            return
        
        db.add_song_to_queue(user_id, song_data)
        
        text = (
            f"✅ <b>Song Added!</b>\n\n"
            f"🎵 <b>{song_data['title']}</b>\n"
            f"👤 {song_data['uploader']}"
        )
        
        await message.reply_text(text, parse_mode="html")
        logger.info(f"User {user_id} added song via URL: {song_data['title']}")
    
    @staticmethod
    async def get_audio_info(url: str) -> Optional[Dict]:
        """Fetch audio info from YouTube URL asynchronously."""
        try:
            # Run yt-dlp in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def fetch_info():
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        return None
                    
                    return {
                        "title": info.get("title", "Unknown"),
                        "url": info.get("webpage_url") or url,
                        "duration": info.get("duration", 0),
                        "thumbnail": info.get("thumbnail"),
                        "uploader": info.get("uploader", "Unknown"),
                    }
            
            result = await loop.run_in_executor(None, fetch_info)
            return result
            
        except Exception as e:
            logger.error(f"Error fetching audio info: {e}")
            return None
    
    async def start(self):
        """Start the bot."""
        log_config()
        
        # Initialize voice manager
        self.voice_manager = init_voice_manager(self.app)
        
        logger.info("🎵 KrishMusic Bot v2 starting...")
        logger.info(f"Platform: {'Termux' if settings.is_termux else 'Linux' if settings.is_linux else 'Windows'}")
        logger.info(f"Python: {settings.python_version}")
        logger.info(f"Database: {settings.database_url}")
        logger.info(f"Voice Chat: {'✅ Enabled' if settings.enable_voice_chat else '❌ Disabled'}")
        
        try:
            await self.app.start()
            if self.voice_manager:
                await self.voice_manager.start()
            
            me = await self.app.get_me()
            logger.info(f"✅ Bot started as @{me.username} ({me.id})")
            
            # Keep bot running
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            sys.exit(1)
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("Stopping bot...")
        if self.voice_manager:
            await self.voice_manager.stop()
        await self.app.stop()
        db.close()
        logger.info("✅ Bot stopped gracefully")


async def main():
    """Entry point."""
    bot = MusicBot()
    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
        sys.exit(0)
