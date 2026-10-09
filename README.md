# 🎵 Advanced Telegram Music Bot

A powerful Telegram music bot with admin panel, broadcast, and clone management features.

## ⚡ Advanced Features

✅ **Music Management**
- YouTube music queue
- Personal queues per user
- Queue management (add, view, clear)
- Song info with duration and uploader

✅ **Admin Panel**
- Broadcast messages to all users
- Clone bot management
- User statistics
- Bot analytics

✅ **Clone Bot Support**
- Create multiple bot instances
- Manage all clones from one panel
- Multi-channel deployment
- Clone tracking

✅ **User Features**
- Direct YouTube URL support
- Inline button controls
- Group & personal chat support
- Real-time queue updates

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Telegram Bot Token (from @BotFather)
- Your Telegram User ID

### Installation

1. **Clone or download repository**

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

5. **Configure .env**
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   BOT_OWNER_ID=your_telegram_user_id_here
   ```

   To get your User ID:
   - Open Telegram
   - Go to @userinfobot
   - It will show your User ID

6. **Run the bot**
   ```bash
   python bot.py
   ```

## 📋 User Commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/play <URL>` | Add YouTube song |
| `/queue` | View your queue |
| `/clear` | Remove all songs |
| `/help` | Show help |

## 🔐 Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Open admin panel |
| `/broadcast` | Start broadcast mode |
| `/broadcast_send` | Send broadcast message |
| `/list_clones` | View all clone bots |
| `/add_clone` | Add new clone bot |

## 👨‍💼 Admin Panel Features

### 📢 Broadcast
- Send message to all active users
- Real-time delivery tracking
- Success/failure statistics

### 🤖 Clone Bot Manager
- Add new bot clones
- List all registered clones
- Remove inactive clones
- Token management

### 📊 Statistics
- Active users count
- Total songs in system
- Active clones
- Real-time metrics

## 🎯 How to Use

### For Regular Users
1. Send YouTube URL directly → Bot adds it
2. Use `/play <URL>` command
3. Use inline buttons for quick actions
4. Check `/queue` anytime

### For Admins
1. Use `/admin` to open admin panel
2. Access broadcast, clone management, stats
3. Send announcements to all users
4. Manage bot instances

## 🤖 Clone Bot Setup

1. Create bot tokens from @BotFather
2. Use `/add_clone` command
3. Provide clone token
4. Track all clones from admin panel

## 🔧 Configuration

**.env File:**
```env
TELEGRAM_BOT_TOKEN=123456:ABCdefGHI...  # Your main bot token
BOT_OWNER_ID=987654321                   # Your Telegram User ID
```

## 📁 Project Structure

```
krishmusic/
├── bot.py              # Main bot code
├── requirements.txt    # Dependencies
├── .env.example       # Config template
├── .gitignore         # Git ignore
└── README.md          # This file
```

## ⚙️ How It Works

1. **User sends URL** → Bot fetches video info
2. **Song added to queue** → Stored per user
3. **Queue management** → View/clear anytime
4. **Admin actions** → Broadcast to all
5. **Clone deployment** → Multi-instance setup

## 🐛 Troubleshooting

**Bot not starting?**
- Check `TELEGRAM_BOT_TOKEN` in `.env`
- Verify all dependencies: `pip install -r requirements.txt`

**Can't add songs?**
- Verify YouTube URL is valid
- Update yt-dlp: `pip install --upgrade yt-dlp`

**Admin panel not showing?**
- Check `BOT_OWNER_ID` in `.env`
- Use your actual Telegram User ID

**Broadcast not working?**
- Ensure bot is admin only feature
- Only bot owner can broadcast

## 🎁 Features Coming Soon

- Real voice chat playback
- Song search by name
- Playlist support
- Skip/pause/resume
- Database persistence
- Web dashboard
- Multi-language support

## 📝 License

MIT License

## 💬 Support

For issues:
- Check bot console logs
- Verify .env configuration
- Test with valid YouTube URLs
- Check bot permissions

---

**🎵 Made with ❤️ for music lovers**
