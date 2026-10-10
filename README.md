# 🎵 Advanced Telegram Music Bot - v2 (Pyrogram + Voice Chat)

A production-ready Telegram music bot with persistent queue storage, group voice chat playback, and full Termux/Python 3.13 compatibility.

## ⚡ Features

✅ **Music Management**
- YouTube music queue (persistent SQLite storage)
- Personal queues per user & group queues
- Queue management (add, view, clear)
- Song metadata with duration and uploader
- **Queues survive bot restart!**

✅ **Voice Chat Playback**
- Real Telegram group voice chat streaming
- FFmpeg-based audio processing
- Queue-based playback orchestration

✅ **Admin Panel**
- Broadcast messages to all users
- Bot statistics & analytics
- Database status monitoring

✅ **Compatibility**
- ✅ Python 3.9 through Python 3.13+
- ✅ Android Termux environment
- ✅ Linux (Ubuntu/Debian)
- ✅ macOS and Windows

## 🚀 Quick Start

### Prerequisites

**On Termux:**
```bash
pkg update
pkg install python ffmpeg git
```

**On Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg git
```

**On macOS:**
```bash
brew install python ffmpeg
```

**Get Telegram Credentials:**
- **Bot Token:** Create bot with @BotFather on Telegram → `/newbot`
- **API_ID & API_HASH:** Get from https://my.telegram.org/apps (logged in as your account, not bot)
- **User ID:** Send `/start` to @userinfobot → note your ID

### Installation

#### 1. Clone or Download Repository
```bash
cd ~
git clone https://github.com/8789094171/krishmusic.git
cd krishmusic
```

#### 2. Create Virtual Environment

**Termux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your actual values
nano .env    # Termux/Linux
# or
code .env    # Windows/macOS
```

**Fill in .env:**
```env
TELEGRAM_BOT_TOKEN=123456:ABCdefGHI...
API_ID=12345678
API_HASH=abc123def456...
BOT_OWNER_ID=987654321
```

#### 5. Verify Installation
```bash
python bot.py
```

You should see:
```
============================================================
🎵 KrishMusic Bot Configuration
============================================================
Python Version:      3.13.0
Platform:            Termux (or Linux/Windows)
FFmpeg:              ✅ Available
Database:            sqlite:///data/krishmusic.db
Voice Chat Support:  ✅ Enabled
Persistence:         ✅ Enabled
============================================================
```

## 📋 User Commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/play <URL>` | Add YouTube song |
| `/queue` | View your queue |
| `/clear` | Clear queue |
| `/help` | Full help |
| `/voice` | Join group voice chat (admin only) |

## 🔐 Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Open admin panel |

## 🎯 How to Use

### Add Songs (Personal Queue)
1. **Direct URL:** Just send a YouTube URL
2. **Command:** `/play https://www.youtube.com/watch?v=...`
3. **View queue:** `/queue`
4. **Clear queue:** `/clear`

### Group Voice Chat Playback
1. Start a voice chat in a Telegram group
2. Add the bot to the group (make it admin)
3. Run `/voice` (bot owner only)
4. Send YouTube URLs in the group chat
5. Bot streams audio into the active voice call

## 🗄️ Database & Persistence

All user data is stored in **SQLite** at `data/krishmusic.db`:
- User queues
- Group queues
- Song metadata
- Bot statistics
- Clone bot records

**Queue persists across restarts!**

To back up:
```bash
cp data/krishmusic.db krishmusic.db.backup
```

To restore:
```bash
cp krishmusic.db.backup data/krishmusic.db
```

## 🔧 Configuration Details

### Environment Variables
```env
TELEGRAM_BOT_TOKEN      # Bot token from @BotFather
API_ID                  # From https://my.telegram.org/apps
API_HASH                # From https://my.telegram.org/apps
BOT_OWNER_ID            # Your Telegram user ID (from @userinfobot)
```

### Project Structure
```
krishmusic/
├── bot.py              # Main bot entrypoint (Pyrogram)
├── config.py           # Configuration & environment detection
├── database.py         # SQLite models & ORM
├── voice_handler.py    # Voice chat integration (PyTgCalls)
├── requirements.txt    # Python dependencies
├── .env.example        # Config template
├── .env                # (You create this)
├── data/               # Database & runtime data
│   └── krishmusic.db   # SQLite database (auto-created)
└── README.md           # This file
```

## 🐛 Troubleshooting

### Bot won't start
```bash
# Check token
grep TELEGRAM_BOT_TOKEN .env

# Check FFmpeg
ffmpeg -version

# Check Python
python --version

# View full error
python bot.py
```

### ImportError: No module named 'pyrogram'
```bash
pip install --upgrade pyrogram
```

### FFmpeg not found (Termux)
```bash
pkg install ffmpeg
# Verify
ffmpeg -version
```

### Can't add YouTube songs
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Test URL
python -c "import yt_dlp; print('yt-dlp OK')"
```

### Database issues
```bash
# Backup existing
cp data/krishmusic.db data/krishmusic.db.backup

# Delete and recreate
rm data/krishmusic.db
python bot.py  # Will auto-create fresh DB
```

## 🔄 How It Works

1. **User sends URL** → Bot fetches metadata via yt-dlp
2. **Song added to queue** → Stored in SQLite (persistent)
3. **Voice chat active** → Bot streams audio via PyTgCalls
4. **Queue management** → View, skip, clear anytime
5. **Restart → Queue recovered** from database

## 🚀 Deploy to Server (Optional)

### Using systemd (Linux)

Create `/etc/systemd/system/krishmusic.service`:
```ini
[Unit]
Description=KrishMusic Telegram Bot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/krishmusic
Environment="PATH=/home/pi/krishmusic/.venv/bin"
ExecStart=/home/pi/krishmusic/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable krishmusic
sudo systemctl start krishmusic
sudo systemctl status krishmusic
```

### Using screen (Termux)

```bash
screen -S krishmusic python bot.py
# Press Ctrl+A then D to detach
# Reattach:
screen -r krishmusic
```

## 📊 Admin Features

### Bot Statistics
- Total active users
- Total groups
- Total songs added
- Active voice chats
- Broadcasts sent

### Database Monitoring
- Check database status
- View configuration
- Monitor runtime

## 💾 Backup & Recovery

### Daily Backup Script
```bash
#!/bin/bash
BACKUP_DIR=~/krishmusic_backups
mkdir -p $BACKUP_DIR
cp ~/krishmusic/data/krishmusic.db $BACKUP_DIR/krishmusic.db.$(date +%Y%m%d_%H%M%S)
```

### Restore from Backup
```bash
cp ~/krishmusic_backups/krishmusic.db.20241010_143022 ~/krishmusic/data/krishmusic.db
```

## 🎁 Coming Soon

- Song search by name/artist
- Playlist support
- Skip/pause/resume controls
- Multi-language support
- Web dashboard

## 📝 License

MIT License — Free to use and modify.

## 💬 Support

For issues:
- Check bot console output
- Verify `.env` configuration
- Test with valid YouTube URLs
- Check bot has required permissions in group
- See **Troubleshooting** section above

---

**🎵 Made with ❤️ for music lovers | Python 3.13 & Termux Ready**
