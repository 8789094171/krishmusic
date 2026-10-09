# 🎵 Telegram Music Bot

A powerful Telegram music bot for adding and managing YouTube music in your chats.

## ✨ Features

✅ **YouTube Integration**
- Add songs from YouTube URLs
- Auto-fetch song info (title, duration, uploader)
- Thumbnail display support

✅ **Queue Management**
- Personal music queues
- View full queue with durations
- Clear queue instantly
- See queue position for added songs

✅ **Easy to Use**
- Send YouTube URL directly
- Use `/play <url>` command
- Inline button controls
- Works in groups and personal chats

✅ **User Friendly**
- Clean formatted messages
- Song info with uploader
- Total queue duration
- Status emojis for every action

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Telegram Bot Token (from @BotFather)

### Installation

1. **Clone or download the repository**

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\\Scripts\\activate    # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment**
   ```bash
   cp .env.example .env
   ```

5. **Add your bot token**
   - Edit `.env` file
   - Replace `your_bot_token_here` with your actual token from @BotFather
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstUVwxyz
   ```

6. **Run the bot**
   ```bash
   python bot.py
   ```

## 📖 Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot and show menu |
| `/play <URL>` | Add song from YouTube URL |
| `/queue` | View your music queue |
| `/clear` | Remove all songs from queue |
| `/help` | Show full help message |

## 💡 Usage Examples

### Method 1: Direct URL
```
Just send: https://www.youtube.com/watch?v=...
Bot will automatically add it!
```

### Method 2: Command
```
/play https://www.youtube.com/watch?v=...
```

### Method 3: Inline Buttons
- Press "📋 My Queue" to view songs
- Press "🗑️ Clear Queue" to remove all
- Press "❓ Help" to see help

## 🔑 Getting Your Bot Token

1. Open Telegram
2. Search for **@BotFather**
3. Type `/newbot`
4. Follow the instructions
5. Copy the token provided
6. Paste it in `.env` file

## 📁 Project Structure

```
krishmusic/
├── bot.py              # Main bot code
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## 🎯 How It Works

1. User sends YouTube URL or uses `/play <url>`
2. Bot fetches video info using yt-dlp
3. Song is added to user's personal queue
4. User gets confirmation with song details
5. User can view, manage, and clear queue anytime

## ⚠️ Troubleshooting

**Bot not starting?**
- Check if `TELEGRAM_BOT_TOKEN` is set in `.env`
- Make sure all dependencies installed: `pip install -r requirements.txt`

**Can't add songs?**
- Verify YouTube URL is valid
- Try updating yt-dlp: `pip install --upgrade yt-dlp`
- Check internet connection

**Bot crashes?**
- Check logs for error messages
- Restart: `Ctrl+C` then `python bot.py`
- Make sure bot has message permissions

## 🔒 Security

- Never share your `.env` file
- Keep bot token secret
- Don't commit `.env` to git (`.gitignore` prevents this)

## 📈 Future Features

- Real voice chat audio streaming
- Song search by name
- Playlist support
- Skip/pause/resume controls
- Admin commands
- Database for persistent queues
- Group DJ mode

## 📝 License

MIT License - Feel free to use and modify!

## 💬 Support

For issues or questions:
- Check README thoroughly
- Review bot console logs
- Verify bot token and permissions

---

**Made with ❤️ for music lovers**
