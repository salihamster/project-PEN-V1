"""
Google Drive synchronization module
Manual upload -> Automatic download -> Automatic cleanup
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
    """Google Drive synchronization"""
    
    def __init__(self, service_account_file: str, folder_name: str = "PEN_WhatsApp_Exports"):
        """
        Initialize DriveSync
        
        Args:
            service_account_file: Service account JSON file
            folder_name: Folder name in Drive
        """
        self.service_account_file = service_account_file
        self.folder_name = folder_name
        self.service = None
        self.folder_id = None
    
    def connect(self) -> bool:
        """
        Connect to Google Drive
        
        Returns:
            True if successful
        """
        try:
            logger.info("Connecting to Google Drive...")
            
            # Service account authentication
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            # Drive API service
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Find or create folder
            self.folder_id = self._get_or_create_folder()
            
            logger.info(f"Google Drive connection successful")
            logger.info(f"   Folder: {self.folder_name}")
            return True
        
        except Exception as e:
            logger.error(f"Google Drive connection error: {e}")
            return False
    
    def _get_or_create_folder(self) -> str:
        """
        Find or create folder
        
        Returns:
            Folder ID
        """
        try:
            # Search for folder
            query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime)',
                orderBy='createdTime asc'  # Get oldest folder (first created)
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                # If multiple folders, check file count in each
                if len(files) > 1:
                    logger.warning(f"Found {len(files)} folders named '{self.folder_name}'!")
                    
                    # Check file count in each folder
                    best_folder = None
                    max_files = -1
                    
                    for folder in files:
                        folder_id = folder['id']
                        # Check file count in this folder
                        file_query = f"'{folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
                        file_results = self.service.files().list(
                            q=file_query,
                            spaces='drive',
                            fields='files(id)',
                            pageSize=1000
                        ).execute()
                        
                        file_count = len(file_results.get('files', []))
                        logger.info(f"   Folder ID {folder_id}: {file_count} files (created: {folder.get('createdTime', 'N/A')})")
                        
                        if file_count > max_files:
                            max_files = file_count
                            best_folder = folder
                    
                    if best_folder and max_files > 0:
                        folder_id = best_folder['id']
                        logger.info(f"Selected folder with most files: {max_files} files")
                    else:
                        # If all empty, use oldest
                        folder_id = files[0]['id']
                        logger.info(f"All folders empty, using oldest")
                else:
                    # Single folder
                    folder_id = files[0]['id']
                    logger.info(f"Folder found: {self.folder_name}")
                
                return folder_id
            else:
                # Folder doesn't exist, create it
                logger.info(f"Creating folder: {self.folder_name}")
                file_metadata = {
                    'name': self.folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                
                folder_id = folder.get('id')
                logger.info(f"Folder created: {self.folder_name}")
                return folder_id
        
        except Exception as e:
            logger.error(f"Folder operation error: {e}")
            raise
    
    def list_files(self, file_extensions: List[str] = None) -> List[Dict]:
        """
        List files in Drive
        
        Args:
            file_extensions: File extensions (None = all)
        
        Returns:
            File list
        """
        try:
            logger.info(f"Listing files in Drive...")
            logger.info(f"Folder ID: {self.folder_id}")
            logger.info(f"Folder name: {self.folder_name}")
            
            # Search for files in folder (excluding folders)
            query = f"'{self.folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
            
            # Extension filter (optional)
            if file_extensions:
                ext_queries = [f"name contains '{ext}'" for ext in file_extensions]
                query += f" and ({' or '.join(ext_queries)})"
            
            logger.info(f"Query: {query}")
            
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, createdTime, size, mimeType)',
                orderBy='createdTime desc'
            ).execute()
            
            files = results.get('files', [])
            
            logger.info(f"{len(files)} files found")
            
            # Check all Drive files (for debugging)
            logger.info("Checking all Drive files...")
            all_query = "trashed=false"
            all_results = self.service.files().list(
                q=all_query,
                spaces='drive',
                fields='files(id, name, mimeType, parents)',
                pageSize=100
            ).execute()
            
            all_files = all_results.get('files', [])
            logger.info(f"Total {len(all_files)} files/folders in Drive")
            
            # List folders
            folders = [f for f in all_files if f.get('mimeType') == 'application/vnd.google-apps.folder']
            logger.info(f"Folders ({len(folders)}):")
            for folder in folders:
                logger.info(f"  - {folder['name']} (ID: {folder['id']})")
            
            # List files
            non_folders = [f for f in all_files if f.get('mimeType') != 'application/vnd.google-apps.folder']
            logger.info(f"Files ({len(non_folders)}):")
            for file in non_folders[:20]:  # First 20 files
                parent_info = f" (parent: {file.get('parents', ['root'])[0]})" if 'parents' in file else " (root)"
                logger.info(f"  - {file['name']}{parent_info}")
            
            return files
        
        except Exception as e:
            logger.error(f"File listing error: {e}")
            return []
    
    def download_file(self, file_id: str, file_name: str, output_dir: Path) -> List[str]:
        """
        Download file (extract if ZIP)
        
        Args:
            file_id: Drive file ID
            file_name: File name
            output_dir: Output directory
        
        Returns:
            Downloaded/extracted file paths
        """
        try:
            logger.info(f"📥 Downloading: {file_name[:50]}...")
            
            # Download file
            request = self.service.files().get_media(fileId=file_id)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean file name (for Windows)
            safe_name = self._sanitize_filename(file_name)
            
            # Add .txt extension if missing
            if not safe_name.endswith('.txt') and not safe_name.endswith('.zip'):
                safe_name += '.txt'
            
            # Temporary file
            temp_path = output_dir / safe_name
            
            with io.FileIO(str(temp_path), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                last_progress = 0
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        # Log every 10%
                        if progress >= last_progress + 10:
                            logger.info(f"   Progress: %{progress}")
                            last_progress = progress
            
            logger.info(f"✅ Downloaded: {safe_name[:50]}...")
            
            # Check if file is ZIP by reading header
            with open(temp_path, 'rb') as f:
                header = f.read(4)
            
            # ZIP header? (PK\x03\x04)
            if header[:2] == b'PK':
                logger.info(f"   ZIP file detected (header check)")
                return self._extract_zip(temp_path, output_dir)
            
            # If not ZIP, try decompress
            decompressed_path = self._try_decompress(temp_path)
            return [str(decompressed_path)]
        
        except Exception as e:
            logger.error(f"File download error: {e}")
            return []
    
    def _try_decompress(self, file_path: Path) -> Path:
        """
        Try to decompress file
        
        Args:
            file_path: File path
        
        Returns:
            Decompressed file path (or original)
        """
        try:
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check if already text
            try:
                data.decode('utf-8')
                logger.info(f"   File already in text format")
                return file_path
            except UnicodeDecodeError:
                pass
            
            # Check for GZIP
            if data[:2] == b'\x1f\x8b':
                logger.info(f"   GZIP compression detected, extracting...")
                try:
                    decompressed = gzip.decompress(data)
                    with open(file_path, 'wb') as f:
                        f.write(decompressed)
                    logger.info(f"   ✅ GZIP extracted")
                    return file_path
                except Exception as e:
                    logger.warning(f"   GZIP extraction error: {e}")
            
            # Check for ZLIB
            if data[:2] == b'\x78\x9c' or data[:2] == b'\x78\x01':
                logger.info(f"   ZLIB compression detected, extracting...")
                try:
                    decompressed = zlib.decompress(data)
                    with open(file_path, 'wb') as f:
                        f.write(decompressed)
                    logger.info(f"   ✅ ZLIB extracted")
                    return file_path
                except Exception as e:
                    logger.warning(f"   ZLIB extraction error: {e}")
            
            # Check for ZIP header
            if data[:2] == b'PK':
                logger.info(f"   ZIP file detected")
                # Will be processed as ZIP, don't touch
                return file_path
            
            # Try generic zlib
            logger.info(f"   Trying generic decompress...")
            try:
                decompressed = zlib.decompress(data, -zlib.MAX_WBITS)
                with open(file_path, 'wb') as f:
                    f.write(decompressed)
                logger.info(f"   ✅ Decompress successful")
                return file_path
            except:
                pass
            
            # Nothing worked, return original file
            logger.warning(f"   ⚠️  File could not be decompressed, using original")
            return file_path
        
        except Exception as e:
            logger.error(f"   Decompress error: {e}")
            return file_path
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Clean file name (for Windows)
        
        Args:
            filename: File name
        
        Returns:
            Cleaned file name
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*\n\r\t'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Invisible characters
        filename = filename.replace('\u200e', '')  # Left-to-right mark
        filename = filename.replace('\u200f', '')  # Right-to-left mark
        
        # Remove leading/trailing spaces
        filename = filename.strip()
        
        # Replace double spaces with single
        while '  ' in filename:
            filename = filename.replace('  ', ' ')
        
        return filename
    
    def _extract_zip(self, zip_path: Path, output_dir: Path) -> List[str]:
        """
        Extract ZIP file
        
        Args:
            zip_path: ZIP file path
            output_dir: Output directory
        
        Returns:
            Extracted .txt file paths
        """
        try:
            logger.info(f"Extracting ZIP: {zip_path.name}")
            
            extracted_files = []
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract only .txt files
                txt_files = [f for f in zip_ref.namelist() if f.endswith('.txt')]
                
                for txt_file in txt_files:
                    # Extract
                    zip_ref.extract(txt_file, output_dir)
                    extracted_path = output_dir / txt_file
                    extracted_files.append(str(extracted_path))
                    logger.info(f"   ✅ Extracted: {txt_file}")
            
            # Delete ZIP
            zip_path.unlink()
            logger.info(f"   🗑️  ZIP deleted: {zip_path.name}")
            
            return extracted_files
        
        except Exception as e:
            logger.error(f"ZIP extraction error: {e}")
            return []
    
    def sync_and_process(self, output_dir: Path) -> List[str]:
        """
        Fetch and process files from Drive
        
        Args:
            output_dir: Output directory
        
        Returns:
            Downloaded/extracted file paths
        """
        try:
            # List all files (excluding folders)
            files = self.list_files()
            
            if not files:
                logger.info("No new files in Drive")
                return []
            
            logger.info(f"📦 {len(files)} files found, downloading...")
            
            all_extracted_files = []
            
            for i, file_info in enumerate(files, 1):
                file_id = file_info['id']
                file_name = file_info['name']
                
                logger.info(f"\n[{i}/{len(files)}] Processing: {file_name[:60]}...")
                
                # Download (auto-extract if ZIP)
                extracted_files = self.download_file(file_id, file_name, output_dir)
                
                if extracted_files:
                    all_extracted_files.extend(extracted_files)
                    logger.info(f"   ✅ Ready: {len(extracted_files)} files")
                else:
                    logger.warning(f"   ⚠️  Failed to download: {file_name[:60]}")
            
            if all_extracted_files:
                logger.info(f"\n🎉 Complete! {len(all_extracted_files)} files ready")
                logger.info(f"💡 Manually delete from Drive: {self.folder_name}")
            
            return all_extracted_files
        
        except Exception as e:
            logger.error(f"Synchronization error: {e}")
            return []


def auto_sync_from_drive(service_account_file: str, 
                        output_dir: Path,
                        folder_name: str = "PEN_WhatsApp_Exports") -> List[str]:
    """
    Automatic synchronization from Drive
    
    Args:
        service_account_file: Service account JSON file
        output_dir: Output directory
        folder_name: Drive folder name
    
    Returns:
        Downloaded file paths
    """
    sync = DriveSync(service_account_file, folder_name)
    
    if not sync.connect():
        return []
    
    return sync.sync_and_process(output_dir)
