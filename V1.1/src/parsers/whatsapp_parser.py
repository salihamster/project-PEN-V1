"""
WhatsApp message parsing module
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppParser:
    """Parses WhatsApp TXT export files"""
    
    def __init__(self):
        self.messages = []
    
    def parse_file(self, file_path: str) -> List[Dict]:
        """
        Parse WhatsApp TXT file
        
        Args:
            file_path: WhatsApp export file path
        
        Returns:
            List of parsed messages
        """
        logger.info(f"Parsing WhatsApp file: {file_path}")
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1254']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    logger.info(f"File read with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if lines is None:
                logger.error(f"File could not be read with any encoding")
                return []
            
            logger.info(f"{len(lines)} lines read")
            
            self.messages = []
            current_message = None
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                # WhatsApp message format: DD.MM.YYYY HH:MM - Sender: Message
                match = re.match(
                    r'(\d{1,2}\.\d{1,2}\.\d{4})\s+(\d{1,2}:\d{2})\s+-\s+(.+?):\s+(.*)',
                    line
                )
                
                if match:
                    # Save previous message
                    if current_message:
                        self.messages.append(current_message)
                    
                    # Start new message
                    date_str = match.group(1)
                    time_str = match.group(2)
                    sender = match.group(3).strip()
                    body = match.group(4).strip()
                    
                    # Parse date and time
                    try:
                        datetime_str = f"{date_str} {time_str}"
                        timestamp = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
                    except Exception as e:
                        logger.warning(f"Date parse error: {e}")
                        timestamp = datetime.now()
                    
                    current_message = {
                        'timestamp': timestamp.isoformat(),
                        'sender': sender,
                        'body': body,
                        'source': 'whatsapp',
                        'type': self._detect_message_type(body)
                    }
                else:
                    # Multi-line message continuation
                    if current_message:
                        current_message['body'] += '\n' + line
            
            # Save last message
            if current_message:
                self.messages.append(current_message)
            
            logger.info(f"{len(self.messages)} messages parsed")
            return self.messages
        
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return []
    
    def _detect_message_type(self, body: str) -> str:
        """
        Detect message type
        
        Args:
            body: Message content
        
        Returns:
            Message type (text, image, video, audio, document, link)
        """
        body_lower = body.lower()
        
        if '<medya dahil edilmedi>' in body_lower or '<media omitted>' in body_lower:
            return 'media'
        elif body.startswith('http://') or body.startswith('https://'):
            return 'link'
        elif 'dosya eklendi' in body_lower or 'file attached' in body_lower:
            return 'document'
        else:
            return 'text'
    
    def get_statistics(self) -> Dict:
        """
        Calculate message statistics
        
        Returns:
            Statistics information
        """
        if not self.messages:
            return {}
        
        stats = {
            'total_messages': len(self.messages),
            'senders': {},
            'message_types': {},
            'date_range': {
                'start': None,
                'end': None
            }
        }
        
        for msg in self.messages:
            # Sender statistics
            sender = msg['sender']
            if sender not in stats['senders']:
                stats['senders'][sender] = 0
            stats['senders'][sender] += 1
            
            # Message type statistics
            msg_type = msg['type']
            if msg_type not in stats['message_types']:
                stats['message_types'][msg_type] = 0
            stats['message_types'][msg_type] += 1
            
            # Date range
            timestamp = msg['timestamp']
            if stats['date_range']['start'] is None or timestamp < stats['date_range']['start']:
                stats['date_range']['start'] = timestamp
            if stats['date_range']['end'] is None or timestamp > stats['date_range']['end']:
                stats['date_range']['end'] = timestamp
        
        # Sort senders by message count
        stats['senders'] = dict(
            sorted(stats['senders'].items(), key=lambda x: x[1], reverse=True)
        )
        
        return stats
    
    def save_to_json(self, output_path: str) -> bool:
        """
        Save messages to JSON file
        
        Args:
            output_path: Output file path
        
        Returns:
            True if successful
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Messages saved: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
