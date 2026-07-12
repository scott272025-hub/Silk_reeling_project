import cv2
import numpy as np
import logging
from collections import deque

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self, config):
        self.config = config
        
        # Load params from config
        roi = self.config.get('roi', {})
        self.roi_x = roi.get('x', 200)
        self.roi_y = roi.get('y', 120)
        self.roi_w = roi.get('width', 240)
        self.roi_h = roi.get('height', 200)
        
        proc = self.config.get('image_processing', {})
        self.blur_size = proc.get('blur_size', 5)
        self.min_contour_area = proc.get('min_contour_area', 180)
        self.morph_kernel_w = proc.get('morph_kernel_width', 3)
        self.morph_kernel_h = proc.get('morph_kernel_height', 1)
        self.smooth_window = proc.get('smooth_window', 5)
        
        # Ensure blur size is odd
        if self.blur_size % 2 == 0:
            self.blur_size += 1
            
        self.history = deque(maxlen=self.smooth_window)
        
    def process_frame(self, frame):
        """
        Process the frame to find the silk thread thickness in pixels.
        Returns:
            processed_img: The ROI with drawn bounding boxes for GUI.
            thickness_px: The smoothed thickness in pixels (or None if not found).
        """
        if frame is None:
            return None, None
            
        # 1. Crop ROI
        h, w = frame.shape[:2]
        # Safety bounds check
        rx = max(0, min(self.roi_x, w - 1))
        ry = max(0, min(self.roi_y, h - 1))
        rw = max(1, min(self.roi_w, w - rx))
        rh = max(1, min(self.roi_h, h - ry))
        
        roi_img = frame[ry:ry+rh, rx:rx+rw].copy()
        display_img = roi_img.copy()
        
        # 2. Convert to Grayscale
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        
        # 3. Gaussian Blur
        blurred = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)
        
        # 4. Threshold (Otsu Inverse)
        # We assume the silk is darker than the background (or vice versa),
        # Otsu will find the optimal threshold.
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 5. Morphological Opening to remove noise
        kernel = np.ones((self.morph_kernel_h, self.morph_kernel_w), np.uint8)
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # 6. Find Contours
        contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_thicknesses = []
        
        for cnt in contours:
            # 7. Filter by minimum area
            if cv2.contourArea(cnt) >= self.min_contour_area:
                # 8. Measure thickness using minAreaRect
                rect = cv2.minAreaRect(cnt)
                (cx, cy), (rect_w, rect_h), angle = rect
                
                # The thickness is the minimum dimension of the bounding box
                thickness = min(rect_w, rect_h)
                valid_thicknesses.append(thickness)
                
                # Draw on display_img for GUI
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(display_img, [box], 0, (0, 255, 0), 2)
                
        if valid_thicknesses:
            # If multiple valid objects found, we take the largest thickness or average
            # Typically there should be only one main silk thread
            raw_thickness = max(valid_thicknesses)
            
            # 9. Smooth using Moving Average
            self.history.append(raw_thickness)
            smoothed_thickness = sum(self.history) / len(self.history)
            return display_img, smoothed_thickness
        else:
            self.history.clear()
            return display_img, None
