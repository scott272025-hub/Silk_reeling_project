import logging
import threading
import time
import os

# ใช้ gpiozero หากมีบนระบบ มิฉะนั้นให้จำลองการทำงานไว้สำหรับการทดสอบบนคอมพิวเตอร์ทั่วไป
try:
    if os.name != 'nt':
        from gpiozero import Buzzer
        GPIO_AVAILABLE = True
    else:
        GPIO_AVAILABLE = False
except ImportError:
    GPIO_AVAILABLE = False

logger = logging.getLogger(__name__)

class BuzzerControl:
    def __init__(self, config):
        self.config = config
        buzzer_conf = self.config.get('buzzer', {})
        self.pin = buzzer_conf.get('pin', 18)
        self.duration = buzzer_conf.get('duration_seconds', 10)
        
        self.buzzer = None
        self.is_sounding = False
        self.timer = None
        
        if GPIO_AVAILABLE:
            try:
                self.buzzer = Buzzer(self.pin)
                logger.info(f"เริ่มต้นการทำงานของ Buzzer บนขา GPIO {self.pin}")
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการเริ่มต้น Buzzer: {e}")
        else:
            logger.warning(f"ไม่มีระบบ GPIO บนเครื่องนี้ การทำงานของ Buzzer บนขา {self.pin} จะถูกจำลองขึ้นแทน")
            
    def play_alarm(self):
        """ส่งเสียงเตือนตามระยะเวลาที่กำหนด โดยใช้ Timer แบบ Non-blocking"""
        if self.is_sounding:
            # หากกำลังส่งเสียงอยู่แล้ว ให้ละเว้นคำสั่งนี้
            return
            
        self.is_sounding = True
        logger.info("Buzzer: เปิดเสียง (ON)")
        if self.buzzer:
            self.buzzer.on()
            
        # สั่งให้หยุดเสียงอัตโนมัติเมื่อครบกำหนดเวลา
        self.timer = threading.Timer(self.duration, self.stop_alarm)
        self.timer.start()
        
    def stop_alarm(self):
        """หยุดเสียงเตือนทันที"""
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
            
        self.is_sounding = False
        logger.info("Buzzer: ปิดเสียง (OFF)")
        if self.buzzer:
            self.buzzer.off()
