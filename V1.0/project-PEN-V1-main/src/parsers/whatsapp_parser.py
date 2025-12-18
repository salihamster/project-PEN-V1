"""
WhatsApp mesajlarını parse etme modülü
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppParser:
    """WhatsApp TXT dosyalarını parse eder"""
    
    def __init__(self):
        self.messages = []
    
    def parse_file(self, file_path: str) -> List[Dict]:
        """
        WhatsApp TXT dosyasını parse et
        
        Args:
            file_path: WhatsApp export dosyası yolu
        
        Returns:
            Parse edilmiş mesajlar listesi
        """
        logger.info(f"WhatsApp dosyası parse ediliyor: {file_path}")
        
        try:
            # Farklı encoding'leri dene
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1254']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    logger.info(f"Dosya {encoding} encoding ile okundu")
                    break
                except UnicodeDecodeError:
                    continue
            
            if lines is None:
                logger.error(f"Dosya hiçbir encoding ile okunamadı")
                return []
            
            logger.info(f"{len(lines)} satır okundu")
            
            self.messages = []
            current_message = None
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                # WhatsApp mesaj formatı: DD.MM.YYYY HH:MM - Gönderici: Mesaj
                match = re.match(
                    r'(\d{1,2}\.\d{1,2}\.\d{4})\s+(\d{1,2}:\d{2})\s+-\s+(.+?):\s+(.*)',
                    line
                )
                
                if match:
                    # Önceki mesajı kaydet
                    if current_message:
                        self.messages.append(current_message)
                    
                    # Yeni mesaj başlat
                    date_str = match.group(1)
                    time_str = match.group(2)
                    sender = match.group(3).strip()
                    body = match.group(4).strip()
                    
                    # Tarih ve saati parse et
                    try:
                        datetime_str = f"{date_str} {time_str}"
                        timestamp = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
                    except Exception as e:
                        logger.warning(f"Tarih parse hatası: {e}")
                        timestamp = datetime.now()
                    
                    current_message = {
                        'timestamp': timestamp.isoformat(),
                        'sender': sender,
                        'body': body,
                        'source': 'whatsapp',
                        'type': self._detect_message_type(body)
                    }
                else:
                    # Çok satırlı mesaj devamı
                    if current_message:
                        current_message['body'] += '\n' + line
            
            # Son mesajı kaydet
            if current_message:
                self.messages.append(current_message)
            
            logger.info(f"{len(self.messages)} mesaj parse edildi")
            return self.messages
        
        except Exception as e:
            logger.error(f"Parse hatası: {e}")
            return []
    
    def _detect_message_type(self, body: str) -> str:
        """
        Mesaj tipini belirle
        
        Args:
            body: Mesaj içeriği
        
        Returns:
            Mesaj tipi (text, image, video, audio, document, link)
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
        Mesaj istatistiklerini hesapla
        
        Returns:
            İstatistik bilgileri
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
            # Gönderici istatistikleri
            sender = msg['sender']
            if sender not in stats['senders']:
                stats['senders'][sender] = 0
            stats['senders'][sender] += 1
            
            # Mesaj tipi istatistikleri
            msg_type = msg['type']
            if msg_type not in stats['message_types']:
                stats['message_types'][msg_type] = 0
            stats['message_types'][msg_type] += 1
            
            # Tarih aralığı
            timestamp = msg['timestamp']
            if stats['date_range']['start'] is None or timestamp < stats['date_range']['start']:
                stats['date_range']['start'] = timestamp
            if stats['date_range']['end'] is None or timestamp > stats['date_range']['end']:
                stats['date_range']['end'] = timestamp
        
        # Göndericileri mesaj sayısına göre sırala
        stats['senders'] = dict(
            sorted(stats['senders'].items(), key=lambda x: x[1], reverse=True)
        )
        
        return stats
    
    def save_to_json(self, output_path: str) -> bool:
        """
        Mesajları JSON dosyasına kaydet
        
        Args:
            output_path: Çıktı dosyası yolu
        
        Returns:
            Başarılı ise True
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Mesajlar kaydedildi: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Kaydetme hatası: {e}")
            return False
