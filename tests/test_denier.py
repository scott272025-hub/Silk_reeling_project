import unittest
import sys
import os

# Add the raspberry_pi directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../raspberry_pi')))

from denier import DenierCalculator
from constants import STATUS_PASS, STATUS_OUT_OF_RANGE, STATUS_NO_SILK

class TestDenierCalculator(unittest.TestCase):
    def setUp(self):
        self.config = {
            'calibration': {
                'pixel_to_mm': 0.002,
                'denier_k': 420.0
            },
            'quality': {
                'denier_min': 18.0,
                'denier_max': 24.0
            }
        }
        self.calculator = DenierCalculator(self.config)

    def test_calculate_denier_valid(self):
        thickness_mm, denier = self.calculator.calculate_denier(25) # 25 * 0.002 = 0.05mm
        self.assertAlmostEqual(thickness_mm, 0.05)
        self.assertAlmostEqual(denier, 21.0) # 420 * 0.05 = 21

    def test_calculate_denier_invalid(self):
        thickness_mm, denier = self.calculator.calculate_denier(None)
        self.assertIsNone(thickness_mm)
        self.assertIsNone(denier)

        thickness_mm, denier = self.calculator.calculate_denier(0)
        self.assertIsNone(thickness_mm)
        self.assertIsNone(denier)

    def test_evaluate_quality_pass(self):
        status = self.calculator.evaluate_quality(21.0)
        self.assertEqual(status, STATUS_PASS)
        
    def test_evaluate_quality_out_of_range(self):
        status = self.calculator.evaluate_quality(17.9)
        self.assertEqual(status, STATUS_OUT_OF_RANGE)
        
        status = self.calculator.evaluate_quality(24.1)
        self.assertEqual(status, STATUS_OUT_OF_RANGE)
        
    def test_evaluate_quality_no_silk(self):
        status = self.calculator.evaluate_quality(None)
        self.assertEqual(status, STATUS_NO_SILK)

if __name__ == '__main__':
    unittest.main()
