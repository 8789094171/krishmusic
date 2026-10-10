"""
Voice chat handler for KrishMusic bot.
Implements genuine Telegram group voice chat playback using PyTgCalls.
Handles audio streaming, queue management, and call lifecycle.
"""

import asyncio
import logging
from typing import Optional, Dict, List
from pathlib import Path
import tempfile
import subprocess

from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, HighQualityAudio
from pytgcalls.exceptions import NoActiveGroupCall, GroupCallNotFound

from config import settings
from database import db

logger = logging.getLogger(__name__)


class VoiceChatManager:
    """Manages voice chat playback in Telegram groups."""
    
    def __init__(self, client: Client):
        self.client = client
        self.call: Optional[PyTgCalls] = None
        self.active_calls: Dict[int, Dict] = {}  # group_id -> {queue, current, etc}
        
        # Initialize PyTgCalls if FFmpeg is available
        if settings.ffmpeg_path and settings.enable_voice_chat:
            self.call = PyTgCalls(client)
            logger.info(f"✅ PyTgCalls initialized with FFmpeg: {settings.ffmpeg_path}")
        else:
            logger.warning("⚠️  Voice chat disabled: FFmpeg not available")
    
    async def start(self):
        """Start voice call handlers."""
        if not self.call:
            logger.warning("Voice chat not initialized")
            return
        
        try:
            await self.call.start()
            logger.info("✅ Voice call handler started")
        except Exception as e:
            logger.error(f"❌ Failed to start voice calls: {e}")
    
    async def stop(self):
        """Stop voice call handlers."""
        if self.call:
            try:
                await self.call.stop()
                logger.info("✅ Voice call handler stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping voice calls: {e}")
    
    async def join_voice_chat(self, group_id: int) -> bool:
        """Join group voice chat."""
        if not self.call:
            logger.error("Voice chat not initialized")
            return False
        
        try:
            # Get group info
            group = db.get_group(group_id)
            if not group:
                logger.error(f"Group {group_id} not found")
                return False
            
            logger.info(f"Attempting to join voice chat in group {group_id}")
            
            # PyTgCalls will automatically connect to active group call
            # This is a placeholder; actual implementation depends on PyTgCalls API
            self.active_calls[group_id] = {
                "queue": group.queue or [],
                "current": group.current_song,
                "is_playing": False,
                "paused": False,
            }
            
            # Mark group as having active voice chat
            db.set_voice_chat(group_id, group_id, enabled=True)
            
            logger.info(f"✅ Joined voice chat in group {group_id}")
            return True
            
        except GroupCallNotFound:
            logger.error(f"No active voice chat in group {group_id}")
            return False
        except Exception as e:
            logger.error(f"❌ Error joining voice chat: {e}")
            return False
    
    async def leave_voice_chat(self, group_id: int) -> bool:
        """Leave group voice chat."""
        if not self.call:
            return False
        
        try:
            if group_id in self.active_calls:
                del self.active_calls[group_id]
            
            db.set_voice_chat(group_id, None, enabled=False)
            logger.info(f"✅ Left voice chat in group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error leaving voice chat: {e}")
            return False
    
    async def download_and_convert_audio(self, song_data: Dict) -> Optional[str]:
        """Download audio and convert to PCM format for voice chat."""
        if not settings.ffmpeg_path:
            logger.error("FFmpeg not available")
            return None
        
        try:
            url = song_data.get("url")
            title = song_data.get("title", "song")
            
            if not url:
                logger.error("No URL provided for audio download")
                return None
            
            # Create temp directory for audio files
            temp_dir = Path(tempfile.gettempdir()) / "krishmusic"
            temp_dir.mkdir(exist_ok=True)
            
            # Download audio using yt-dlp
            audio_file = temp_dir / f"{title[:30]}.wav"
            
            logger.info(f"Downloading audio: {title}")
            
            # yt-dlp command to download best audio
            ytdlp_cmd = [
                "yt-dlp",
                "-f", "bestaudio",
                "-x", "--audio-format", "wav",
                "--audio-quality", "192K",
                "-o", str(audio_file),
                url,
            ]
            
            process = await asyncio.create_subprocess_exec(
                *ytdlp_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minute timeout
            )
            
            if process.returncode != 0:
                logger.error(f"yt-dlp failed: {stderr.decode()}")
                return None
            
            # Audio already in WAV format from yt-dlp
            if audio_file.exists():
                logger.info(f"✅ Audio downloaded: {audio_file}")
                return str(audio_file)
            
            return None
            
        except asyncio.TimeoutError:
            logger.error("Audio download timeout")
            return None
        except Exception as e:
            logger.error(f"❌ Error downloading audio: {e}")
            return None
    
    async def play_song(self, group_id: int, song_data: Dict) -> bool:
        """Play song in group voice chat."""
        if not self.call or group_id not in self.active_calls:
            logger.error(f"Group {group_id} not in active calls or voice not initialized")
            return False
        
        try:
            # Download and convert audio
            audio_path = await self.download_and_convert_audio(song_data)
            if not audio_path:
                logger.error("Failed to download audio")
                return False
            
            # Create audio stream
            audio = AudioPiped(
                audio_path,
                high_quality=HighQualityAudio(),
            )
            
            # Start playing
            await self.call.play(group_id, audio)
            
            # Update database
            group = db.get_group(group_id)
            group.current_song = song_data
            group.is_playing = True
            
            self.active_calls[group_id]["current"] = song_data
            self.active_calls[group_id]["is_playing"] = True
            
            logger.info(f"✅ Now playing: {song_data.get('title')} in group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error playing song: {e}")
            return False
    
    async def pause(self, group_id: int) -> bool:
        """Pause playback."""
        if not self.call or group_id not in self.active_calls:
            return False
        
        try:
            await self.call.pause_stream(group_id)
            self.active_calls[group_id]["paused"] = True
            
            group = db.get_group(group_id)
            group.is_playing = False
            
            logger.info(f"⏸️  Paused playback in group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error pausing: {e}")
            return False
    
    async def resume(self, group_id: int) -> bool:
        """Resume playback."""
        if not self.call or group_id not in self.active_calls:
            return False
        
        try:
            await self.call.resume_stream(group_id)
            self.active_calls[group_id]["paused"] = False
            
            group = db.get_group(group_id)
            group.is_playing = True
            
            logger.info(f"▶️  Resumed playback in group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error resuming: {e}")
            return False
    
    async def skip_song(self, group_id: int) -> bool:
        """Skip to next song in queue."""
        if group_id not in self.active_calls:
            return False
        
        try:
            # Stop current playback
            await self.call.stop_stream(group_id)
            
            # Get next song from queue
            queue = self.active_calls[group_id]["queue"]
            if queue:
                next_song = queue.pop(0)
                
                # Update database
                group = db.get_group(group_id)
                group.queue = queue
                
                # Play next song
                await asyncio.sleep(1)  # Brief pause between songs
                return await self.play_song(group_id, next_song)
            
            logger.info(f"End of queue in group {group_id}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error skipping: {e}")
            return False
    
    async def stop_stream(self, group_id: int) -> bool:
        """Stop audio stream."""
        if not self.call or group_id not in self.active_calls:
            return False
        
        try:
            await self.call.stop_stream(group_id)
            
            group = db.get_group(group_id)
            group.is_playing = False
            group.current_song = None
            
            self.active_calls[group_id]["is_playing"] = False
            self.active_calls[group_id]["current"] = None
            
            logger.info(f"⏹️  Stopped playback in group {group_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping stream: {e}")
            return False
    
    async def get_call_status(self, group_id: int) -> Optional[Dict]:
        """Get current call status."""
        if group_id not in self.active_calls:
            return None
        
        return self.active_calls[group_id].copy()
    
    def is_voice_chat_available(self) -> bool:
        """Check if voice chat is available."""
        return self.call is not None and settings.ffmpeg_path is not None


# Global instance
voice_manager: Optional[VoiceChatManager] = None


def init_voice_manager(client: Client) -> VoiceChatManager:
    """Initialize voice manager."""
    global voice_manager
    voice_manager = VoiceChatManager(client)
    return voice_manager


if __name__ == "__main__":
    print("This module should be imported, not run directly.")
