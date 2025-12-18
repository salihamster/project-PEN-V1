"""
Email message parsing module
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
from threading import Lock, Semaphore
import queue

from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmailParser:
    """Fetches and parses email messages via IMAP"""
    
    def __init__(self, email_address: str, password: str, 
                 imap_server: str = "imap.gmail.com", imap_port: int = 993,
                 max_workers: int = 5):
        """
        Initialize EmailParser
        
        Args:
            email_address: Email address
            password: Email password (app password)
            imap_server: IMAP server address
            imap_port: IMAP port number
            max_workers: Parallel workers count (default: 5)
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
        Connect to IMAP server
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Connecting to IMAP server: {self.imap_server}")
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=30)
            self.mail.login(self.email_address, self.password)
            logger.info("IMAP connection successful")
            return True
        except Exception as e:
            logger.error(f"IMAP connection error: {e}")
            return False
    
    def disconnect(self):
        """Close IMAP connection"""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
                logger.info("IMAP connection closed")
            except:
                pass
    
    def fetch_emails(self, folder: str = 'INBOX', limit: Optional[int] = None, 
                    parallel: bool = True) -> List[Dict]:
        """
        Fetch emails (parallel or serial)
        
        Args:
            folder: Email folder (INBOX, Sent, etc.)
            limit: Maximum email count (None = all)
            parallel: Use parallel processing (default: True)
        
        Returns:
            List of parsed emails
        """
        if not self.mail:
            logger.error("No IMAP connection. Call connect() first.")
            return []
        
        try:
            logger.info(f"Fetching emails from {folder}...")
            self.mail.select(folder)
            
            status, messages = self.mail.search(None, 'ALL')
            email_ids = messages[0].split()
            
            # If limit, get last 'limit' emails
            if limit:
                email_ids = email_ids[-limit:]
            
            total = len(email_ids)
            logger.info(f"{total} emails found, processing...")
            
            if parallel and total > 10:
                logger.info(f"Using parallel processing ({self.max_workers} threads)")
                return self._fetch_emails_parallel(email_ids)
            else:
                logger.info("Using serial processing")
                return self._fetch_emails_serial(email_ids)
        
        except Exception as e:
            logger.error(f"Email fetch error: {e}")
            return []
    
    def fetch_emails_with_search(self, search_criteria: str, 
                                 limit: Optional[int] = None,
                                 parallel: bool = True) -> List[Dict]:
        """
        Fetch emails by specific criteria
        
        Args:
            search_criteria: IMAP search criteria (e.g., 'FROM "penelope@ac.com"')
            limit: Maximum email count (None = all)
            parallel: Use parallel processing (default: True)
        
        Returns:
            List of parsed emails
        
        Example search criteria:
            - 'FROM "user@example.com"'
            - 'SUBJECT "meeting"'
            - 'SINCE "01-Jan-2024"'
            - 'FROM "user@example.com" SINCE "01-Jan-2024"'
        """
        if not self.mail:
            logger.error("No IMAP connection. Call connect() first.")
            return []
        
        try:
            logger.info(f"Searching emails: {search_criteria}")
            self.mail.select('INBOX')
            
            # IMAP search
            status, messages = self.mail.search(None, search_criteria)
            email_ids = messages[0].split()
            
            if not email_ids:
                logger.info("No emails found matching criteria")
                return []
            
            # If limit, get last 'limit' emails
            if limit:
                email_ids = email_ids[-limit:]
            
            total = len(email_ids)
            logger.info(f"{total} emails found, processing...")
            
            if parallel and total > 10:
                logger.info(f"Using parallel processing ({self.max_workers} threads)")
                return self._fetch_emails_parallel(email_ids)
            else:
                logger.info("Using serial processing")
                return self._fetch_emails_serial(email_ids)
        
        except Exception as e:
            logger.error(f"Email search error: {e}")
            return []
    
    def _fetch_emails_serial(self, email_ids: List[bytes]) -> List[Dict]:
        """
        Fetch emails serially (legacy method)
        
        Args:
            email_ids: List of email IDs
        
        Returns:
            List of parsed emails
        """
        self.emails = []
        total = len(email_ids)
        
        for idx, email_id in enumerate(email_ids, 1):
            try:
                status, msg_data = self.mail.fetch(email_id, '(RFC822)')
                msg = Parser().parsestr(msg_data[0][1].decode('utf-8', errors='ignore'))
                
                email_obj = self._parse_email_message(msg)
                self.emails.append(email_obj)
                
                # Show progress
                if idx % 50 == 0 or idx == total:
                    percent = (idx * 100) // total
                    logger.info(f"Processing: {idx}/{total} ({percent}%)")
            
            except Exception as e:
                logger.warning(f"Email parse error (ID: {email_id}): {str(e)[:50]}")
                continue
        
        logger.info(f"{len(self.emails)} emails fetched")
        return self.emails
    
    def _fetch_emails_parallel(self, email_ids: List[bytes]) -> List[Dict]:
        """
        Fetch emails in parallel (fast with connection pool)
        
        Args:
            email_ids: List of email IDs
        
        Returns:
            List of parsed emails
        """
        self.emails = []
        total = len(email_ids)
        processed = 0
        
        # Create connection pool (max_workers connections)
        connection_pool = queue.Queue(maxsize=self.max_workers)
        for _ in range(self.max_workers):
            try:
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=10)
                mail.login(self.email_address, self.password)
                mail.select('INBOX')
                connection_pool.put(mail)
            except Exception as e:
                logger.warning(f"Connection pool creation error: {e}")
        
        # Parallel processing with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_id = {
                executor.submit(self._fetch_single_email_pooled, email_id, connection_pool): email_id 
                for email_id in email_ids
            }
            
            # Collect results
            for future in as_completed(future_to_id):
                email_id = future_to_id[future]
                try:
                    email_obj = future.result()
                    if email_obj:
                        with self.emails_lock:
                            self.emails.append(email_obj)
                    
                    processed += 1
                    
                    # Show progress
                    if processed % 50 == 0 or processed == total:
                        percent = (processed * 100) // total
                        logger.info(f"Processing: {processed}/{total} ({percent}%)")
                
                except Exception as e:
                    logger.warning(f"Email parse error: {str(e)[:50]}")
                    processed += 1
        
        # Close connections
        while not connection_pool.empty():
            try:
                mail = connection_pool.get_nowait()
                mail.close()
                mail.logout()
            except:
                pass
        
        logger.info(f"{len(self.emails)} emails fetched (parallel, connection pool)")
        return self.emails
    
    def _fetch_single_email_pooled(self, email_id: bytes, connection_pool: queue.Queue) -> Optional[Dict]:
        """
        Fetch a single email (from connection pool)
        
        Args:
            email_id: Email ID
            connection_pool: Connection pool
        
        Returns:
            Parsed email object or None
        """
        mail = None
        try:
            # Get connection from pool
            mail = connection_pool.get(timeout=30)
            
            # Fetch email
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            msg = Parser().parsestr(msg_data[0][1].decode('utf-8', errors='ignore'))
            
            # Parse
            email_obj = self._parse_email_message(msg)
            
            return email_obj
        
        except Exception as e:
            logger.debug(f"Email fetch error (ID: {email_id}): {str(e)[:50]}")
            return None
        
        finally:
            # Return connection to pool
            if mail:
                try:
                    connection_pool.put(mail, timeout=5)
                except:
                    try:
                        mail.close()
                        mail.logout()
                    except:
                        pass
    
    def _fetch_single_email(self, email_id: bytes) -> Optional[Dict]:
        """
        Fetch a single email (legacy method - not used)
        
        Args:
            email_id: Email ID
        
        Returns:
            Parsed email object or None
        """
        try:
            # Create new IMAP connection for each thread
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=30)
            mail.login(self.email_address, self.password)
            mail.select('INBOX')
            
            # Fetch email
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            msg = Parser().parsestr(msg_data[0][1].decode('utf-8', errors='ignore'))
            
            # Parse
            email_obj = self._parse_email_message(msg)
            
            # Close connection
            mail.close()
            mail.logout()
            
            return email_obj
        
        except Exception as e:
            logger.debug(f"Email fetch error (ID: {email_id}): {str(e)[:50]}")
            return None
    
    def _decode_header_value(self, value: Optional[str]) -> str:
        """Decode MIME-encoded header to a readable Unicode string."""
        try:
            return str(make_header(decode_header(value or "")))
        except Exception:
            return value or ""

    def _parse_email_message(self, msg) -> Dict:
        """
        Parse email message object
        
        Args:
            msg: Email message object
        
        Returns:
            Parsed email object
        """
        # Parse timestamp
        try:
            timestamp = parsedate_to_datetime(msg['Date']).isoformat()
        except:
            timestamp = datetime.now().isoformat()
        
        # Decode headers to store readable text
        msg_id = msg.get('Message-ID', '')
        from_decoded = self._decode_header_value(msg.get('From', ''))
        to_decoded = self._decode_header_value(msg.get('To', ''))
        subject_decoded = self._decode_header_value(msg.get('Subject', ''))
        
        body_text, body_html = self._get_email_body(msg)
        
        return {
            'id': msg_id,
            'from': from_decoded,
            'to': to_decoded,
            'subject': subject_decoded,
            'body': body_text,
            'html_body': body_html,
            'timestamp': timestamp,
            'source': 'email',
            'is_spam': self._is_spam(msg)
        }
    
    def _get_email_body(self, msg) -> tuple:
        """
        Extract email body (text and HTML)
        
        Args:
            msg: Email message object
        
        Returns:
            Tuple: (text_body, html_body)
        """
        text_body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        decoded = payload.decode('utf-8', errors='ignore')
                        
                        if content_type == "text/plain" and not text_body:
                            text_body = decoded
                        elif content_type == "text/html" and not html_body:
                            html_body = decoded
                except:
                    continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    decoded = payload.decode('utf-8', errors='ignore')
                    content_type = msg.get_content_type()
                    
                    if content_type == "text/plain":
                        text_body = decoded
                    elif content_type == "text/html":
                        html_body = decoded
            except:
                text_body = str(msg.get_payload())
        
        return text_body[:1000], html_body  # Text limit 1000, HTML full
    
    def _is_spam(self, msg) -> bool:
        """
        Check if email is spam/advertisement

        Args:
            msg: Email message object

        Returns:
            True if spam
        """
        # Spam filter removed - always return False
        return False
    
    def get_statistics(self) -> Dict:
        """
        Calculate email statistics
        
        Returns:
            Statistics information
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
            # Sender statistics
            sender = email['from'].split('<')[0].strip() if '<' in email['from'] else email['from']
            if sender not in stats['senders']:
                stats['senders'][sender] = 0
            stats['senders'][sender] += 1
            
            # Date range
            timestamp = email['timestamp']
            if stats['date_range']['start'] is None or timestamp < stats['date_range']['start']:
                stats['date_range']['start'] = timestamp
            if stats['date_range']['end'] is None or timestamp > stats['date_range']['end']:
                stats['date_range']['end'] = timestamp
        
        # Sort senders by email count
        stats['senders'] = dict(
            sorted(stats['senders'].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return stats
    
    def save_to_json(self, output_path: str) -> bool:
        """
        Save emails to JSON file
        
        Args:
            output_path: Output file path
        
        Returns:
            True if successful
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.emails, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Emails saved: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
