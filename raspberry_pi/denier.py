import logging

logger = logging.getLogger(__name__)

class DenierCalculator:
    def __init__(self, config):
        self.config = config
        
        calib = self.config.get('calibration', {})
        self.pixel_to_mm = calib.get('pixel_to_mm', 0.002)
        self.denier_k = calib.get('denier_k', 419.92)
        
        quality = self.config.get('quality', {})
        self.denier_min = quality.get('denier_min', 18.0)
        self.denier_max = quality.get('denier_max', 24.0)
        
    def calculate_denier(self, thickness_px):
        """
        คำนวณค่า Denier จากความหนาหน่วยพิกเซล โดยอิงจากค่าคงที่การสอบเทียบ (Calibration)
        ใช้สมการเชิงเส้น: denier = K * thickness_mm
        """
        if thickness_px is None or thickness_px <= 0:
            return None, None
            
        thickness_mm = thickness_px * self.pixel_to_mm
        denier = self.denier_k * thickness_mm
        
        return thickness_mm, denier
        
    def evaluate_quality(self, denier):
        """
        ประเมินว่าค่า Denier ที่คำนวณได้อยู่ในเกณฑ์คุณภาพที่ยอมรับได้หรือไม่
        คืนค่ากลับมาเป็นข้อความสถานะที่กำหนดไว้ในค่าคงที่
        """
        if denier is None:
            from constants import STATUS_NO_SILK
            return STATUS_NO_SILK
            
        if self.denier_min <= denier <= self.denier_max:
            from constants import STATUS_PASS
            return STATUS_PASS
        else:
            from constants import STATUS_OUT_OF_RANGE
            return STATUS_OUT_OF_RANGE
