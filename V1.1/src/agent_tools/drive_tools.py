"""
Google Drive access tools for Agent
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
    """Google Drive tools for Agent"""
    
    def __init__(self, service_account_file: str, folder_name: str = "Wpmesages"):
        """
        Initialize DriveTools
        
        Args:
            service_account_file: Service account JSON file
            folder_name: Folder name in Drive
        """
        self.service_account_file = service_account_file
        self.folder_name = folder_name
        self.service = None
        self.folder_id = None
        self._connect()
    
    def _connect(self) -> bool:
        """Connect to Google Drive"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            
            # Find folder
            query = f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                self.folder_id = files[0]['id']
                logger.info(f"Agent: Drive connection successful ({self.folder_name})")
                return True
            else:
                logger.warning(f"Agent: Drive folder not found ({self.folder_name})")
                return False
        
        except Exception as e:
            logger.error(f"Agent: Drive connection error: {e}")
            return False
    
    def list_files(self, file_type: Optional[str] = None, limit: int = 100) -> str:
        """
        List files in Drive
        
        Args:
            file_type: File type filter (txt, pdf, zip, etc.)
            limit: Maximum file count
        
        Returns:
            File list in JSON format
        """
        try:
            if not self.service or not self.folder_id:
                return json.dumps({
                    "status": "error",
                    "message": "No Drive connection"
                })
            
            # Search files in folder
            query = f"'{self.folder_id}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
            
            # File type filter
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
            
            # Format file information
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
            
            logger.info(f"Agent: {len(file_list)} files listed (Drive)")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Agent tool error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def download_file(self, file_id: str, output_path: str) -> str:
        """
        Download file from Drive
        
        Args:
            file_id: Drive file ID
            output_path: Output file path
        
        Returns:
            Result in JSON format
        """
        try:
            if not self.service:
                return json.dumps({
                    "status": "error",
                    "message": "No Drive connection"
                })
            
            # Get file info
            file_info = self.service.files().get(fileId=file_id, fields='name,size').execute()
            file_name = file_info['name']
            file_size = int(file_info.get('size', 0))
            
            # Download file
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
                "message": f"File downloaded: {file_name}"
            }
            
            logger.info(f"Agent: File downloaded - {file_name}")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Agent tool error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def download_file_by_name(self, file_name: str, output_dir: str) -> str:
        """
        Download file from Drive by name
        
        Args:
            file_name: File name
            output_dir: Output directory
        
        Returns:
            Result in JSON format
        """
        try:
            if not self.service or not self.folder_id:
                return json.dumps({
                    "status": "error",
                    "message": "No Drive connection"
                })
            
            # Search for file
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
                    "message": f"File not found: {file_name}"
                })
            
            # Download first matching file
            file_id = files[0]['id']
            output_path = str(Path(output_dir) / file_name)
            
            return self.download_file(file_id, output_path)
        
        except Exception as e:
            logger.error(f"Agent tool error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def search_files(self, query: str, limit: int = 20) -> str:
        """
        Search files in Drive
        
        Args:
            query: Search query (in file name)
            limit: Maximum result count
        
        Returns:
            Search results in JSON format
        """
        try:
            if not self.service or not self.folder_id:
                return json.dumps({
                    "status": "error",
                    "message": "No Drive connection"
                })
            
            # Search in file name
            search_query = f"'{self.folder_id}' in parents and name contains '{query}' and trashed=false"
            results = self.service.files().list(
                q=search_query,
                spaces='drive',
                fields='files(id, name, createdTime, modifiedTime, size)',
                orderBy='modifiedTime desc',
                pageSize=limit
            ).execute()
            
            files = results.get('files', [])
            
            # Format file information
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
            
            logger.info(f"Agent: {len(file_list)} files found for '{query}' (Drive)")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Agent tool error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def get_file_info(self, file_id: str) -> str:
        """
        Get file information
        
        Args:
            file_id: Drive file ID
        
        Returns:
            File information in JSON format
        """
        try:
            if not self.service:
                return json.dumps({
                    "status": "error",
                    "message": "No Drive connection"
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
            
            logger.info(f"Agent: File info retrieved - {file_info['name']}")
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"Agent tool error: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })


def get_drive_tools_description() -> str:
    """
    Return description of Drive tools
    
    Returns:
        Tool descriptions
    """
    return """
# Agent Google Drive Tools

## 1. list_files(file_type=None, limit=100)
List files in Drive.

**Parameters**:
- file_type: File type filter (txt, pdf, zip)
- limit: Maximum file count (default: 100)

**Example**:
```python
drive_tools.list_files(file_type="txt", limit=50)
```

## 2. download_file(file_id, output_path)
Download file from Drive (by ID).

**Parameters**:
- file_id: Drive file ID (required)
- output_path: Output file path (required)

**Example**:
```python
drive_tools.download_file("abc123", "downloads/file.txt")
```

## 3. download_file_by_name(file_name, output_dir)
Download file from Drive (by name).

**Parameters**:
- file_name: File name (required)
- output_dir: Output directory (required)

**Example**:
```python
drive_tools.download_file_by_name("chat.txt", "downloads/")
```

## 4. search_files(query, limit=20)
Search files in Drive.

**Parameters**:
- query: Search query (required)
- limit: Maximum result count (default: 20)

**Example**:
```python
drive_tools.search_files("WhatsApp", limit=10)
```

## 5. get_file_info(file_id)
Get file information.

**Parameters**:
- file_id: Drive file ID (required)

**Example**:
```python
drive_tools.get_file_info("abc123")
```
"""
