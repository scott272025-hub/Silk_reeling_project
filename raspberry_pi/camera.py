import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

class CameraStream:
    def __init__(self, camera_index=0, width=640, height=480, target_fps=12):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.target_fps = target_fps
        self.frame_delay = 1.0 / self.target_fps if self.target_fps > 0 else 0
        
        self.cap = None
        self.is_running = False
        self.thread = None
        self.current_frame = None
        self.lock = threading.Lock()
        
        self.error_count = 0
        self.max_errors = 5
        
    def start(self):
        try:
            # เริ่มต้นเชื่อมต่อกับกล้อง USB
            self.cap = cv2.VideoCapture(self.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            if not self.cap.isOpened():
                logger.error(f"ไม่สามารถเปิดกล้อง index ที่ {self.camera_index} ได้")
                return False
                
            self.is_running = True
            # ใช้ Thread เพื่อป้องกันไม่ให้การอ่านภาพทำให้ GUI ค้าง (Non-blocking)
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            logger.info(f"กล้องเริ่มต้นทำงาน (index {self.camera_index}) ความละเอียด {self.width}x{self.height} @ {self.target_fps}fps")
            return True
        except Exception as e:
            logger.exception(f"เกิดข้อผิดพลาดในการเปิดกล้อง: {e}")
            return False
            
    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
            logger.info("กล้องหยุดทำงานแล้ว")
            
    def read(self):
        # คืนค่าภาพเฟรมปัจจุบันอย่างปลอดภัยผ่าน Thread Lock
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None
            
    def _update(self):
        while self.is_running:
            start_time = time.time()
            
            try:
                if self.cap and self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        with self.lock:
                            self.current_frame = frame
                        self.error_count = 0
                    else:
                        self.error_count += 1
                        if self.error_count >= self.max_errors:
                            logger.error("การอ่านภาพจากกล้องล้มเหลวหลายครั้งติดต่อกัน")
                else:
                    self.error_count += 1
            except Exception as e:
                logger.error(f"ข้อผิดพลาดระหว่างการอ่านภาพ: {e}")
                self.error_count += 1
                
            # ควบคุมความเร็วเฟรมเรตตามที่กำหนด (Frame rate control)
            elapsed_time = time.time() - start_time
            sleep_time = self.frame_delay - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    def is_healthy(self):
        # ตรวจสอบสถานะว่ากล้องทำงานปกติหรือไม่
        return self.is_running and self.error_count < self.max_errors
