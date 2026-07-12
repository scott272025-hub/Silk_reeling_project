import logging
import threading
import time
import os

# Use gpiozero if available, otherwise mock it for testing on non-Pi systems
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
                logger.info(f"Buzzer initialized on GPIO pin {self.pin}")
            except Exception as e:
                logger.error(f"Failed to initialize buzzer: {e}")
        else:
            logger.warning(f"GPIO not available. Buzzer on pin {self.pin} will be mocked.")
            
    def play_alarm(self):
        """Play alarm for the configured duration using a non-blocking timer."""
        if self.is_sounding:
            # Already sounding, maybe extend time? For now, ignore.
            return
            
        self.is_sounding = True
        logger.info("Buzzer ON")
        if self.buzzer:
            self.buzzer.on()
            
        # Stop automatically after duration
        self.timer = threading.Timer(self.duration, self.stop_alarm)
        self.timer.start()
        
    def stop_alarm(self):
        """Stop the alarm manually or via timer."""
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
            
        self.is_sounding = False
        logger.info("Buzzer OFF")
        if self.buzzer:
            self.buzzer.off()
