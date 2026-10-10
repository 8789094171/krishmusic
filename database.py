"""
Database layer for KrishMusic bot.
Persistent storage using SQLAlchemy + SQLite.
Preserves existing user sessions, queues, and statistics.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from config import settings

# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    """User model - stores individual user data."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    queue = Column(JSON, default=[])  # List of {url, title, duration, etc}
    current_song = Column(JSON, nullable=True)
    is_playing = Column(Boolean, default=False)
    total_songs_added = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "queue": self.queue or [],
            "current_song": self.current_song,
            "is_playing": self.is_playing,
            "total_songs_added": self.total_songs_added,
            "created_at": self.created_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
        }


class Group(Base):
    """Group model - stores group chat data."""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    title = Column(String)
    queue = Column(JSON, default=[])  # Shared group queue
    current_song = Column(JSON, nullable=True)
    is_playing = Column(Boolean, default=False)
    voice_chat_enabled = Column(Boolean, default=False)
    voice_chat_id = Column(Integer, nullable=True)  # Telegram group call ID
    dj_id = Column(Integer, nullable=True)  # Current DJ's telegram_id
    admins = Column(JSON, default=[])  # List of admin telegram_ids
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "title": self.title,
            "queue": self.queue or [],
            "current_song": self.current_song,
            "is_playing": self.is_playing,
            "voice_chat_enabled": self.voice_chat_enabled,
            "voice_chat_id": self.voice_chat_id,
            "dj_id": self.dj_id,
            "admins": self.admins or [],
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


class CloneBot(Base):
    """Clone bot model - stores clone bot instances."""
    __tablename__ = "clone_bots"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    token = Column(String, unique=True)
    bot_id = Column(Integer)
    bot_username = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer)  # Owner's telegram_id
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "token": self.token[:10] + "..." + self.token[-10:],  # Masked
            "bot_id": self.bot_id,
            "bot_username": self.bot_username,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


class BotStatistics(Base):
    """Bot statistics model - tracks metrics."""
    __tablename__ = "bot_statistics"
    
    id = Column(Integer, primary_key=True)
    total_users = Column(Integer, default=0)
    total_groups = Column(Integer, default=0)
    total_songs_played = Column(Integer, default=0)
    total_songs_added = Column(Integer, default=0)
    active_voice_chats = Column(Integer, default=0)
    broadcasts_sent = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_users": self.total_users,
            "total_groups": self.total_groups,
            "total_songs_played": self.total_songs_played,
            "total_songs_added": self.total_songs_added,
            "active_voice_chats": self.active_voice_chats,
            "broadcasts_sent": self.broadcasts_sent,
            "last_updated": self.last_updated.isoformat(),
        }


# Database operations
class Database:
    """Database abstraction layer."""
    
    def __init__(self):
        self.session = SessionLocal()
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        Base.metadata.create_all(engine)
    
    # User operations
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get or create user."""
        user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            self.session.add(user)
            self.session.commit()
        return user
    
    def update_user_queue(self, telegram_id: int, queue: List[Dict]) -> None:
        """Update user's queue."""
        user = self.get_user(telegram_id)
        user.queue = queue
        user.last_seen = datetime.utcnow()
        self.session.commit()
    
    def add_song_to_queue(self, telegram_id: int, song_data: Dict) -> None:
        """Add song to user's queue."""
        user = self.get_user(telegram_id)
        if user.queue is None:
            user.queue = []
        user.queue.append(song_data)
        user.total_songs_added += 1
        user.last_seen = datetime.utcnow()
        self.session.commit()
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        return self.session.query(User).all()
    
    # Group operations
    def get_group(self, telegram_id: int) -> Optional[Group]:
        """Get or create group."""
        group = self.session.query(Group).filter_by(telegram_id=telegram_id).first()
        if not group:
            group = Group(telegram_id=telegram_id, title="Unknown Group")
            self.session.add(group)
            self.session.commit()
        return group
    
    def update_group_queue(self, telegram_id: int, queue: List[Dict]) -> None:
        """Update group's queue."""
        group = self.get_group(telegram_id)
        group.queue = queue
        group.last_activity = datetime.utcnow()
        self.session.commit()
    
    def set_voice_chat(self, group_id: int, voice_chat_id: int, enabled: bool = True) -> None:
        """Set group voice chat status."""
        group = self.get_group(group_id)
        group.voice_chat_enabled = enabled
        group.voice_chat_id = voice_chat_id if enabled else None
        self.session.commit()
    
    def get_all_groups(self) -> List[Group]:
        """Get all groups."""
        return self.session.query(Group).all()
    
    # Clone bot operations
    def add_clone_bot(self, name: str, token: str, bot_id: int, created_by: int) -> CloneBot:
        """Add clone bot."""
        clone = CloneBot(
            name=name,
            token=token,
            bot_id=bot_id,
            created_by=created_by
        )
        self.session.add(clone)
        self.session.commit()
        return clone
    
    def get_clone_bot(self, name: str) -> Optional[CloneBot]:
        """Get clone bot by name."""
        return self.session.query(CloneBot).filter_by(name=name).first()
    
    def get_all_clone_bots(self) -> List[CloneBot]:
        """Get all clone bots."""
        return self.session.query(CloneBot).filter_by(is_active=True).all()
    
    def delete_clone_bot(self, name: str) -> None:
        """Delete clone bot."""
        clone = self.get_clone_bot(name)
        if clone:
            clone.is_active = False
            self.session.commit()
    
    # Statistics operations
    def get_statistics(self) -> Dict[str, Any]:
        """Get current bot statistics."""
        stats = self.session.query(BotStatistics).first()
        if not stats:
            stats = BotStatistics()
            self.session.add(stats)
            self.session.commit()
        
        # Calculate live statistics
        total_users = self.session.query(User).count()
        total_groups = self.session.query(Group).count()
        active_voice_chats = self.session.query(Group).filter_by(voice_chat_enabled=True).count()
        
        stats.total_users = total_users
        stats.total_groups = total_groups
        stats.active_voice_chats = active_voice_chats
        stats.last_updated = datetime.utcnow()
        self.session.commit()
        
        return stats.to_dict()
    
    def close(self):
        """Close database session."""
        self.session.close()


# Global database instance
db = Database()


if __name__ == "__main__":
    # Test database initialization
    db.get_user(123456789)
    print("✅ Database initialized successfully!")
    db.close()
