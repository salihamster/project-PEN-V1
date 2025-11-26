"""
Loglama yardımcı fonksiyonları
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, log_file: str = None, level: str = "INFO") -> logging.Logger:
    """
    Logger oluştur ve yapılandır
    
    Args:
        name: Logger adı
        log_file: Log dosyası yolu (opsiyonel)
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Yapılandırılmış logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (opsiyonel)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Mevcut logger'ı al veya yeni oluştur
    
    Args:
        name: Logger adı
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
