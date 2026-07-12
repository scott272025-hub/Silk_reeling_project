import unittest
import sys
import os
import numpy as np

# Add the raspberry_pi directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../raspberry_pi')))

from image_processing import ImageProcessor

class TestImageProcessor(unittest.TestCase):
    def setUp(self):
        self.config = {
            'roi': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
            'image_processing': {
                'blur_size': 3,
                'min_contour_area': 10,
                'morph_kernel_width': 3,
                'morph_kernel_height': 3,
                'smooth_window': 1
            }
        }
        self.processor = ImageProcessor(self.config)

    def test_process_empty_frame(self):
        # White background
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 255
        display_img, thickness = self.processor.process_frame(frame)
        
        self.assertIsNone(thickness)
        self.assertIsNotNone(display_img)

    def test_process_frame_with_line(self):
        # White background
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 255
        # Draw a black line (thickness roughly 10 px)
        frame[40:50, :] = 0
        
        display_img, thickness = self.processor.process_frame(frame)
        
        self.assertIsNotNone(thickness)
        # Should be roughly 10 based on bounding box
        self.assertGreater(thickness, 5)
        self.assertLess(thickness, 15)

if __name__ == '__main__':
    unittest.main()
