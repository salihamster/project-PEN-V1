"""Document Manager for PEN WorkSpace.

Handles file operations in the data/user_docs directory.
Provides safe access to user documents (txt, md, etc.).
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime

class DocumentManager:
    def __init__(self, base_dir: Union[str, Path]):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure standard subdirectories exist
        (self.base_dir / "uploads").mkdir(exist_ok=True)
        (self.base_dir / "daily_plans").mkdir(exist_ok=True)
        (self.base_dir / "notes").mkdir(exist_ok=True)
        (self.base_dir / "projects").mkdir(exist_ok=True)

    def _get_safe_path(self, relative_path: str) -> Path:
        """Resolve path and ensure it's inside base_dir to prevent directory traversal."""
        # Remove potential leading slashes or dots
        clean_path = relative_path.lstrip("/\\").replace("..", "")
        full_path = (self.base_dir / clean_path).resolve()
        
        if not str(full_path).startswith(str(self.base_dir.resolve())):
            raise ValueError(f"Access denied: {relative_path} is outside safe directory.")
            
        return full_path

    def list_documents(self, subdir: str = "") -> List[Dict[str, str]]:
        """List files in a subdirectory."""
        target_dir = self._get_safe_path(subdir)
        if not target_dir.exists():
            return []
            
        files = []
        for p in target_dir.rglob("*"):
            if p.is_file() and not p.name.startswith("."):
                rel_path = p.relative_to(self.base_dir).as_posix()
                files.append({
                    "name": p.name,
                    "path": rel_path,
                    "type": p.suffix.lower(),
                    "size": p.stat().st_size,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                })
        return sorted(files, key=lambda x: x["modified"], reverse=True)

    def read_document(self, path: str) -> str:
        """Read text content of a document."""
        target_path = self._get_safe_path(path)
        if not target_path.exists():
            raise FileNotFoundError(f"Document not found: {path}")
            
        try:
            return target_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def create_document(self, path: str, content: str) -> str:
        """Create a new document or overwrite existing."""
        target_path = self._get_safe_path(path)
        
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        target_path.write_text(content, encoding="utf-8")
        return str(target_path.relative_to(self.base_dir).as_posix())

    def append_document(self, path: str, content: str) -> str:
        """Append text to an existing document."""
        target_path = self._get_safe_path(path)
        if not target_path.exists():
            return self.create_document(path, content)
            
        with open(target_path, "a", encoding="utf-8") as f:
            f.write("\n" + content)
            
        return str(target_path.relative_to(self.base_dir).as_posix())

    def delete_document(self, path: str) -> bool:
        """Delete a document."""
        target_path = self._get_safe_path(path)
        if target_path.exists() and target_path.is_file():
            target_path.unlink()
            return True
        return False
