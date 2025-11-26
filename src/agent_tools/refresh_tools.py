"""
Agent için veri güncelleme tool'ları
"""

import json
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path

from ..parsers.email_parser import EmailParser
from ..parsers.drive_sync import auto_sync_from_drive
from ..storage.data_manager import DataManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RefreshTools:
    """Agent için veri güncelleme araçları"""
    
    def __init__(self, data_manager: DataManager, email_config: Dict, 
                 service_account_file: Optional[str] = None):
        """
        RefreshTools başlat
        
        Args:
            data_manager: DataManager instance
            email_config: Email yapılandırması
            service_account_file: Service account JSON dosyası (Drive için)
        """
        self.data_manager = data_manager
        self.email_config = email_config
        self.service_account_file = service_account_file
    
    def refresh_emails(self, search_query: Optional[str] = None, 
                      limit: int = 50) -> str:
        """
        Email'leri yeniden çek (güncel veri) ve sadece yeni olanları yerel veritabanına ekle.
        
        Args:
            search_query: Email arama sorgusu (örn: "from:penelope@ac.com")
            limit: Maksimum email sayısı
        
        Returns:
            JSON formatında sonuç: meta bilgilerle birlikte yeni eklenen emaillerin kısa listesi
        """
        try:
            logger.info(f"Agent: Email'ler güncelleniyor (query: {search_query})")
            
            # Email parser oluştur
            parser = EmailParser(
                email_address=self.email_config['address'],
                password=self.email_config['password'],
                imap_server=self.email_config['imap_server'],
                imap_port=self.email_config['imap_port'],
                max_workers=self.email_config.get('max_workers', 5)
            )
            
            # Bağlan
            if not parser.connect():
                return json.dumps({
                    "status": "error",
                    "message": "Email sunucusuna bağlanılamadı"
                })
            
            try:
                # Mevcut email anahtarlarını yükle (id veya timestamp+subject fallback)
                try:
                    existing = self.data_manager.get_emails(exclude_spam=False)
                except Exception:
                    existing = []
                existing_keys = set()
                for e in existing:
                    if e.get('id'):
                        existing_keys.add(f"id::{e.get('id')}")
                    else:
                        existing_keys.add(f"ts_subj::{e.get('timestamp')}::{e.get('subject')}")
                
                # Email'leri çek
                if search_query:
                    fetched = parser.fetch_emails_with_search(
                        search_criteria=search_query,
                        limit=limit,
                        parallel=True
                    )
                else:
                    fetched = parser.fetch_emails(
                        folder='INBOX',
                        limit=limit,
                        parallel=True
                    )
                
                if not fetched:
                    return json.dumps({
                        "status": "success",
                        "message": "Yeni email bulunamadı",
                        "total_emails": len(existing),
                        "new_emails": 0,
                        "new_emails_details": []
                    }, ensure_ascii=False, indent=2)
                
                # YENİ emailleri tespit et (yalnızca yeni olanları kaydet)
                def key_of(e):
                    return f"id::{e.get('id')}" if e.get('id') else f"ts_subj::{e.get('timestamp')}::{e.get('subject')}"
                new_emails = [e for e in fetched if key_of(e) not in existing_keys]
                
                if not new_emails:
                    return json.dumps({
                        "status": "success",
                        "message": "Yeni email yok (hepsi mevcut)",
                        "total_emails": len(existing),
                        "new_emails": 0,
                        "new_emails_details": []
                    }, ensure_ascii=False, indent=2)
                
                # Yalnızca yeni emailleri kaydet
                save_result = self.data_manager.save_emails(new_emails)
                
                # Yanıta kısa özet listesi ekle
                short_list = []
                for e in new_emails[:100]:
                    short_list.append({
                        "id": e.get('id'),
                        "timestamp": e.get('timestamp'),
                        "from": e.get('from'),
                        "to": e.get('to'),
                        "subject": e.get('subject'),
                        "snippet": (e.get('snippet') or (e.get('body') or '')[:200]).strip()
                    })
                
                response = {
                    "status": "success",
                    "message": "Email'ler güncellendi",
                    "total_emails": save_result.total_count,
                    "new_emails": save_result.new_count,
                    "existing_emails": save_result.existing_count,
                    "search_query": search_query,
                    "updated_at": datetime.now().isoformat(),
                    "new_emails_details": short_list
                }
                
                logger.info(f"Agent: {save_result.new_count} yeni email eklendi")
                return json.dumps(response, ensure_ascii=False, indent=2)
            
            finally:
                parser.disconnect()
        
        except Exception as e:
            logger.error(f"Email refresh hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, ensure_ascii=False)
    
    def refresh_drive_files(self, folder_name: str = "Wpmesages") -> str:
        """
        Google Drive'dan yeni dosyaları çek
        
        Args:
            folder_name: Drive klasör adı
        
        Returns:
            JSON formatında sonuç
        """
        try:
            if not self.service_account_file:
                return json.dumps({
                    "status": "error",
                    "message": "Service account dosyası yapılandırılmamış"
                })
            
            logger.info(f"Agent: Drive dosyaları güncelleniyor ({folder_name})")
            
            # WhatsApp export klasörü
            from pathlib import Path
            whatsapp_dir = Path("whatsapp_export")
            whatsapp_dir.mkdir(parents=True, exist_ok=True)
            
            # Drive'dan çek
            downloaded_files = auto_sync_from_drive(
                service_account_file=self.service_account_file,
                output_dir=whatsapp_dir,
                folder_name=folder_name
            )
            
            if not downloaded_files:
                return json.dumps({
                    "status": "success",
                    "message": "Drive'da yeni dosya yok",
                    "downloaded_files": 0
                })
            
            # Dosyaları parse et
            from ..parsers.whatsapp_parser import WhatsAppParser
            parser = WhatsAppParser()
            
            processed_chats = []
            for file_path in downloaded_files:
                if file_path.endswith('.txt'):
                    messages = parser.parse_file(file_path)
                    if messages:
                        chat_name = Path(file_path).stem
                        result = self.data_manager.save_whatsapp_messages(messages, chat_name)
                        processed_chats.append({
                            "chat_name": chat_name,
                            "total_messages": result.total_count,
                            "new_messages": result.new_count
                        })
            
            response = {
                "status": "success",
                "message": "Drive dosyaları güncellendi",
                "downloaded_files": len(downloaded_files),
                "processed_chats": len(processed_chats),
                "chats": processed_chats,
                "updated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Agent: {len(downloaded_files)} dosya indirildi, {len(processed_chats)} sohbet işlendi")
            return json.dumps(response, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Drive refresh hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, ensure_ascii=False)
    
    def check_for_updates(self) -> str:
        """
        Güncellemeleri kontrol et (Drive ve Email)
        
        Returns:
            JSON formatında özet
        """
        try:
            logger.info("Agent: Güncellemeler kontrol ediliyor")
            
            updates = {
                "status": "success",
                "checked_at": datetime.now().isoformat(),
                "drive": {"available": False, "new_files": 0},
                "email": {"available": False, "estimated_new": 0}
            }
            
            # Drive kontrolü
            if self.service_account_file:
                try:
                    from ..parsers.drive_sync import list_drive_files
                    files = list_drive_files(
                        service_account_file=self.service_account_file,
                        folder_name="Wpmesages"
                    )
                    updates["drive"]["available"] = True
                    updates["drive"]["new_files"] = len(files)
                except:
                    pass
            
            # Email kontrolü (sadece sayı tahmini)
            if self.email_config.get('address'):
                updates["email"]["available"] = True
                updates["email"]["estimated_new"] = "Bilinmiyor (refresh_emails çalıştırın)"
            
            logger.info("Agent: Güncelleme kontrolü tamamlandı")
            return json.dumps(updates, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Update check hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            }, ensure_ascii=False)


