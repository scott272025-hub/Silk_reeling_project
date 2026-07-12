import serial
import threading
import time
import logging

logger = logging.getLogger(__name__)

class SerialLink:
    def __init__(self, port="/dev/serial0", baudrate=115200, timeout=0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.is_running = False
        self.receive_thread = None
        
        # ฟังก์ชัน Callback เมื่อได้รับข้อมูล
        self.on_data_received = None
        
    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logger.info(f"เชื่อมต่อกับ Arduino ทางพอร์ต {self.port} ที่ {self.baudrate} baud สำเร็จ")
            self.is_running = True
            # ใช้ Thread แบบ Non-blocking เพื่อรอรับข้อมูล
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            return True
        except serial.SerialException as e:
            logger.error(f"ไม่สามารถเชื่อมต่อกับ Arduino ได้: {e}")
            return False
            
    def disconnect(self):
        self.is_running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("ยกเลิกการเชื่อมต่อกับ Arduino แล้ว")
            
    def send_command(self, cmd):
        if self.ser and self.ser.is_open:
            try:
                full_cmd = f"{cmd}\n".encode('utf-8')
                self.ser.write(full_cmd)
                return True
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการส่งคำสั่ง: {e}")
                return False
        else:
            logger.warning(f"ไม่สามารถส่งคำสั่ง '{cmd}' ได้ เนื่องจากการเชื่อมต่อขาดหาย")
            return False
            
    def _receive_loop(self):
        while self.is_running:
            if self.ser and self.ser.is_open:
                try:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode('utf-8').strip()
                        if line and self.on_data_received:
                            self.on_data_received(line)
                except Exception as e:
                    logger.error(f"ข้อผิดพลาดขณะอ่านข้อมูลจากพอร์ต: {e}")
                    time.sleep(1) # ป้องกันการวนลูปถี่เกินไปเมื่อเกิดข้อผิดพลาด
            else:
                time.sleep(0.1)
