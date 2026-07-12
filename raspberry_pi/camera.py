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
            # For Windows we often use cv2.CAP_DSHOW for USB cameras if needed,
            # but on Pi, default backend is fine.
            self.cap = cv2.VideoCapture(self.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera index {self.camera_index}")
                return False
                
            self.is_running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()
            logger.info(f"Camera started on index {self.camera_index} ({self.width}x{self.height} @ {self.target_fps}fps)")
            return True
        except Exception as e:
            logger.exception(f"Exception starting camera: {e}")
            return False
            
    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
            logger.info("Camera stopped")
            
    def read(self):
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
                            logger.error("Camera read failed repeatedly.")
                            # Could trigger a camera error state here
                else:
                    self.error_count += 1
            except Exception as e:
                logger.error(f"Camera read exception: {e}")
                self.error_count += 1
                
            # Control frame rate
            elapsed_time = time.time() - start_time
            sleep_time = self.frame_delay - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            elif sleep_time < -0.1:
                # Dropping frames
                pass
                
    def is_healthy(self):
        return self.is_running and self.error_count < self.max_errors
