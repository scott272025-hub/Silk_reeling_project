import unittest
import sys
import os

# Add the raspberry_pi directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../raspberry_pi')))

from main import Application
from constants import STATE_IDLE, REASON_TARGET_REACHED, REASON_EMERGENCY_STOP

class MockConfigManager:
    def __init__(self):
        self.config = {}

class TestSerialParser(unittest.TestCase):
    def setUp(self):
        # We just want to test handle_serial_data, but it's part of Application.
        # We can bypass hardware init by overriding config and mocking
        self.app = Application.__new__(Application)
        self.app.machine_state = STATE_IDLE
        self.app.current_count = 0
        self.app.target_count = 0
        
        class MockBuzzer:
            def play_alarm(self): pass
            def stop_alarm(self): pass
        self.app.buzzer = MockBuzzer()
        
        # Override stop_machine for testing
        self.stopped_reason = None
        def mock_stop(reason):
            self.stopped_reason = reason
        self.app.stop_machine = mock_stop
        
    def test_parse_status(self):
        self.app.handle_serial_data("STATUS,RUNNING")
        self.assertEqual(self.app.machine_state, "RUNNING")
        
        self.app.handle_serial_data("STATUS,STOPPED")
        self.assertEqual(self.app.machine_state, "STOPPED")
        
    def test_parse_count(self):
        self.app.handle_serial_data("COUNT,150")
        self.assertEqual(self.app.current_count, 150)
        
    def test_parse_target(self):
        self.app.handle_serial_data("TARGET,500")
        self.assertEqual(self.app.target_count, 500)
        
    def test_parse_target_reached(self):
        self.app.handle_serial_data("TARGET_REACHED,") # Depending on format
        self.assertEqual(self.stopped_reason, REASON_TARGET_REACHED)
        
    def test_parse_emergency_stop(self):
        self.app.handle_serial_data("EMERGENCY_STOP,") 
        self.assertEqual(self.stopped_reason, REASON_EMERGENCY_STOP)

if __name__ == '__main__':
    unittest.main()
