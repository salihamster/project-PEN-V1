"""
Email mesajlarını parse etme modülü
"""

import imaplib
import json
from email.parser import Parser
from email.utils import parsedate_to_datetime
from email.header import decode_header, make_header
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmailParser:
    """Email mesajlarını IMAP üzerinden çeker ve parse eder"""
    
    def __init__(self, email_address: str, password: str, 
                 imap_server: str = "imap.gmail.com", imap_port: int = 993,
                 max_workers: int = 5):
        """
        EmailParser başlat
        
        Args:
            email_address: Email adresi
            password: Email şifresi (app password)
            imap_server: IMAP sunucu adresi
            imap_port: IMAP port numarası
            max_workers: Paralel işlem sayısı (varsayılan: 5)
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.max_workers = max_workers
        self.mail = None
        self.emails = []
        self.emails_lock = Lock()
    
    def connect(self) -> bool:
        """
        IMAP sunucusuna bağlan
        
        Returns:
            Başarılı ise True
        """
        try:
            logger.info(f"IMAP sunucusuna bağlanılıyor: {self.imap_server}")
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=30)
            self.mail.login(self.email_address, self.password)
            logger.info("IMAP bağlantısı başarılı")
            return True
        except Exception as e:
            logger.error(f"IMAP bağlantı hatası: {e}")
            return False
    
    def disconnect(self):
        """IMAP bağlantısını kapat"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                logger.info("IMAP bağlantısı kapatıldı")
            except:
                pass
    
    def fetch_emails(self, folder: str = 'INBOX', limit: Optional[int] = None, 
                    parallel: bool = True) -> List[Dict]:
        """
        Email'leri çek (paralel veya seri)
        
        Args:
            folder: Email klasörü (INBOX, Sent, etc.)
            limit: Maksimum email sayısı (None = tümü)
            parallel: Paralel işlem kullan (varsayılan: True)
        
        Returns:
            Parse edilmiş email listesi
        """
        if not self.mail:
            logger.error("IMAP bağlantısı yok. Önce connect() çağırın.")
            return []
        
        try:
            logger.info(f"{folder} klasöründen email'ler çekiliyor...")
            self.mail.select(folder)
            
            status, messages = self.mail.search(None, 'ALL')
            email_ids = messages[0].split()
            
            # Limit varsa son 'limit' email'i al
            if limit:
                email_ids = email_ids[-limit:]
            
            total = len(email_ids)
            logger.info(f"{total} email bulundu, işleniyor...")
            
            if parallel and total > 10:
                logger.info(f"Paralel işlem kullanılıyor ({self.max_workers} thread)")
                return self._fetch_emails_parallel(email_ids)
            else:
                logger.info("Seri işlem kullanılıyor")
                return self._fetch_emails_serial(email_ids)
        
        except Exception as e:
            logger.error(f"Email çekme hatası: {e}")
            return []
    
    def fetch_emails_with_search(self, search_criteria: str, 
                                 limit: Optional[int] = None,
                                 parallel: bool = True) -> List[Dict]:
        """
        Belirli kriterlere göre email'leri çek
        
        Args:
            search_criteria: IMAP arama kriteri (örn: 'FROM "penelope@ac.com"')
            limit: Maksimum email sayısı (None = tümü)
            parallel: Paralel işlem kullan (varsayılan: True)
        
        Returns:
            Parse edilmiş email listesi
        
        Örnek arama kriterleri:
            - 'FROM "user@example.com"'
            - 'SUBJECT "meeting"'
            - 'SINCE "01-Jan-2024"'
            - 'FROM "user@example.com" SINCE "01-Jan-2024"'
        """
        if not self.mail:
            logger.error("IMAP bağlantısı yok. Önce connect() çağırın.")
            return []
        
        try:
            logger.info(f"Email arama yapılıyor: {search_criteria}")
            self.mail.select('INBOX')
            
            # IMAP search
            status, messages = self.mail.search(None, search_criteria)
            email_ids = messages[0].split()
            
            if not email_ids:
                logger.info("Arama kriterine uyan email bulunamadı")
                return []
            
            # Limit varsa son 'limit' email'i al
            if limit:
                email_ids = email_ids[-limit:]
            
            total = len(email_ids)
            logger.info(f"{total} email bulundu, işleniyor...")
            
            if parallel and total > 10:
                logger.info(f"Paralel işlem kullanılıyor ({self.max_workers} thread)")
                return self._fetch_emails_parallel(email_ids)
            else:
                logger.info("Seri işlem kullanılıyor")
                return self._fetch_emails_serial(email_ids)
        
        except Exception as e:
            logger.error(f"Email arama hatası: {e}")
            return []
    
    def _fetch_emails_serial(self, email_ids: List[bytes]) -> List[Dict]:
        """
        Email'leri seri olarak çek (eski yöntem)
        
        Args:
            email_ids: Email ID listesi
        
        Returns:
            Parse edilmiş email listesi
        """
        self.emails = []
        total = len(email_ids)
        
        for idx, email_id in enumerate(email_ids, 1):
            try:
                status, msg_data = self.mail.fetch(email_id, '(RFC822)')
                msg = Parser().parsestr(msg_data[0][1].decode('utf-8', errors='ignore'))
                
                email_obj = self._parse_email_message(msg)
                self.emails.append(email_obj)
                
                # İlerleme göster
                if idx % 50 == 0 or idx == total:
                    percent = (idx * 100) // total
                    logger.info(f"İşleniyor: {idx}/{total} ({percent}%)")
            
            except Exception as e:
                logger.warning(f"Email parse hatası (ID: {email_id}): {str(e)[:50]}")
                continue
        
        logger.info(f"{len(self.emails)} email çekildi")
        return self.emails
    
    def _fetch_emails_parallel(self, email_ids: List[bytes]) -> List[Dict]:
        """
        Email'leri paralel olarak çek (hızlı)
        
        Args:
            email_ids: Email ID listesi
        
        Returns:
            Parse edilmiş email listesi
        """
        self.emails = []
        total = len(email_ids)
        processed = 0
        
        # ThreadPoolExecutor ile paralel işlem
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Her thread için ayrı IMAP bağlantısı oluştur
            future_to_id = {
                executor.submit(self._fetch_single_email, email_id): email_id 
                for email_id in email_ids
            }
            
            # Sonuçları topla
            for future in as_completed(future_to_id):
                email_id = future_to_id[future]
                try:
                    email_obj = future.result()
                    if email_obj:
                        with self.emails_lock:
                            self.emails.append(email_obj)
                    
                    processed += 1
                    
                    # İlerleme göster
                    if processed % 50 == 0 or processed == total:
                        percent = (processed * 100) // total
                        logger.info(f"İşleniyor: {processed}/{total} ({percent}%)")
                
                except Exception as e:
                    logger.warning(f"Email parse hatası: {str(e)[:50]}")
                    processed += 1
        
        logger.info(f"{len(self.emails)} email çekildi (paralel)")
        return self.emails
    
    def _fetch_single_email(self, email_id: bytes) -> Optional[Dict]:
        """
        Tek bir email'i çek (thread-safe)
        
        Args:
            email_id: Email ID
        
        Returns:
            Parse edilmiş email objesi veya None
        """
        try:
            # Her thread için yeni IMAP bağlantısı
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=30)
            mail.login(self.email_address, self.password)
            mail.select('INBOX')
            
            # Email'i çek
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            msg = Parser().parsestr(msg_data[0][1].decode('utf-8', errors='ignore'))
            
            # Parse et
            email_obj = self._parse_email_message(msg)
            
            # Bağlantıyı kapat
            mail.close()
            mail.logout()
            
            return email_obj
        
        except Exception as e:
            logger.debug(f"Email ��ekme hatası (ID: {email_id}): {str(e)[:50]}")
            return None
    
    def _decode_header_value(self, value: Optional[str]) -> str:
        """Decode MIME-encoded header to a readable Unicode string."""
        try:
            return str(make_header(decode_header(value or "")))
        except Exception:
            return value or ""

    def _parse_email_message(self, msg) -> Dict:
        """
        Email message objesini parse et
        
        Args:
            msg: Email message objesi
        
        Returns:
            Parse edilmiş email objesi
        """
        # Timestamp'i parse et
        try:
            timestamp = parsedate_to_datetime(msg['Date']).isoformat()
        except:
            timestamp = datetime.now().isoformat()
        
        # Decode headers to store readable text
        msg_id = msg.get('Message-ID', '')
        from_decoded = self._decode_header_value(msg.get('From', ''))
        to_decoded = self._decode_header_value(msg.get('To', ''))
        subject_decoded = self._decode_header_value(msg.get('Subject', ''))
        
        return {
            'id': msg_id,
            'from': from_decoded,
            'to': to_decoded,
            'subject': subject_decoded,
            'body': self._get_email_body(msg),
            'timestamp': timestamp,
            'source': 'email',
            'is_spam': self._is_spam(msg)
        }
    
    def _get_email_body(self, msg) -> str:
        """
        Email gövdesini çıkar
        
        Args:
            msg: Email message objesi
        
        Returns:
            Email gövdesi (ilk 1000 karakter)
        """
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())
        
        return body[:1000]  # İlk 1000 karakter
    
    def _is_spam(self, msg) -> bool:
        """
        Email'in spam/reklam olup olmadığını kontrol et
        
        Args:
            msg: Email message objesi
        
        Returns:
            Spam ise True
        """
        spam_keywords = [
            'noreply', 'no-reply', 'notification', 'alert',
            'marketing', 'promo', 'newsletter', 'unsubscribe',
            'promotional', 'deal', 'offer', 'discount'
        ]
        
        from_field = self._decode_header_value(msg.get('From', '')).lower()
        subject = self._decode_header_value(msg.get('Subject', '')).lower()
        
        for keyword in spam_keywords:
            if keyword in from_field or keyword in subject:
                return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        Email istatistiklerini hesapla
        
        Returns:
            İstatistik bilgileri
        """
        if not self.emails:
            return {}
        
        stats = {
            'total_emails': len(self.emails),
            'spam_count': sum(1 for e in self.emails if e['is_spam']),
            'senders': {},
            'date_range': {
                'start': None,
                'end': None
            }
        }
        
        for email in self.emails:
            # Gönderici istatistikleri
            sender = email['from'].split('<')[0].strip() if '<' in email['from'] else email['from']
            if sender not in stats['senders']:
                stats['senders'][sender] = 0
            stats['senders'][sender] += 1
            
            # Tarih aralığı
            timestamp = email['timestamp']
            if stats['date_range']['start'] is None or timestamp < stats['date_range']['start']:
                stats['date_range']['start'] = timestamp
            if stats['date_range']['end'] is None or timestamp > stats['date_range']['end']:
                stats['date_range']['end'] = timestamp
        
        # Göndericileri email sayısına göre sırala
        stats['senders'] = dict(
            sorted(stats['senders'].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return stats
    
    def save_to_json(self, output_path: str) -> bool:
        """
        Email'leri JSON dosyasına kaydet
        
        Args:
            output_path: Çıktı dosyası yolu
        
        Returns:
            Başarılı ise True
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.emails, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Email'ler kaydedildi: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Kaydetme hatası: {e}")
            return False
