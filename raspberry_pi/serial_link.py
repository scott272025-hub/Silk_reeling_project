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
        
        # Callbacks for received data
        self.on_data_received = None
        
    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            logger.info(f"Connected to Arduino on {self.port} at {self.baudrate}")
            self.is_running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False
            
    def disconnect(self):
        self.is_running = False
        if self.receive_thread:
            self.receive_thread.join(timeout=1.0)
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("Disconnected from Arduino")
            
    def send_command(self, cmd):
        if self.ser and self.ser.is_open:
            try:
                full_cmd = f"{cmd}\n".encode('utf-8')
                self.ser.write(full_cmd)
                # logger.info(f"Sent: {cmd}")
                return True
            except Exception as e:
                logger.error(f"Error sending command: {e}")
                return False
        else:
            logger.warning(f"Cannot send '{cmd}', serial is not connected")
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
                    logger.error(f"Error reading from serial: {e}")
                    time.sleep(1) # Prevent tight loop on error
            else:
                time.sleep(0.1)
