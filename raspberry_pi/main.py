import time
import logging
import sys

from config_manager import ConfigManager
from logger import setup_logger
from serial_link import SerialLink
from camera import CameraStream
from image_processing import ImageProcessor
from denier import DenierCalculator
from gpio_control import BuzzerControl
from gui import GUI
from constants import *

logger = setup_logger()

class Application:
    def __init__(self):
        logger.info("กำลังเริ่มต้นระบบส่วนกลาง...")
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        
        self.serial_link = SerialLink(
            port=self.config.get('serial', {}).get('port', '/dev/serial0'),
            baudrate=self.config.get('serial', {}).get('baudrate', 115200)
        )
        self.serial_link.on_data_received = self.handle_serial_data
        
        cam_conf = self.config.get('camera', {})
        self.camera = CameraStream(
            camera_index=cam_conf.get('camera_index', 0),
            width=cam_conf.get('camera_width', 640),
            height=cam_conf.get('camera_height', 480),
            target_fps=cam_conf.get('target_fps', 12)
        )
        
        self.image_processor = ImageProcessor(self.config)
        self.denier_calc = DenierCalculator(self.config)
        self.buzzer = BuzzerControl(self.config)
        
        # ฟังก์ชันเมื่อมีการกดปุ่ม
        callbacks = {
            'start': self.cmd_start,
            'stop': self.cmd_stop,
            'reset': self.cmd_reset,
            'calibrate': self.cmd_calibrate,
            'exit': self.cmd_exit
        }
        self.gui = GUI(self.config, callbacks)
        
        self.is_running = True
        self.machine_state = STATE_IDLE
        self.current_count = 0
        self.target_count = 0
        
        # ตัวแปรสำหรับลอจิกควบคุมคุณภาพ (QC Logic)
        qc_conf = self.config.get('quality', {})
        self.bad_frame_limit = qc_conf.get('bad_frame_limit', 10)
        self.bad_duration_seconds = qc_conf.get('bad_duration_seconds', 5.0)
        self.no_silk_frame_limit = qc_conf.get('no_silk_frame_limit', 15)
        self.no_silk_duration_seconds = qc_conf.get('no_silk_duration_seconds', 5.0)
        
        self.bad_frame_count = 0
        self.bad_start_time = None
        self.no_silk_frame_count = 0
        self.no_silk_start_time = None

    def handle_serial_data(self, data):
        """ประมวลผลข้อมูลที่ส่งมาจาก Arduino"""
        # รูปแบบเช่น STATUS,RUNNING หรือ COUNT,125
        parts = data.split(',')
        if len(parts) >= 2:
            key, val = parts[0], parts[1]
            if key == "STATUS":
                self.machine_state = val
                logger.info(f"สถานะเครื่องจักรเปลี่ยนเป็น: {self.machine_state}")
            elif key == "COUNT":
                self.current_count = int(val)
            elif key == "TARGET":
                self.target_count = int(val)
            elif key == "TARGET_REACHED":
                self.stop_machine(REASON_TARGET_REACHED)
            elif key == "EMERGENCY_STOP":
                self.stop_machine(REASON_EMERGENCY_STOP)
                self.buzzer.play_alarm()

    def send_serial(self, cmd):
        self.serial_link.send_command(cmd)

    def cmd_start(self):
        logger.info("คำสั่งจาก GUI: เริ่มทำงาน (START)")
        self.send_serial("START")
        self.buzzer.stop_alarm()
        self.reset_qc_counters()

    def cmd_stop(self):
        logger.info("คำสั่งจาก GUI: หยุด (STOP)")
        self.stop_machine(REASON_MANUAL_STOP)

    def cmd_reset(self):
        logger.info("คำสั่งจาก GUI: รีเซ็ต (RESET)")
        self.send_serial("RESET")
        self.machine_state = STATE_IDLE
        self.reset_qc_counters()
        self.buzzer.stop_alarm()

    def cmd_calibrate(self):
        logger.info("คำสั่งจาก GUI: สอบเทียบ (CALIBRATE - ยังไม่สมบูรณ์แบบ)")
        pass

    def cmd_exit(self):
        logger.info("คำสั่งจาก GUI: ออกจากโปรแกรม (EXIT)")
        self.is_running = False

    def stop_machine(self, reason):
        logger.warning(f"สั่งหยุดเครื่องจักร. เหตุผล: {reason}")
        if reason == REASON_NO_SILK:
            self.send_serial("STOP,NO_SILK")
        elif reason == REASON_OUT_OF_RANGE:
            self.send_serial("STOP,OUT_OF_RANGE")
        else:
            self.send_serial("STOP")
            
        self.machine_state = STATE_STOPPED
        if reason in [REASON_NO_SILK, REASON_OUT_OF_RANGE, REASON_CAMERA_ERROR]:
            self.buzzer.play_alarm()

    def reset_qc_counters(self):
        self.bad_frame_count = 0
        self.bad_start_time = None
        self.no_silk_frame_count = 0
        self.no_silk_start_time = None

    def run(self):
        logger.info("เริ่มต้นการทำงานของทุกระบบ...")
        self.serial_link.connect()
        self.camera.start()
        
        # วงจรการทำงานหลัก (Main Event Loop)
        try:
            while self.is_running:
                # 1. จัดการเหตุการณ์จาก GUI
                self.gui.process_events()
                
                # 2. รับภาพจากกล้อง
                frame = self.camera.read()
                cam_status = "ออนไลน์" if self.camera.is_healthy() else "มีปัญหา"
                
                if cam_status == "มีปัญหา" and self.machine_state == STATE_RUNNING:
                    self.stop_machine(REASON_CAMERA_ERROR)
                
                # 3. ประมวลผลภาพ
                display_img, thickness_px = self.image_processor.process_frame(frame)
                
                # 4. คำนวณค่าคุณภาพ (Denier)
                thickness_mm, denier = self.denier_calc.calculate_denier(thickness_px)
                qc_status = self.denier_calc.evaluate_quality(denier)
                
                # 5. ตรวจสอบเงื่อนไขการหยุดเครื่องอัตโนมัติขณะเดินเครื่อง
                if self.machine_state == STATE_RUNNING:
                    now = time.time()
                    
                    if qc_status == STATUS_NO_SILK:
                        self.no_silk_frame_count += 1
                        if self.no_silk_start_time is None:
                            self.no_silk_start_time = now
                            
                        no_silk_duration = now - self.no_silk_start_time
                        if self.no_silk_frame_count >= self.no_silk_frame_limit and no_silk_duration >= self.no_silk_duration_seconds:
                            self.stop_machine(REASON_NO_SILK)
                    else:
                        self.no_silk_frame_count = 0
                        self.no_silk_start_time = None
                        
                    if qc_status == STATUS_OUT_OF_RANGE:
                        self.bad_frame_count += 1
                        if self.bad_start_time is None:
                            self.bad_start_time = now
                            
                        bad_duration = now - self.bad_start_time
                        if self.bad_frame_count >= self.bad_frame_limit and bad_duration >= self.bad_duration_seconds:
                            self.stop_machine(REASON_OUT_OF_RANGE)
                    else:
                        self.bad_frame_count = 0
                        self.bad_start_time = None
                        
                    if self.target_count > 0 and self.current_count >= self.target_count:
                        self.stop_machine(REASON_TARGET_REACHED)
                
                # 6. อัปเดตข้อมูลบน GUI
                self.gui.update_state(
                    machine_state=self.machine_state,
                    camera_status=cam_status,
                    denier=denier,
                    status_text=qc_status,
                    thickness_mm=thickness_mm,
                    current_count=self.current_count,
                    target_count=self.target_count
                )
                self.gui.draw(display_img)
                
                # หน่วงเวลาเล็กน้อยเพื่อไม่ให้กินทรัพยากร CPU เต็ม 100% (GUI แสดงผลที่ประมาณ 30-60 FPS)
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            logger.info("ผู้ใช้สั่งหยุดการทำงานของระบบ")
        except Exception as e:
            logger.exception(f"เกิดข้อผิดพลาดที่ไม่คาดคิดในวงจรการทำงานหลัก: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        logger.info("กำลังทำความสะอาดทรัพยากร (Cleanup)...")
        self.camera.stop()
        self.serial_link.disconnect()
        self.buzzer.stop_alarm()
        self.gui.quit()
        logger.info("ปิดระบบสมบูรณ์")

if __name__ == "__main__":
    app = Application()
    app.run()
