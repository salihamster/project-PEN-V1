"""
WhatsApp Media Manager

Handles:
- Media file storage and indexing
- Media ID generation and lookup
- Processing cache (avoid re-processing same media)
- Integration with Gemini Vision, OCR, document parsers
"""

import os
import json
import hashlib
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import re

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MediaManager:
    """Manages WhatsApp media files, indexing, and processing cache."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize MediaManager.
        
        Args:
            data_dir: Base data directory (e.g., project/data)
        """
        self.data_dir = Path(data_dir)
        self.media_dir = self.data_dir / "whatsapp_media"
        self.index_file = self.data_dir / "whatsapp_media_index.json"
        self.cache_file = self.data_dir / "whatsapp_media_cache.json"
        
        # Ensure directories exist
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # Load index and cache
        self.index: Dict[str, Dict[str, Any]] = self._load_json(self.index_file, {})
        self.cache: Dict[str, Dict[str, Any]] = self._load_json(self.cache_file, {})
    
    def _load_json(self, path: Path, default: Any) -> Any:
        """Load JSON file or return default."""
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {path}: {e}")
        return default
    
    def _save_index(self):
        """Save media index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def _save_cache(self):
        """Save processing cache to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def get_media_type(self, filename: str) -> str:
        """
        Determine media type from filename.
        
        Returns: 'image', 'pdf', 'document', 'video', 'audio', 'unknown'
        """
        ext = Path(filename).suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic']:
            return 'image'
        elif ext == '.pdf':
            return 'pdf'
        elif ext in ['.pptx', '.ppt']:
            return 'pptx'
        elif ext in ['.docx', '.doc']:
            return 'docx'
        elif ext in ['.xlsx', '.xls']:
            return 'xlsx'
        elif ext in ['.mp4', '.mov', '.avi', '.mkv']:
            return 'video'
        elif ext in ['.mp3', '.ogg', '.opus', '.m4a', '.wav']:
            return 'audio'
        else:
            return 'unknown'
    
    def generate_media_id(self, filename: str) -> str:
        """
        Generate a media ID from filename.
        
        WhatsApp already uses unique names like IMG-20260103-WA0014.jpg
        We'll use the filename stem as ID, prefixed by type.
        
        Returns: e.g., "IMG-20260103-WA0014" or "DOC-sindirim_sistemi_ozet"
        """
        stem = Path(filename).stem
        media_type = self.get_media_type(filename)
        
        # WhatsApp images already have good IDs
        if stem.startswith('IMG-') or stem.startswith('VID-') or stem.startswith('AUD-'):
            return stem
        
        # For other files, create a prefixed ID
        prefix_map = {
            'pdf': 'PDF',
            'pptx': 'PPTX',
            'docx': 'DOC',
            'xlsx': 'XLS',
            'video': 'VID',
            'audio': 'AUD',
            'image': 'IMG',
            'unknown': 'FILE'
        }
        prefix = prefix_map.get(media_type, 'FILE')
        
        # Sanitize filename for ID
        safe_stem = re.sub(r'[^\w\-]', '_', stem)[:50]
        return f"{prefix}-{safe_stem}"
    
    def store_media(
        self,
        file_content: bytes,
        original_filename: str,
        chat_name: str,
        sender: str = "",
        timestamp: str = ""
    ) -> str:
        """
        Store a media file and add to index.
        
        Args:
            file_content: Raw file bytes
            original_filename: Original filename from WhatsApp
            chat_name: WhatsApp chat name
            sender: Message sender
            timestamp: Message timestamp
            
        Returns:
            Media ID
        """
        media_id = self.generate_media_id(original_filename)
        media_type = self.get_media_type(original_filename)
        ext = Path(original_filename).suffix.lower()
        
        # Store file
        file_path = self.media_dir / f"{media_id}{ext}"
        
        # Check if already exists (same ID)
        if media_id in self.index and file_path.exists():
            logger.debug(f"Media already exists: {media_id}")
            return media_id
        
        # Write file
        try:
            with open(file_path, 'wb') as f:
                f.write(file_content)
            logger.info(f"Stored media: {media_id} ({len(file_content)} bytes)")
        except Exception as e:
            logger.error(f"Failed to store media {media_id}: {e}")
            raise
        
        # Add to index
        self.index[media_id] = {
            "id": media_id,
            "type": media_type,
            "path": str(file_path.relative_to(self.data_dir)),
            "original_name": original_filename,
            "chat_name": chat_name,
            "sender": sender,
            "timestamp": timestamp,
            "size_bytes": len(file_content),
            "indexed_at": datetime.now().isoformat()
        }
        self._save_index()
        
        return media_id
    
    def get_media_info(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get media info from index."""
        return self.index.get(media_id)
    
    def get_media_path(self, media_id: str) -> Optional[Path]:
        """Get full path to media file."""
        info = self.index.get(media_id)
        if info:
            return self.data_dir / info["path"]
        return None
    
    def get_cached_result(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get cached processing result if available."""
        return self.cache.get(media_id)
    
    def set_cached_result(self, media_id: str, result: str, model_used: str = ""):
        """Cache a processing result."""
        self.cache[media_id] = {
            "media_id": media_id,
            "result": result,
            "model_used": model_used,
            "processed_at": datetime.now().isoformat()
        }
        self._save_cache()
        logger.info(f"Cached result for {media_id}")
    
    def list_media_by_chat(self, chat_name: str) -> List[Dict[str, Any]]:
        """List all media for a specific chat."""
        return [
            info for info in self.index.values()
            if info.get("chat_name") == chat_name
        ]
    
    def list_unprocessed_media(self) -> List[str]:
        """List media IDs that haven't been processed yet."""
        return [
            media_id for media_id in self.index.keys()
            if media_id not in self.cache
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get media statistics."""
        type_counts = {}
        total_size = 0
        
        for info in self.index.values():
            media_type = info.get("type", "unknown")
            type_counts[media_type] = type_counts.get(media_type, 0) + 1
            total_size += info.get("size_bytes", 0)
        
        return {
            "total_media": len(self.index),
            "cached_results": len(self.cache),
            "by_type": type_counts,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    def extract_date_from_media_id(self, media_id: str) -> Optional[str]:
        """
        Extract date from WhatsApp media ID.
        
        IMG-20260103-WA0014 -> 2026-01-03
        VID-20251231-WA0032 -> 2025-12-31
        
        Returns:
            Date string in YYYY-MM-DD format or None
        """
        # Pattern: XXX-YYYYMMDD-WAxxxx
        match = re.search(r'-(\d{4})(\d{2})(\d{2})-WA', media_id)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
        return None
    
    def match_media_to_messages(self, whatsapp_json_path: Path) -> Dict[str, Any]:
        """
        Match "medya dahil edilmedi" messages with media files based on:
        - Chat name (from filename)
        - Date (from media ID and message timestamp)
        - Order (sequential matching for same date)
        
        Args:
            whatsapp_json_path: Path to parsed WhatsApp JSON file
            
        Returns:
            Dict with match results and updated message count
        """
        import json
        
        # Load messages
        try:
            with open(whatsapp_json_path, 'r', encoding='utf-8') as f:
                messages = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {whatsapp_json_path}: {e}")
            return {"status": "error", "message": str(e)}
        
        # Extract chat name from filename
        # Format: ChatName_ile_WhatsApp_Sohbeti.json
        filename = whatsapp_json_path.stem
        chat_name_match = re.match(r'(.+?)_ile_WhatsApp_Sohbeti', filename)
        if chat_name_match:
            chat_name_from_file = chat_name_match.group(1).replace('_', ' ')
        else:
            chat_name_from_file = filename
        
        # Get all media for this chat (try multiple name variations)
        chat_media = []
        for info in self.index.values():
            indexed_chat = info.get("chat_name", "")
            # Normalize for comparison
            if (indexed_chat.lower().replace(' ', '') == chat_name_from_file.lower().replace(' ', '') or
                chat_name_from_file.lower() in indexed_chat.lower() or
                indexed_chat.lower() in chat_name_from_file.lower()):
                chat_media.append(info)
        
        if not chat_media:
            logger.info(f"No media found for chat: {chat_name_from_file}")
            return {"status": "no_media", "chat_name": chat_name_from_file, "matched": 0}
        
        # Group media by date
        media_by_date: Dict[str, List[Dict]] = {}
        for media in chat_media:
            media_id = media.get("id", "")
            date = self.extract_date_from_media_id(media_id)
            if date:
                if date not in media_by_date:
                    media_by_date[date] = []
                media_by_date[date].append(media)
        
        # Sort each date's media by ID (WA number ensures order)
        for date in media_by_date:
            media_by_date[date].sort(key=lambda x: x.get("id", ""))
        
        # Track which media have been used
        used_media: set = set()
        matched_count = 0
        
        # Process messages
        for msg in messages:
            body = msg.get("body", "")
            
            # Check if this is an unmatched media message
            if "<medya dahil edilmedi>" in body.lower() or "<media omitted>" in body.lower():
                # Already has media_id?
                if msg.get("media_id"):
                    continue
                
                # Extract date from timestamp
                timestamp = msg.get("timestamp", "")
                if not timestamp:
                    continue
                
                msg_date = timestamp[:10]  # YYYY-MM-DD
                
                # Find matching media for this date
                if msg_date in media_by_date:
                    for media in media_by_date[msg_date]:
                        media_id = media.get("id", "")
                        if media_id not in used_media:
                            # Match found!
                            msg["body"] = f"[{media_id}]"
                            msg["media_id"] = media_id
                            msg["type"] = "media_attached"
                            used_media.add(media_id)
                            matched_count += 1
                            logger.debug(f"Matched: {media_id} -> {timestamp}")
                            break
        
        # Save updated messages
        try:
            with open(whatsapp_json_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            logger.info(f"Updated {whatsapp_json_path}: {matched_count} media matched")
        except Exception as e:
            logger.error(f"Failed to save {whatsapp_json_path}: {e}")
            return {"status": "error", "message": str(e)}
        
        return {
            "status": "success",
            "chat_name": chat_name_from_file,
            "matched": matched_count,
            "total_chat_media": len(chat_media),
            "unmatched_media": len(chat_media) - len(used_media)
        }
    
    def match_all_chats(self, whatsapp_data_dir: Path) -> Dict[str, Any]:
        """
        Match media to all WhatsApp JSON files in the data directory.
        
        Args:
            whatsapp_data_dir: Directory containing WhatsApp JSON files
            
        Returns:
            Summary of all matches
        """
        results = []
        total_matched = 0
        
        json_files = list(whatsapp_data_dir.glob("*.json"))
        logger.info(f"Processing {len(json_files)} WhatsApp JSON files...")
        
        for json_file in json_files:
            result = self.match_media_to_messages(json_file)
            results.append({
                "file": json_file.name,
                **result
            })
            if result.get("matched", 0) > 0:
                total_matched += result["matched"]
        
        return {
            "status": "success",
            "files_processed": len(json_files),
            "total_matched": total_matched,
            "details": results
        }


# Singleton instance (will be initialized with proper data_dir)
_media_manager: Optional[MediaManager] = None


def get_media_manager(data_dir: Optional[Path] = None) -> MediaManager:
    """Get or create MediaManager singleton."""
    global _media_manager
    
    if _media_manager is None:
        if data_dir is None:
            # Default to project data dir
            project_root = Path(__file__).resolve().parents[2]
            data_dir = project_root / "data"
        _media_manager = MediaManager(data_dir)
    
    return _media_manager
