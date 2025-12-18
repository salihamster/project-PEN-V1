"""
Agent için Google Drive erişim tool'ları
"""

import json
from typing import List, Dict, Optional
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DriveTools:
    """Agent için Google Drive araçları"""
    
    def __init__(self, service_account_file: str, folder_name: str = "Wpmesages"):
        """
        DriveTools başlat
        
        Args:
            service_account_file: Service account JSON dosyası
            folder_name: Drive'daki klasör adı
        """
        self.service_account_file = service_account_file
        self.folder_name = folder_name
        self.service = None
        self.folder_id = None
        self._connect()
    
    def _connect(self) -> bool:
        """Google Drive'a bağlan"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Klasörü bul
            query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                self.folder_id = files[0]['id']
                logger.info(f"Agent: Drive bağlantısı başarılı ({self.folder_name})")
                return True
            else:
                logger.warning(f"Agent: Drive klasörü bulunamadı ({self.folder_name})")
                return False
        
        except Exception as e:
            logger.error(f"Agent: Drive bağlantı hatası: {e}")
            return False
    
    def list_files(self, file_type: Optional[str] = None, limit: int = 100) -> str:
        """
        Drive'daki dosyaları listele
        
        Args:
            file_type: Dosya tipi filtresi (txt, pdf, zip, vb.)
            limit: Maksimum dosya sayısı
        
        Returns:
            JSON formatında dosya listesi
        """
        try:
            if not self.service or not self.folder_id:
                return json.dumps({
                    "status": "error",
                    "message": "Drive bağlantısı yok"
                })
            
            # Klasördeki dosyaları ara
            query = f"'{self.folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
            
            # Dosya tipi filtresi
            if file_type:
                query += f" and name contains '.{file_type}'"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime, modifiedTime, size, mimeType)',
                orderBy='modifiedTime desc',
                pageSize=limit
            ).execute()
            
            files = results.get('files', [])
            
            # Dosya bilgilerini formatla
            file_list = []
            for f in files:
                file_list.append({
                    'id': f['id'],
                    'name': f['name'],
                    'size': int(f.get('size', 0)),
                    'created': f.get('createdTime', ''),
                    'modified': f.get('modifiedTime', ''),
                    'type': f.get('mimeType', '')
                })
            
            result = {
                "status": "success",
                "folder": self.folder_name,
                "total_files": len(file_list),
                "files": file_list
            }
            
            logger.info(f"Agent: {len(file_list)} dosya listelendi (Drive)")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Agent tool hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def download_file(self, file_id: str, output_path: str) -> str:
        """
        Drive'dan dosya indir
        
        Args:
            file_id: Drive dosya ID
            output_path: Çıktı dosya yolu
        
        Returns:
            JSON formatında sonuç
        """
        try:
            if not self.service:
                return json.dumps({
                    "status": "error",
                    "message": "Drive bağlantısı yok"
                })
            
            # Dosya bilgisini al
            file_info = self.service.files().get(fileId=file_id, fields='name,size').execute()
            file_name = file_info['name']
            file_size = int(file_info.get('size', 0))
            
            # Dosyayı indir
            request = self.service.files().get_media(fileId=file_id)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with io.FileIO(str(output_file), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            result = {
                "status": "success",
                "file_name": file_name,
                "file_size": file_size,
                "output_path": str(output_file),
                "message": f"Dosya indirildi: {file_name}"
            }
            
            logger.info(f"Agent: Dosya indirildi - {file_name}")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Agent tool hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def download_file_by_name(self, file_name: str, output_dir: str) -> str:
        """
        Drive'dan dosyayı ismine göre indir
        
        Args:
            file_name: Dosya adı
            output_dir: Çıktı dizini
        
        Returns:
            JSON formatında sonuç
        """
        try:
            if not self.service or not self.folder_id:
                return json.dumps({
                    "status": "error",
                    "message": "Drive bağlantısı yok"
                })
            
            # Dosyayı ara
            query = f"'{self.folder_id}' in parents and name='{file_name}' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                return json.dumps({
                    "status": "error",
                    "message": f"Dosya bulunamadı: {file_name}"
                })
            
            # İlk eşleşen dosyayı indir
            file_id = files[0]['id']
            output_path = str(Path(output_dir) / file_name)
            
            return self.download_file(file_id, output_path)
        
        except Exception as e:
            logger.error(f"Agent tool hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def search_files(self, query: str, limit: int = 20) -> str:
        """
        Drive'da dosya ara
        
        Args:
            query: Arama sorgusu (dosya adında)
            limit: Maksimum sonuç sayısı
        
        Returns:
            JSON formatında arama sonuçları
        """
        try:
            if not self.service or not self.folder_id:
                return json.dumps({
                    "status": "error",
                    "message": "Drive bağlantısı yok"
                })
            
            # Dosya adında ara
            search_query = f"'{self.folder_id}' in parents and name contains '{query}' and trashed=false"
            results = self.service.files().list(
                q=search_query,
                spaces='drive',
                fields='files(id, name, createdTime, modifiedTime, size)',
                orderBy='modifiedTime desc',
                pageSize=limit
            ).execute()
            
            files = results.get('files', [])
            
            # Dosya bilgilerini formatla
            file_list = []
            for f in files:
                file_list.append({
                    'id': f['id'],
                    'name': f['name'],
                    'size': int(f.get('size', 0)),
                    'created': f.get('createdTime', ''),
                    'modified': f.get('modifiedTime', '')
                })
            
            result = {
                "status": "success",
                "query": query,
                "total_results": len(file_list),
                "files": file_list
            }
            
            logger.info(f"Agent: '{query}' için {len(file_list)} dosya bulundu (Drive)")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Agent tool hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def get_file_info(self, file_id: str) -> str:
        """
        Dosya bilgilerini getir
        
        Args:
            file_id: Drive dosya ID
        
        Returns:
            JSON formatında dosya bilgileri
        """
        try:
            if not self.service:
                return json.dumps({
                    "status": "error",
                    "message": "Drive bağlantısı yok"
                })
            
            file_info = self.service.files().get(
                fileId=file_id,
                fields='id, name, size, createdTime, modifiedTime, mimeType, owners'
            ).execute()
            
            result = {
                "status": "success",
                "file": {
                    'id': file_info['id'],
                    'name': file_info['name'],
                    'size': int(file_info.get('size', 0)),
                    'created': file_info.get('createdTime', ''),
                    'modified': file_info.get('modifiedTime', ''),
                    'type': file_info.get('mimeType', ''),
                    'owners': [o.get('emailAddress', '') for o in file_info.get('owners', [])]
                }
            }
            
            logger.info(f"Agent: Dosya bilgisi alındı - {file_info['name']}")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Agent tool hatası: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })


def get_drive_tools_description() -> str:
    """
    Drive tool'larının açıklamasını döndür
    
    Returns:
        Tool açıklamaları
    """
    return """
# Agent Google Drive Tool'ları

## 1. list_files(file_type=None, limit=100)
Drive'daki dosyaları listeler.

**Parametreler**:
- file_type: Dosya tipi filtresi (txt, pdf, zip)
- limit: Maksimum dosya sayısı (varsayılan: 100)

**Örnek**:
```python
drive_tools.list_files(file_type="txt", limit=50)
```

## 2. download_file(file_id, output_path)
Drive'dan dosya indirir (ID ile).

**Parametreler**:
- file_id: Drive dosya ID (zorunlu)
- output_path: Çıktı dosya yolu (zorunlu)

**Örnek**:
```python
drive_tools.download_file("abc123", "downloads/file.txt")
```

## 3. download_file_by_name(file_name, output_dir)
Drive'dan dosya indirir (isim ile).

**Parametreler**:
- file_name: Dosya adı (zorunlu)
- output_dir: Çıktı dizini (zorunlu)

**Örnek**:
```python
drive_tools.download_file_by_name("sohbet.txt", "downloads/")
```

## 4. search_files(query, limit=20)
Drive'da dosya arar.

**Parametreler**:
- query: Arama sorgusu (zorunlu)
- limit: Maksimum sonuç sayısı (varsayılan: 20)

**Örnek**:
```python
drive_tools.search_files("WhatsApp", limit=10)
```

## 5. get_file_info(file_id)
Dosya bilgilerini getirir.

**Parametreler**:
- file_id: Drive dosya ID (zorunlu)

**Örnek**:
```python
drive_tools.get_file_info("abc123")
```
"""
