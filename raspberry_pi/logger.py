import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(log_dir="logs", log_file="silk_qc.log"):
    """
    Setup logging configuration that writes to both console and file.
    Logs are format as specified in the rules:
    2026-07-12 14:30:10,INFO,MACHINE_START
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Custom format to match the specification as closely as possible
    # Specification format: 2026-07-12 14:30:10,INFO,MACHINE_START
    formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # File Handler
    file_path = os.path.join(log_dir, log_file)
    file_handler = RotatingFileHandler(file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger
