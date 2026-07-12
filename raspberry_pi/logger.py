import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(log_dir="logs", log_file="silk_qc.log"):
    """
    ตั้งค่าระบบการเก็บล็อก (Logging) โดยจะบันทึกทั้งลงในไฟล์และแสดงผลผ่าน Console
    รูปแบบล็อกเป็นไปตามข้อกำหนด:
    2026-07-12 14:30:10,INFO,MACHINE_START
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # รูปแบบล็อกตามที่กำหนด
    # ตัวอย่าง: 2026-07-12 14:30:10,INFO,MACHINE_START
    formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # การบันทึกลงไฟล์ (File Handler) พร้อมระบบหมุนเวียนไฟล์ (Rotating) เพื่อไม่ให้ไฟล์ใหญ่เกินไป
    file_path = os.path.join(log_dir, log_file)
    file_handler = RotatingFileHandler(file_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # การแสดงผลออกหน้าจอ (Console Handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger
