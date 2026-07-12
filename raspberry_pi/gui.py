import pygame
import cv2
import sys
import numpy as np
import logging
from constants import *

logger = logging.getLogger(__name__)

# รหัสสี (Colors)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)

class Button:
    def __init__(self, rect, text, color, hover_color, action):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False

    def draw(self, surface, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, width=2, border_radius=5)
        
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.action()

class GUI:
    def __init__(self, config, callbacks):
        self.config = config
        self.callbacks = callbacks
        
        display_conf = self.config.get('display', {})
        self.width = display_conf.get('width', 480)
        self.height = display_conf.get('height', 320)
        self.fullscreen = display_conf.get('fullscreen', True)
        
        # ตัวแปรแสดงสถานะบนหน้าจอ
        self.machine_state = STATE_IDLE
        self.camera_status = "ออฟไลน์"
        self.denier = 0.0
        self.status_text = "รอการเริ่มงาน"
        self.thickness_mm = 0.0
        self.current_count = 0
        self.target_count = 0
        
        pygame.init()
        # ใช้ Font ของระบบเพื่อรองรับภาษาไทยเบื้องต้น (หากต้องการภาษาไทยสมบูรณ์ต้องชี้ไปที่ไฟล์ .ttf ภาษาไทย)
        try:
            self.font_large = pygame.font.SysFont("tahoma", 24)
            self.font_small = pygame.font.SysFont("tahoma", 18)
        except:
            self.font_large = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
            
        if self.fullscreen:
            # สำหรับการใช้งานจริงบนจอ Raspberry Pi อาจจำเป็นต้องเปิดโหมด Fullscreen
            self.screen = pygame.display.set_mode((self.width, self.height))
        else:
            self.screen = pygame.display.set_mode((self.width, self.height))
            
        pygame.display.set_caption("เครื่องสาวไหม & ควบคุมคุณภาพ")
        
        self.buttons = []
        self._create_buttons()
        
    def _create_buttons(self):
        button_y = self.height - 50
        button_w = 85
        button_h = 40
        spacing = (self.width - (button_w * 5)) // 6
        
        self.buttons.append(Button((spacing, button_y, button_w, button_h), "เริ่ม (START)", GREEN, LIGHT_GRAY, self.callbacks.get('start', lambda: None)))
        self.buttons.append(Button((spacing*2 + button_w, button_y, button_w, button_h), "หยุด (STOP)", RED, LIGHT_GRAY, self.callbacks.get('stop', lambda: None)))
        self.buttons.append(Button((spacing*3 + button_w*2, button_y, button_w, button_h), "รีเซ็ต (RESET)", YELLOW, LIGHT_GRAY, self.callbacks.get('reset', lambda: None)))
        self.buttons.append(Button((spacing*4 + button_w*3, button_y, button_w, button_h), "สอบเทียบ", LIGHT_GRAY, WHITE, self.callbacks.get('calibrate', lambda: None)))
        self.buttons.append(Button((spacing*5 + button_w*4, button_y, button_w, button_h), "ออก (EXIT)", GRAY, WHITE, self.callbacks.get('exit', lambda: None)))

    def update_state(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
                
    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.callbacks.get('exit', lambda: sys.exit(0))()
            for button in self.buttons:
                button.handle_event(event)

    def draw(self, camera_frame):
        self.screen.fill(BLACK)
        
        # 1. แถบข้อมูลด้านบน (Header)
        header_text = f"เครื่องจักร: {self.machine_state}   กล้อง: {self.camera_status}"
        header_surf = self.font_large.render(header_text, True, WHITE)
        self.screen.blit(header_surf, (10, 10))
        
        pygame.draw.line(self.screen, GRAY, (0, 40), (self.width, 40), 2)
        
        # 2. มุมมองจากกล้อง (Camera View)
        # ขนาดมาตรฐานคือประมาณ 240x200
        cam_rect = pygame.Rect(10, 50, 240, 200)
        pygame.draw.rect(self.screen, GRAY, cam_rect, 1)
        
        if camera_frame is not None:
            try:
                # เปลี่ยนจาก BGR (OpenCV) เป็น RGB (Pygame)
                rgb_frame = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                # ปรับขนาดภาพให้พอดีกับกรอบ (Resize)
                rgb_frame = cv2.resize(rgb_frame, (cam_rect.w, cam_rect.h))
                # สลับแกนภาพเพื่อใช้กับ Pygame
                surf = pygame.surfarray.make_surface(np.swapaxes(rgb_frame, 0, 1))
                self.screen.blit(surf, (cam_rect.x, cam_rect.y))
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการวาดเฟรมจากกล้อง: {e}")
        else:
            no_cam_text = self.font_small.render("ไม่มีสัญญาณภาพจากกล้อง", True, RED)
            self.screen.blit(no_cam_text, (cam_rect.x + 20, cam_rect.y + 90))
            
        # 3. แถบสถิติข้อมูล (Stats Panel)
        stats_x = 260
        stats_y = 60
        line_spacing = 30
        
        def draw_stat(label, value, y_offset, color=WHITE):
            text = f"{label}: {value}"
            surf = self.font_small.render(text, True, color)
            self.screen.blit(surf, (stats_x, stats_y + y_offset))

        draw_stat("ดีเนียร์ (Denier)", f"{self.denier:.2f}" if self.denier else "--", 0)
        
        # สีของข้อความสถานะ (Status Color)
        status_color = GREEN if self.status_text == STATUS_PASS else (RED if self.status_text in [STATUS_OUT_OF_RANGE, STATUS_NO_SILK] else WHITE)
        draw_stat("สถานะคุณภาพ", self.status_text, line_spacing, status_color)
        
        draw_stat("ความหนา", f"{self.thickness_mm:.3f} mm" if self.thickness_mm else "--", line_spacing * 2)
        draw_stat("จำนวนรอบ", f"{self.current_count} / {self.target_count}", line_spacing * 3)

        pygame.draw.line(self.screen, GRAY, (0, self.height - 60), (self.width, self.height - 60), 2)
        
        # 4. ปุ่มกด (Buttons)
        for button in self.buttons:
            button.draw(self.screen, self.font_small)
            
        pygame.display.flip()
        
    def quit(self):
        pygame.quit()