def get_refresh_tools_description() -> str:
    """
    Refresh tool'larının açıklamasını döndür
    
    Returns:
        Tool açıklamaları
    """
    return """
# Agent Veri Güncelleme Tool'ları

## 1. refresh_emails(search_query=None, limit=50)
Email'leri yeniden çeker (güncel veri).

**Parametreler**:
- search_query: Email arama sorgusu (örn: "from:penelope@ac.com")
- limit: Maksimum email sayısı (varsayılan: 50)

**Örnek**:
```python
refresh_tools.refresh_emails(search_query="from:penelope@ac.com", limit=20)
```

## 2. refresh_drive_files(folder_name="Wpmesages")
Google Drive'dan yeni dosyaları çeker.

**Parametreler**:
- folder_name: Drive klasör adı (varsayılan: "Wpmesages")

**Örnek**:
```python
refresh_tools.refresh_drive_files()
```

## 3. check_for_updates()
Güncellemeleri kontrol eder (Drive ve Email).

**Parametreler**: Yok

**Örnek**:
```python
refresh_tools.check_for_updates()
```

## Kullanım Senaryoları:
- "Penelope'den yeni mail var mı?" → refresh_emails(search_query="from:penelope@ac.com")
- "Drive'da yeni WhatsApp export var mı?" → refresh_drive_files()
- "Güncellemeleri kontrol et" → check_for_updates()
"""
