"""
PEN - Personal Assistant Project
Main execution script for data processing pipeline.

This script orchestrates the data collection and processing workflow:
1. Syncs WhatsApp exports from Google Drive
2. Processes WhatsApp messages
3. Processes emails (if enabled)
4. Generates statistics
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import (
    DATA_DIR, LOGS_DIR, EMAIL_CONFIG_OBJ, SYSTEM_CONFIG,
    GOOGLE_DRIVE_CONFIG, DATA_SOURCE_CONFIG, AGENT_CONFIG
)
from src.utils.logger import setup_logger
from src.parsers.whatsapp_parser import WhatsAppParser
from src.parsers.email_parser import EmailParser
from src.parsers.drive_sync import auto_sync_from_drive
from src.storage.data_manager import DataManager, SaveResult
from src.exceptions import (
    ConfigurationError, DataManagerError, ParserError
)

# Global logger instance
logger = None


def print_banner() -> None:
    """Print application banner."""
    print("=" * 70)
    print("🤖 PEN - Personal Assistant Project")
    print("=" * 70)
    print()


def sync_from_drive() -> List[str]:
    """
    Sync WhatsApp exports from Google Drive.
    
    Downloads new WhatsApp export files from the configured Google Drive
    folder to the local whatsapp_export directory.
    
    Returns:
        List of downloaded file paths
        
    Raises:
        ConfigurationError: If service account file is missing
    """
    logger.info("Syncing WhatsApp exports from Google Drive...")
    
    # Check service account file
    if not GOOGLE_DRIVE_CONFIG.service_account_file.exists():
        logger.warning(
            f"Service account file not found: "
            f"{GOOGLE_DRIVE_CONFIG.service_account_file}"
        )
        logger.info("Skipping Google Drive synchronization")
        return []
    
    # Create WhatsApp export directory
    whatsapp_dir = project_root / "whatsapp_export"
    whatsapp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Sync from Drive (no deletion, manual cleanup required)
        downloaded_files = auto_sync_from_drive(
            service_account_file=str(GOOGLE_DRIVE_CONFIG.service_account_file),
            output_dir=whatsapp_dir,
            folder_name=GOOGLE_DRIVE_CONFIG.folder_name
        )
        
        if downloaded_files:
            logger.info(f"Downloaded {len(downloaded_files)} files from Drive")
            logger.info("Note: Files must be manually deleted from Drive")
            return downloaded_files
        else:
            logger.info("No new files found on Drive")
            return []
    
    except Exception as e:
        logger.error(f"Drive synchronization error: {e}", exc_info=SYSTEM_CONFIG.debug)
        return []


def process_whatsapp(data_manager: DataManager) -> List[SaveResult]:
    """
    Process WhatsApp messages from export files.
    
    This function:
    1. Syncs new files from Google Drive
    2. Parses WhatsApp export .txt files
    3. Saves messages to the data manager
    
    Args:
        data_manager: DataManager instance for saving messages
        
    Returns:
        List of SaveResult objects for each processed chat
    """
    logger.info("Processing WhatsApp messages...")
    
    # Sync from Drive (continue even if sync fails)
    try:
        sync_from_drive()
    except Exception as e:
        logger.warning(f"Drive sync error (continuing): {e}")
    
    # Check WhatsApp export directory
    whatsapp_dir = project_root / "whatsapp_export"
    
    if not whatsapp_dir.exists():
        logger.warning(f"WhatsApp export directory not found: {whatsapp_dir}")
        logger.info("To export WhatsApp chats:")
        logger.info("  1. Open chat in WhatsApp")
        logger.info("  2. Menu (⋮) → More → Export chat")
        logger.info("  3. Select 'Without media'")
        logger.info(f"  4. Upload .txt file to Drive folder: {GOOGLE_DRIVE_CONFIG.folder_name}")
        return []
    
    # Find .txt files
    txt_files = list(whatsapp_dir.glob("*.txt"))
    
    if not txt_files:
        logger.warning("No .txt files found in WhatsApp export directory")
        return []
    
    results = []
    parser = WhatsAppParser()
    
    for txt_file in txt_files:
        logger.info(f"Processing file: {txt_file.name}")
        
        try:
            messages = parser.parse_file(str(txt_file))
            
            if messages:
                # Show statistics
                stats = parser.get_statistics()
                logger.info(f"  Total messages: {stats.get('total_messages', 0)}")
                
                date_range = stats.get('date_range', {})
                start_date = date_range.get('start', 'N/A')[:10]
                end_date = date_range.get('end', 'N/A')[:10]
                logger.info(f"  Date range: {start_date} to {end_date}")
                
                # Extract chat name from filename
                chat_name = txt_file.stem
                
                # Save with categorization
                result = data_manager.save_whatsapp_messages(messages, chat_name)
                results.append(result)
            else:
                logger.warning(f"  No messages parsed from {txt_file.name}")
                
        except ParserError as e:
            logger.error(f"  Parser error for {txt_file.name}: {e}")
        except Exception as e:
            logger.error(
                f"  Unexpected error processing {txt_file.name}: {e}",
                exc_info=SYSTEM_CONFIG.debug
            )
    
    return results


def process_email(data_manager: DataManager) -> Optional[SaveResult]:
    """
    Process emails from configured email account.
    
    This function:
    1. Connects to email server via IMAP
    2. Fetches recent emails
    3. Saves emails to the data manager
    
    Args:
        data_manager: DataManager instance for saving emails
        
    Returns:
        SaveResult object if successful, None otherwise
    """
    logger.info("Processing emails...")
    
    # Check email configuration
    if not EMAIL_CONFIG_OBJ.is_configured():
        logger.warning("Email not configured. Check .env file.")
        return None
    
    # Create email parser with parallel processing
    parser = EmailParser(
        email_address=EMAIL_CONFIG_OBJ.address,
        password=EMAIL_CONFIG_OBJ.password,
        imap_server=EMAIL_CONFIG_OBJ.imap_server,
        imap_port=EMAIL_CONFIG_OBJ.imap_port,
        max_workers=SYSTEM_CONFIG.max_workers
    )
    
    # Connect to server
    if not parser.connect():
        logger.error("Failed to connect to email server")
        return None
    
    try:
        # Fetch emails (all emails, with parallel processing)
        # limit=None means fetch all emails
        emails = parser.fetch_emails(
            folder='INBOX',
            limit=None,
            parallel=True
        )
        
        if emails:
            # Show statistics
            stats = parser.get_statistics()
            logger.info(f"  Total emails: {stats.get('total_emails', 0)}")
            logger.info(f"  Spam count: {stats.get('spam_count', 0)}")
            
            # Save with categorization
            result = data_manager.save_emails(emails)
            return result
        
        return None
    
    finally:
        parser.disconnect()


def display_statistics(data_manager: DataManager) -> None:
    """
    Display overall statistics for all data sources.
    
    Args:
        data_manager: DataManager instance
    """
    try:
        stats = data_manager.get_statistics()
        
        logger.info("\n📊 Overall Statistics:")
        logger.info(f"  WhatsApp Chats: {stats.whatsapp_total_chats}")
        logger.info(f"  WhatsApp Messages: {stats.whatsapp_total_messages}")
        logger.info(f"  Emails: {stats.email_total_count}")
        logger.info(f"  Spam: {stats.email_spam_count}")
        logger.info(f"\n✅ Data categorized and ready for agent!")
        logger.info(f"📁 Data directory: {DATA_DIR}")
        
    except Exception as e:
        logger.error(f"Failed to generate statistics: {e}", exc_info=SYSTEM_CONFIG.debug)


def main() -> None:
    """
    Main execution function.
    
    Orchestrates the complete data processing pipeline:
    1. Initialize logger and data manager
    2. Process WhatsApp messages
    3. Process emails (if enabled)
    4. Display statistics
    """
    print_banner()
    
    # Setup logger
    log_file = LOGS_DIR / f"pen_{datetime.now().strftime('%Y-%m-%d')}.log"
    global logger
    logger = setup_logger('PEN', str(log_file), SYSTEM_CONFIG.log_level.value)
    
    logger.info("PEN starting...")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Log directory: {LOGS_DIR}")
    
    # Initialize data manager
    try:
        data_manager = DataManager(DATA_DIR)
    except DataManagerError as e:
        logger.error(f"Failed to initialize DataManager: {e}")
        print(f"\n❌ Initialization error: {e}")
        return
    
    # Process WhatsApp messages
    if DATA_SOURCE_CONFIG.whatsapp_enabled:
        try:
            whatsapp_results = process_whatsapp(data_manager)
            if whatsapp_results:
                logger.info(f"\n✅ Updated {len(whatsapp_results)} WhatsApp chats")
        except Exception as e:
            logger.error(
                f"WhatsApp processing error: {e}",
                exc_info=SYSTEM_CONFIG.debug
            )
    else:
        logger.info("\n⏭️  WhatsApp processing disabled")
    
    # Process emails (if enabled)
    if EMAIL_CONFIG_OBJ.enabled and DATA_SOURCE_CONFIG.email_enabled:
        try:
            email_result = process_email(data_manager)
            if email_result:
                logger.info(f"\n✅ Emails updated")
        except Exception as e:
            logger.error(
                f"Email processing error: {e}",
                exc_info=SYSTEM_CONFIG.debug
            )
    else:
        logger.info("\n⏭️  Email processing disabled (EMAIL_ENABLED=false)")
    
    # Display statistics
    display_statistics(data_manager)
    
    print("\n" + "=" * 70)
    print("Processing complete!")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if SYSTEM_CONFIG.debug:
            import traceback
            traceback.print_exc()
