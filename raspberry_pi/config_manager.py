import json
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_path="silk_qc_config.json"):
        self.config_path = config_path
        self.config = {}
        self.load_config()

    def load_config(self):
        try:
            if not os.path.exists(self.config_path):
                logger.error(f"ไม่พบไฟล์คอนฟิก (Config file) ที่ตำแหน่ง {self.config_path}")
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info("โหลดการตั้งค่าสำเร็จ")
            return True
        except Exception as error:
            logger.exception(f"เกิดข้อผิดพลาดในการโหลดการตั้งค่า: {error}")
            return False

    def get(self, section, key=None, default=None):
        if not self.config:
            return default
            
        try:
            if key is None:
                return self.config.get(section, default)
            
            section_data = self.config.get(section, {})
            return section_data.get(key, default)
        except Exception as error:
            logger.exception(f"เกิดข้อผิดพลาดในการเข้าถึงการตั้งค่าส่วน {section}.{key}: {error}")
            return default

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logger.info("บันทึกการตั้งค่าสำเร็จ")
            return True
        except Exception as error:
            logger.exception(f"เกิดข้อผิดพลาดในการบันทึกการตั้งค่า: {error}")
            return False
            
    def update(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        return self.save_config()
