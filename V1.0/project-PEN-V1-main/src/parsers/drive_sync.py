"""
Google Drive senkronizasyon modülü
Manuel upload → Otomatik download → Otomatik silme
"""

import os
import io
import zipfile
import gzip
import zlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DriveSync:
    """Google Drive senkronizasyon"""
    
    def __init__(self, service_account_file: str, folder_name: str = "PEN_WhatsApp_Exports"):
        """
        DriveSync başlat
        
        Args:
            service_account_file: Service account JSON dosyası
            folder_name: Drive'daki klasör adı
        """
        self.service_account_file = service_account_file
        self.folder_name = folder_name
        self.service = None
        self.folder_id = None
    
    def connect(self) -> bool:
        """
        Google Drive'a bağlan
        
        Returns:
            Başarılı ise True
        """
        try:
            logger.info("Google Drive'a bağlanılıyor...")
            
            # Service account ile kimlik doğrulama
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            # Drive API servisi
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Klasörü bul veya oluştur
            self.folder_id = self._get_or_create_folder()
            
            logger.info(f"✅ Google Drive bağlantısı başarılı")
            logger.info(f"   Klasör: {self.folder_name}")
            return True
        
        except Exception as e:
            logger.error(f"Google Drive bağlantı hatası: {e}")
            return False
    
    def _get_or_create_folder(self) -> str:
        """
        Klasörü bul veya oluştur
        
        Returns:
            Klasör ID
        """
        try:
            # Klasörü ara
            query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                # Klasör var
                folder_id = files[0]['id']
                logger.info(f"Klasör bulundu: {self.folder_name}")
                return folder_id
            else:
                # Klasör yok, oluştur
                logger.info(f"Klasör oluşturuluyor: {self.folder_name}")
                file_metadata = {
                    'name': self.folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                
                folder_id = folder.get('id')
                logger.info(f"✅ Klasör oluşturuldu: {self.folder_name}")
                return folder_id
        
        except Exception as e:
            logger.error(f"Klasör işlemi hatası: {e}")
            raise
    
    def list_files(self, file_extensions: List[str] = None) -> List[Dict]:
        """
        Drive'daki dosyaları listele
        
        Args:
            file_extensions: Dosya uzantıları (None = tümü)
        
        Returns:
            Dosya listesi
        """
        try:
            logger.info(f"Drive'daki dosyalar listeleniyor...")
            
            # Klasördeki dosyaları ara (klasör olmayan)
            query = f"'{self.folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
            
            # Uzantı filtresi (opsiyonel)
            if file_extensions:
                ext_queries = [f"name contains '{ext}'" for ext in file_extensions]
                query += f" and ({' or '.join(ext_queries)})"
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime, size, mimeType)',
                orderBy='createdTime desc'
            ).execute()
            
            files = results.get('files', [])
            
            logger.info(f"✅ {len(files)} dosya bulundu")
            return files
        
        except Exception as e:
            logger.error(f"Dosya listeleme hatası: {e}")
            return []
    
    def download_file(self, file_id: str, file_name: str, output_dir: Path) -> List[str]:
        """
        Dosyayı indir (ZIP ise aç)
        
        Args:
            file_id: Drive dosya ID
            file_name: Dosya adı
            output_dir: Çıktı dizini
        
        Returns:
            İndirilen/çıkarılan dosya yollar��
        """
        try:
            logger.info(f"📥 İndiriliyor: {file_name[:50]}...")
            
            # Dosyayı indir
            request = self.service.files().get_media(fileId=file_id)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Dosya adını temizle (Windows için)
            safe_name = self._sanitize_filename(file_name)
            
            # .txt uzantısı yoksa ekle
            if not safe_name.endswith('.txt') and not safe_name.endswith('.zip'):
                safe_name += '.txt'
            
            # Geçici dosya
            temp_path = output_dir / safe_name
            
            with io.FileIO(str(temp_path), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                last_progress = 0
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        # Her %10'da log
                        if progress >= last_progress + 10:
                            logger.info(f"   Progress: %{progress}")
                            last_progress = progress
            
            logger.info(f"✅ İndirildi: {safe_name[:50]}...")
            
            # Dosya içeriğine bakarak ZIP mi kontrol et
            with open(temp_path, 'rb') as f:
                header = f.read(4)
            
            # ZIP header mı? (PK\x03\x04)
            if header[:2] == b'PK':
                logger.info(f"   ZIP dosyası tespit edildi (header kontrolü)")
                return self._extract_zip(temp_path, output_dir)
            
            # ZIP değilse decompress dene
            decompressed_path = self._try_decompress(temp_path)
            return [str(decompressed_path)]
        
        except Exception as e:
            logger.error(f"Dosya indirme hatası: {e}")
            return []
    
    def _try_decompress(self, file_path: Path) -> Path:
        """
        Dosyayı decompress etmeyi dene
        
        Args:
            file_path: Dosya yolu
        
        Returns:
            Decompress edilmiş dosya yolu (veya orijinal)
        """
        try:
            # Dosyayı oku
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Zaten text mi kontrol et
            try:
                data.decode('utf-8')
                logger.info(f"   Dosya zaten text formatında")
                return file_path
            except UnicodeDecodeError:
                pass
            
            # GZIP mi kontrol et
            if data[:2] == b'\x1f\x8b':
                logger.info(f"   GZIP sıkıştırması tespit edildi, açılıyor...")
                try:
                    decompressed = gzip.decompress(data)
                    with open(file_path, 'wb') as f:
                        f.write(decompressed)
                    logger.info(f"   ✅ GZIP açıldı")
                    return file_path
                except Exception as e:
                    logger.warning(f"   GZIP açma hatası: {e}")
            
            # ZLIB mi kontrol et
            if data[:2] == b'\x78\x9c' or data[:2] == b'\x78\x01':
                logger.info(f"   ZLIB sıkıştırması tespit edildi, açılıyor...")
                try:
                    decompressed = zlib.decompress(data)
                    with open(file_path, 'wb') as f:
                        f.write(decompressed)
                    logger.info(f"   ✅ ZLIB açıldı")
                    return file_path
                except Exception as e:
                    logger.warning(f"   ZLIB açma hatası: {e}")
            
            # ZIP header mı kontrol et
            if data[:2] == b'PK':
                logger.info(f"   ZIP dosyası tespit edildi")
                # ZIP olarak işlenecek, dokunma
                return file_path
            
            # Genel zlib deneme
            logger.info(f"   Genel decompress deneniyor...")
            try:
                decompressed = zlib.decompress(data, -zlib.MAX_WBITS)
                with open(file_path, 'wb') as f:
                    f.write(decompressed)
                logger.info(f"   ✅ Decompress başarılı")
                return file_path
            except:
                pass
            
            # Hiçbiri çalışmadı, orijinal dosyayı döndür
            logger.warning(f"   ⚠️  Dosya decompress edilemedi, orijinal kullanılacak")
            return file_path
        
        except Exception as e:
            logger.error(f"   Decompress hatası: {e}")
            return file_path
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Dosya adını temizle (Windows için)
        
        Args:
            filename: Dosya adı
        
        Returns:
            Temizlenmiş dosya adı
        """
        # Geçersiz karakterleri değiştir
        invalid_chars = '<>:"/\\|?*\n\r\t'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Invisible characters
        filename = filename.replace('\u200e', '')  # Left-to-right mark
        filename = filename.replace('\u200f', '')  # Right-to-left mark
        
        # Başındaki/sonundaki boşlukları kaldır
        filename = filename.strip()
        
        # Çift boşlukları tek yap
        while '  ' in filename:
            filename = filename.replace('  ', ' ')
        
        return filename
    
    def _extract_zip(self, zip_path: Path, output_dir: Path) -> List[str]:
        """
        ZIP dosyasını aç
        
        Args:
            zip_path: ZIP dosya yolu
            output_dir: Çıktı dizini
        
        Returns:
            Çıkarılan .txt dosya yolları
        """
        try:
            logger.info(f"ZIP açılıyor: {zip_path.name}")
            
            extracted_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Sadece .txt dosyalarını çıkar
                txt_files = [f for f in zip_ref.namelist() if f.endswith('.txt')]
                
                for txt_file in txt_files:
                    # Çıkar
                    zip_ref.extract(txt_file, output_dir)
                    extracted_path = output_dir / txt_file
                    extracted_files.append(str(extracted_path))
                    logger.info(f"   ✅ Çıkarıldı: {txt_file}")
            
            # ZIP'i sil
            zip_path.unlink()
            logger.info(f"   🗑️  ZIP silindi: {zip_path.name}")
            
            return extracted_files
        
        except Exception as e:
            logger.error(f"ZIP açma hatası: {e}")
            return []
    
    def sync_and_process(self, output_dir: Path) -> List[str]:
        """
        Drive'dan dosyaları çek ve işle
        
        Args:
            output_dir: Çıktı dizini
        
        Returns:
            İndirilen/çıkarılan dosya yolları
        """
        try:
            # Tüm dosyaları listele (klasör hariç)
            files = self.list_files()
            
            if not files:
                logger.info("Drive'da yeni dosya yok")
                return []
            
            logger.info(f"📦 {len(files)} dosya bulundu, indiriliyor...")
            
            all_extracted_files = []
            
            for i, file_info in enumerate(files, 1):
                file_id = file_info['id']
                file_name = file_info['name']
                
                logger.info(f"\n[{i}/{len(files)}] İşleniyor: {file_name[:60]}...")
                
                # İndir (ZIP ise otomatik aç)
                extracted_files = self.download_file(file_id, file_name, output_dir)
                
                if extracted_files:
                    all_extracted_files.extend(extracted_files)
                    logger.info(f"   ✅ Hazır: {len(extracted_files)} dosya")
                else:
                    logger.warning(f"   ⚠️  İndirilemedi: {file_name[:60]}")
            
            if all_extracted_files:
                logger.info(f"\n🎉 Tamamlandı! {len(all_extracted_files)} dosya hazır")
                logger.info(f"💡 Drive'dan manuel silin: {self.folder_name}")
            
            return all_extracted_files
        
        except Exception as e:
            logger.error(f"Senkronizasyon hatası: {e}")
            return []


def auto_sync_from_drive(service_account_file: str, 
                        output_dir: Path,
                        folder_name: str = "PEN_WhatsApp_Exports") -> List[str]:
    """
    Drive'dan otomatik senkronizasyon
    
    Args:
        service_account_file: Service account JSON dosyası
        output_dir: Çıktı dizini
        folder_name: Drive klasör adı
    
    Returns:
        İndirilen dosya yolları
    """
    sync = DriveSync(service_account_file, folder_name)
    
    if not sync.connect():
        return []
    
    return sync.sync_and_process(output_dir)
