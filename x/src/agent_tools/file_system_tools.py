"""File System Tools for PEN Agent.

Provides safe access to file operations within the allowed directory (data/user_docs).
Wraps DocumentManager functionality and adds specific requested tools.
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from src.storage.document_manager import DocumentManager

class FileSystemTools:
    def __init__(self, document_manager: DocumentManager):
        self.doc_manager = document_manager
        self.base_dir = self.doc_manager.base_dir

    def _get_safe_path(self, path: str) -> Path:
        """Resolve path using DocumentManager's safety check."""
        # This will raise ValueError if path is unsafe
        return self.doc_manager._get_safe_path(path)

    def read_file(self, path: str) -> str:
        """Read and return the full contents of a text file."""
        try:
            return self.doc_manager.read_document(path)
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_to_file(self, path: str, content: str) -> str:
        """Write content to a file. Creates/Overwrites."""
        try:
            rel_path = self.doc_manager.create_document(path, content)
            return f"Successfully wrote to {rel_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def replace_in_file(self, path: str, diff: str) -> str:
        """
        Modify a file using a structured multi-block diff string.
        Format:
        <<<<<<< SEARCH
        original text
        =======
        new text
        >>>>>>> REPLACE
        """
        try:
            current_content = self.read_file(path)
            if current_content.startswith("Error"):
                return current_content
            
            # Improved block replacement parser with better error handling
            blocks = re.split(r'<<<<<<< SEARCH\s*\n', diff)
            new_content = current_content
            changes_count = 0
            failed_blocks = []
            
            for block_idx, block in enumerate(blocks[1:], 1):
                try:
                    if '\n=======\n' not in block:
                        failed_blocks.append(f"Block {block_idx}: Missing separator '======='")
                        continue
                    
                    parts = block.split('\n=======\n', 1)
                    search_block = parts[0]
                    
                    if '\n>>>>>>> REPLACE' not in parts[1]:
                        failed_blocks.append(f"Block {block_idx}: Missing end marker '>>>>>>> REPLACE'")
                        continue
                    
                    replace_block = parts[1].split('\n>>>>>>> REPLACE')[0]
                    
                    if search_block in new_content:
                        new_content = new_content.replace(search_block, replace_block, 1)
                        changes_count += 1
                    else:
                        search_preview = search_block[:100] + "..." if len(search_block) > 100 else search_block
                        failed_blocks.append(f"Block {block_idx}: Search text not found\nSearching for: {search_preview}")
                        
                except Exception as e:
                    failed_blocks.append(f"Block {block_idx}: Parse error - {str(e)}")

            if changes_count > 0:
                self.write_to_file(path, new_content)
                result = f"Successfully applied {changes_count} change(s) to {path}"
                if failed_blocks:
                    result += f"\n\nWarnings:\n" + "\n".join(failed_blocks)
                return result
            else:
                if failed_blocks:
                    return "No changes applied. Errors:\n" + "\n".join(failed_blocks)
                else:
                    return "No changes applied (no valid blocks found)."

        except Exception as e:
            return f"Error replacing in file: {str(e)}"

    def search_files(self, pattern: str, glob_pattern: str = "**/*") -> str:
        """Search for a regex or string pattern across file contents."""
        try:
            # Validate glob pattern for security (prevent path traversal)
            if ".." in glob_pattern or glob_pattern.startswith("/"):
                return "Error: Invalid glob pattern (path traversal detected)"
            
            results = []
            # Use rglob for recursive search, limited to base_dir
            files = list(self.base_dir.rglob(glob_pattern.lstrip("**/")))
            
            # Limit number of files to search (prevent DoS)
            max_files = 1000
            if len(files) > max_files:
                files = files[:max_files]
                results.append(f"[Warning: Limited to first {max_files} files]")
            
            for file_path in files:
                # Security check: ensure file is within base_dir
                try:
                    file_path.relative_to(self.base_dir)
                except ValueError:
                    continue  # Skip files outside base_dir
                
                if file_path.is_file():
                    try:
                        # Limit file size to prevent memory issues
                        if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                            continue
                        
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if re.search(pattern, content):
                            # Find matching lines
                            lines = content.splitlines()
                            for i, line in enumerate(lines):
                                if re.search(pattern, line):
                                    rel_path = file_path.relative_to(self.base_dir)
                                    results.append(f"{rel_path}:{i+1}: {line.strip()}")
                                    # Limit results per file
                                    if len(results) >= 100:
                                        break
                            if len(results) >= 100:
                                break
                    except Exception:
                        continue
            
            if not results or (len(results) == 1 and results[0].startswith("[Warning")):
                return "No matches found."
            return "\n".join(results[:100]) # Limit total results
        except Exception as e:
            return f"Error searching files: {str(e)}"

    def get_file_info(self, path: str) -> str:
        """Retrieve metadata about a file or directory."""
        try:
            target_path = self._get_safe_path(path)
            if not target_path.exists():
                return f"Path not found: {path}"
            
            stat = target_path.stat()
            info = {
                "name": target_path.name,
                "type": "directory" if target_path.is_dir() else "file",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(target_path.relative_to(self.base_dir))
            }
            return str(info)
        except Exception as e:
            return f"Error getting info: {str(e)}"

    def list_files(self, path: str = "") -> str:
        """List all files and directories in the specified path."""
        try:
            files = self.doc_manager.list_documents(path)
            if not files:
                return "Directory is empty or not found."
            
            output = []
            for f in files:
                output.append(f"{f['name']} ({f['size']} bytes) - {f['modified']}")
            return "\n".join(output)
        except Exception as e:
            return f"Error listing files: {str(e)}"
