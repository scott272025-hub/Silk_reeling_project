---
trigger: always_on
---

# Project Specification  
## ระบบเครื่องสาวไหมกึ่งอัตโนมัติและตรวจสอบคุณภาพเส้นไหมด้วยการประมวลผลภาพ

> ไฟล์นี้ใช้เป็น Project Context / Development Specification สำหรับนำไปใช้งานใน Google Antigravity IDE หรือเครื่องมือ AI Coding Assistant
---

## 1. ชื่อโครงการ

**ภาษาไทย:**  
การพัฒนานวัตกรรมเครื่องสาวไหม และตรวจสอบคุณภาพเส้นไหมด้วยเทคโนโลยีการประมวลผลภาพ

**ภาษาอังกฤษ:**  
Development of Innovative Silk Reeling and Silk Quality Inspection Machines Using Image Processing Technology

---

## 2. เป้าหมายของระบบ

พัฒนาระบบเครื่องสาวไหมกึ่งอัตโนมัติที่สามารถ:

1. ควบคุมการเริ่มและหยุดเครื่องสาวไหม
2. กำหนดจำนวนรอบเป้าหมายผ่าน Keypad 4×4
3. นับจำนวนรอบด้วย proximity sensor
4. แสดงจำนวนรอบผ่านจอ TM1637
5. ตรวจจับเส้นไหมด้วยกล้อง USB Microscope แบบเรียลไทม์
6. วัดความหนาของเส้นไหมจากภาพ
7. คำนวณค่าความละเอียดเส้นไหมเป็นหน่วย Denier
8. แสดงสถานะคุณภาพเส้นไหมบนจอ TFT 3.5 นิ้ว
9. หยุดเครื่องอัตโนมัติเมื่อ:
   - จำนวนรอบถึงเป้าหมาย
   - ไม่พบเส้นไหมตามเงื่อนไข
   - คุณภาพเส้นไหมออกนอกเกณฑ์ตามเงื่อนไข
10. แจ้งเตือนด้วยเสียง Buzzer เมื่อเกิดความผิดปกติ

---

## 3. สถาปัตยกรรมระบบ

ระบบแบ่งออกเป็น 2 ส่วนหลัก

### 3.1 Arduino UNO R3

รับผิดชอบงานควบคุมเครื่องจักรแบบเรียลไทม์ ได้แก่:

- อ่าน Keypad 4×4
- อ่าน Hall Sensor
- นับจำนวนรอบ
- ควบคุม Relay
- ควบคุม TM1637
- รับคำสั่งหยุดจาก Raspberry Pi
- ส่งข้อมูลสถานะไปยัง Raspberry Pi

### 3.2 Raspberry Pi Zero 2 W

รับผิดชอบงานประมวลผลภาพและส่วนติดต่อผู้ใช้ ได้แก่:

- รับภาพจาก USB Microscope
- ประมวลผลภาพด้วย OpenCV
- ตรวจจับเส้นไหม
- วัดความหนาเส้นไหม
- คำนวณค่า Denier
- แสดง GUI บนจอ MHS TFT 3.5 นิ้ว
- ส่งคำสั่ง STOP ไปยัง Arduino
- ควบคุม Buzzer
- บันทึกค่าการตรวจสอบ

---

## 4. ฮาร์ดแวร์หลัก

### 4.1 ฝั่ง Arduino

- Arduino UNO R3
- Relay Module
- Hall Sensor
- Magnet
- Keypad 4×4
- TM1637 4-Digit Display จำนวน 2 ชุด
- วงจรควบคุมมอเตอร์
- External PWM Motor Speed Controller 6–60V 30A
- Power Supply
- Emergency Stop หรือ Safety Breaker

### 4.2 ฝั่ง Raspberry Pi

- Raspberry Pi Zero 2 W
- MHS 3.5-inch TFT Display
- USB Digital Microscope 50×–1000×
- Logic Level Shifter
- Buzzer
- MicroSD Card
- Power Supply 5V ที่เพียงพอ

---

## 5. การกำหนดขา Arduino UNO R3

```cpp
// Relay
RELAY_PIN = 7

// Hall Sensor
HALL_PIN = 5

// TM1637 ชุดที่ 1
TM1637_1_CLK = 4
TM1637_1_DIO = 6

// TM1637 ชุดที่ 2
TM1637_2_CLK = 9
TM1637_2_DIO = 10

// Keypad Rows
ROW_1 = A0
ROW_2 = A1
ROW_3 = A2
ROW_4 = A3

// Keypad Columns
COL_1 = A4
COL_2 = A5
COL_3 = A6
COL_4 = A7

PULSES_PER_REV = 1
```

> หมายเหตุ: Arduino UNO แบบ DIP บางรุ่นไม่มี A6 และ A7 ให้ใช้งานภายนอก  
> หากบอร์ดไม่มี A6/A7 ต้องเปลี่ยนไปใช้ขา Digital ที่ว่าง หรือปรับวงจรใหม่

---

## 6. หน้าที่ของปุ่ม Keypad

| ปุ่ม | หน้าที่ |
|---|---|
| 0–9 | ป้อนจำนวนรอบเป้าหมาย |
| `*` | ลบตัวเลขล่าสุด |
| `#` | ยืนยันจำนวนรอบเป้าหมาย |
| A | เริ่มหรือหยุดเครื่อง |
| B | ล้างค่าที่ป้อน |
| C | สลับโหมดหรือหน้าจอ |
| D | รีเซ็ตระบบและจำนวนรอบ |

---

## 7. การเชื่อมต่อ Raspberry Pi กับ Arduino

ใช้ UART Serial ผ่าน Logic Level Shifter

### ตัวเลือกหลัก

```text
Raspberry Pi GPIO14 TXD → Level Shifter → Arduino RX
Raspberry Pi GPIO15 RXD ← Level Shifter ← Arduino TX
GND Raspberry Pi ↔ GND Arduino
```

### ตัวเลือก GPIO สำรอง

หาก GPIO14 และ GPIO15 ถูกใช้งานโดยจอ TFT สามารถกำหนด Software UART หรือ UART Overlay ให้ใช้:

```text
Raspberry Pi GPIO5 → TX
Raspberry Pi GPIO6 → RX
```

การใช้งาน GPIO5 และ GPIO6 ต้องกำหนด Device Tree Overlay และทดสอบความเข้ากันได้กับระบบปฏิบัติการก่อนใช้งานจริง

### ระดับแรงดัน

- Raspberry Pi ใช้ Logic 3.3V
- Arduino UNO ใช้ Logic 5V
- ห้ามต่อ Arduino TX 5V เข้าขา RX ของ Raspberry Pi โดยตรง
- ต้องใช้ Logic Level Shifter หรือวงจรแบ่งแรงดัน

---

## 8. Serial Protocol

ใช้ข้อความแบบบรรทัดเดียว จบด้วย `\n`

### 8.1 Arduino ส่งไป Raspberry Pi

```text
STATUS,RUNNING
STATUS,STOPPED
RPM,100
COUNT,125
TARGET,500
TARGET_REACHED
EMERGENCY_STOP
```

### 8.2 Raspberry Pi ส่งไป Arduino

```text
START
STOP
RESET
STOP,NO_SILK
STOP,OUT_OF_RANGE
STOP,CAMERA_ERROR
```

### 8.3 รูปแบบข้อมูลที่แนะนำ

```text
KEY,VALUE
```

ตัวอย่าง:

```text
COUNT,250
DENIER,21.45
QUALITY,PASS
```

---

## 9. กล้องและการประมวลผลภาพ

### 9.1 กล้อง

- USB Digital Microscope
- Resolution เริ่มต้น: 640×480
- Frame Rate เป้าหมาย: 12 FPS
- ควรล็อกตำแหน่งกล้องและระยะโฟกัส
- ใช้แสง LED คงที่
- หลีกเลี่ยงแสงสะท้อนและการเปลี่ยนแปลงแสงภายนอก

### 9.2 ROI

ค่าตั้งต้น:

```python
ROI_X = 200
ROI_Y = 120
ROI_W = 240
ROI_H = 200
```

### 9.3 Pipeline การประมวลผลภาพ

1. อ่านภาพจากกล้อง
2. Crop เฉพาะ ROI
3. แปลงภาพเป็น Grayscale
4. Gaussian Blur
5. Threshold แบบ Otsu Inverse
6. Morphological Opening
7. ค้นหา Contour
8. กรอง Contour ตามพื้นที่ขั้นต่ำ
9. เลือกวัตถุที่มีลักษณะเป็นเส้นไหม
10. วัดความหนาเป็น Pixel
11. Smooth ค่าด้วย Moving Average
12. แปลง Pixel เป็นมิลลิเมตร
13. คำนวณ Denier
14. เปรียบเทียบกับเกณฑ์คุณภาพ
15. แสดงผลบน GUI

### 9.4 ค่าตั้งต้น

```python
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
TARGET_FPS = 12

BLUR_SIZE = 5
MORPH_KERNEL_W = 3
MORPH_KERNEL_H = 1
MIN_CONTOUR_AREA = 180

SMOOTH_WINDOW = 5
```

---

## 10. การวัดความหนาเส้นไหม

ให้ใช้กรอบสี่เหลี่ยมครอบวัตถุหรือ Rotated Rectangle

```python
thickness_px = min(rect_width, rect_height)
```

ห้ามใช้ด้านที่ยาวกว่าเป็นค่าความหนา เพราะจะทำให้วัดความยาวของเส้นไหมแทน

### การแปลง Pixel เป็นมิลลิเมตร

```python
thickness_mm = thickness_px * pixel_to_mm
```

ค่า `pixel_to_mm` ต้องได้จากการ Calibration จริง

---

## 11. การ Calibration

### 11.1 วัตถุอ้างอิง

ใช้วัตถุที่ทราบขนาดจริง เช่น:

- เส้นลวดมาตรฐาน
- แผ่น Calibration
- ไม้บรรทัด Microscope
- เส้นอ้างอิงที่ทราบเส้นผ่านศูนย์กลาง

### 11.2 สูตร

```python
pixel_to_mm = known_width_mm / measured_width_px
```

### 11.3 ข้อกำหนด

- ระยะกล้องต้องคงที่
- Zoom ต้องคงที่
- Focus ต้องคงที่
- ตำแหน่งเส้นไหมต้องผ่านบริเวณเดิม
- ห้ามเปลี่ยน Resolution หลัง Calibration

---

## 12. การคำนวณ Denier

Denier คือมวลของเส้นใยหน่วยกรัมต่อความยาว 9,000 เมตร

```text
Denier = น้ำหนักเส้นไหมหน่วยกรัม × 9000 / ความยาวเส้นไหมหน่วยเมตร
```

หากประเมินจากภาพ ต้องใช้สมการ Calibration ที่ได้จากตัวอย่างจริง

รูปแบบสมการตัวอย่าง:

```python
denier = K * measured_value
```

หรือ:

```python
denier = a * thickness_mm + b
```

หรือ:

```python
denier = a * thickness_mm**2 + b
```

ห้ามกำหนดสมการโดยไม่มีข้อมูลทดลองจริง

### ค่าตัวแปรที่ต้องเก็บใน Config

```json
{
  "calibration_k": 419.92,
  "pixel_to_mm": 0.002,
  "denier_min": 18.0,
  "denier_max": 24.0
}
```

> ค่าในตัวอย่างเป็นเพียงค่าตั้งต้น ต้องตรวจสอบกับผลการทดลองจริง

---

## 13. สถานะคุณภาพ

ระบบต้องแสดงสถานะภาษาไทยดังนี้:

```text
ผ่าน
ออกนอกเกณฑ์
ไม่พบเส้นไหม
```

### 13.1 ผ่าน

เกิดเมื่อ:

```python
denier_min <= denier <= denier_max
```

### 13.2 ออกนอกเกณฑ์

เกิดเมื่อ:

```python
denier < denier_min or denier > denier_max
```

### 13.3 ไม่พบเส้นไหม

เกิดเมื่อ:

- ไม่พบ Contour ที่ผ่านเกณฑ์
- พื้นที่ Contour ต่ำกว่า `MIN_CONTOUR_AREA`
- ไม่พบเส้นไหมต่อเนื่องตามจำนวน Frame และเวลาที่กำหนด

---

## 14. เงื่อนไขหยุดอัตโนมัติ

### 14.1 ออกนอกเกณฑ์

ต้องครบทั้งสองเงื่อนไข:

- ออกนอกเกณฑ์ต่อเนื่องอย่างน้อย 10 Frame
- เวลาต่อเนื่องอย่างน้อย 5 วินาที

```python
if bad_frame_count >= 10 and bad_duration >= 5.0:
    stop_machine("OUT_OF_RANGE")
```

### 14.2 ไม่พบเส้นไหม

ต้องครบทั้งสองเงื่อนไข:

- ไม่พบเส้นไหมต่อเนื่องอย่างน้อย 15 Frame
- เวลาต่อเนื่องอย่างน้อย 5 วินาที

```python
if no_silk_frame_count >= 15 and no_silk_duration >= 5.0:
    stop_machine("NO_SILK")
```

### 14.3 จำนวนรอบถึงเป้าหมาย

```python
if current_count >= target_count:
    stop_machine("TARGET_REACHED")
```

### 14.4 กล้องผิดพลาด

หากอ่านภาพไม่ได้หลายครั้งติดต่อกัน ให้:

1. แสดงสถานะ Camera Error
2. ส่ง STOP ไป Arduino
3. เปิด Buzzer
4. บันทึก Error Log

---

## 15. Buzzer

Buzzer อยู่ฝั่ง Raspberry Pi

### เงื่อนไขเปิดเสียง

- ไม่พบเส้นไหม
- เส้นไหมออกนอกเกณฑ์
- กล้องผิดพลาด
- การเชื่อมต่อ Arduino ขาด
- Emergency Stop

### ระยะเวลา

```python
BUZZER_DURATION = 10
```

ควรใช้ Non-blocking Timer ห้ามใช้ `time.sleep(10)` ใน Main Loop เพราะจะทำให้ GUI ค้าง

---

## 16. GUI บนจอ MHS TFT 3.5 นิ้ว

### 16.1 ความละเอียด

```text
480 × 320 pixels
```

### 16.2 โหมด

- Fullscreen
- ไม่มีกรอบหน้าต่าง
- รองรับ Touchscreen
- ปุ่มมีขนาดใหญ่พอสำหรับนิ้วมือ
- ใช้ภาษาไทยที่อ่านง่าย

### 16.3 ข้อมูลที่ต้องแสดง

1. ภาพจากกล้อง
2. กรอบ ROI
3. ค่า Thickness Pixel
4. ค่า Thickness mm
5. ค่า Denier
6. ค่า Denier ต่ำสุดและสูงสุด
7. จำนวนรอบปัจจุบัน
8. จำนวนรอบเป้าหมาย
9. สถานะเครื่อง
10. สถานะคุณภาพ
11. สถานะกล้อง
12. สถานะการเชื่อมต่อ Arduino

### 16.4 ปุ่มบน GUI

- START
- STOP
- RESET
- CALIBRATE
- SETTINGS
- EXIT

### 16.5 Layout แนะนำ

```text
┌──────────────────────────────────────────────┐
│ MACHINE: RUNNING     CAMERA: ONLINE          │
├───────────────────────────┬──────────────────┤
│                           │ Denier: 21.45    │
│       CAMERA VIEW         │ Status: ผ่าน     │
│                           │ Thickness: 0.05  │
│                           │ Count: 125/500   │
├───────────────────────────┴──────────────────┤
│ START │ STOP │ RESET │ CALIBRATE │ SETTINGS │
└──────────────────────────────────────────────┘
```

---

## 17. เทคโนโลยีซอฟต์แวร์

### Raspberry Pi

- Python 3
- OpenCV
- Pygame
- PySerial
- RPi.GPIO หรือ gpiozero
- JSON
- CSV
- Logging
- Threading หรือ Queue

### Arduino

- Arduino C++
- Keypad Library
- TM1637Display Library
- Interrupt หรือ Debounce สำหรับ Hall Sensor
- Serial Communication

---

## 18. โครงสร้างโปรเจกต์ที่แนะนำ

```text
silk_reeling_project/
│
├── raspberry_pi/
│   ├── main.py
│   ├── gui.py
│   ├── camera.py
│   ├── image_processing.py
│   ├── calibration.py
│   ├── denier.py
│   ├── serial_link.py
│   ├── gpio_control.py
│   ├── logger.py
│   ├── config_manager.py
│   ├── constants.py
│   ├── silk_qc_config.json
│   ├── requirements.txt
│   └── logs/
│
├── arduino/
│   └── silk_reeling_controller/
│       └── silk_reeling_controller.ino
│
├── docs/
│   ├── wiring.md
│   ├── serial_protocol.md
│   ├── calibration_guide.md
│   └── test_plan.md
│
├── tests/
│   ├── test_denier.py
│   ├── test_serial_parser.py
│   └── test_image_processing.py
│
└── README.md
```

---

## 19. Config File

ชื่อไฟล์:

```text
silk_qc_config.json
```

ตัวอย่าง:

```json
{
  "camera_index": 0,
  "camera_width": 640,
  "camera_height": 480,
  "target_fps": 12,

  "roi": {
    "x": 200,
    "y": 120,
    "width": 240,
    "height": 200
  },

  "image_processing": {
    "blur_size": 5,
    "min_contour_area": 180,
    "morph_kernel_width": 3,
    "morph_kernel_height": 1,
    "smooth_window": 5
  },

  "calibration": {
    "pixel_to_mm": 0.002,
    "denier_k": 419.92
  },

  "quality": {
    "denier_min": 18.0,
    "denier_max": 24.0,
    "bad_frame_limit": 10,
    "bad_duration_seconds": 5.0,
    "no_silk_frame_limit": 15,
    "no_silk_duration_seconds": 5.0
  },

  "serial": {
    "port": "/dev/serial0",
    "baudrate": 115200,
    "timeout": 0.1
  },

  "buzzer": {
    "pin": 18,
    "duration_seconds": 10
  },

  "display": {
    "width": 480,
    "height": 320,
    "fullscreen": true
  }
}
```

---

## 20. ข้อกำหนดการเขียนโปรแกรม

### 20.1 ห้ามทำให้ GUI ค้าง

ห้ามใช้คำสั่ง Blocking ใน Main Loop เช่น:

```python
time.sleep(10)
serial.readline()
camera.read()  # หากไม่มี Timeout หรือ Recovery
```

ให้ใช้:

- Timer
- Thread
- Queue
- Non-blocking Serial
- Event Loop

### 20.2 Error Handling

ทุกโมดูลต้องมี:

```python
try:
    ...
except Exception as error:
    logger.exception(error)
```

ห้ามใช้:

```python
except:
    pass
```

### 20.3 Logging

ต้องบันทึกอย่างน้อย:

- เวลาเริ่มระบบ
- เวลาเริ่มเครื่อง
- เวลาหยุดเครื่อง
- เหตุผลการหยุด
- ค่า Denier
- สถานะคุณภาพ
- จำนวนรอบ
- Error จากกล้อง
- Error จาก Serial

ตัวอย่าง:

```text
2026-07-12 14:30:10,INFO,MACHINE_START
2026-07-12 14:30:11,DATA,DENIER=21.45,STATUS=PASS,COUNT=125
2026-07-12 14:31:02,WARNING,NO_SILK
2026-07-12 14:31:07,STOP,REASON=NO_SILK
```

---

## 21. State Machine

ระบบควรใช้ State Machine

```text
IDLE
READY
RUNNING
STOPPING
STOPPED
ALARM
ERROR
CALIBRATING
```

### การเปลี่ยน State

```text
IDLE → พร้อม
READY → กำลังทำงาน
RUNNING → STOPPING
STOPPING → STOPPED
RUNNING → ALARM
ALARM → STOPPED
ANY STATE → เกิดข้อผิดพลาด
ERROR → IDLE หลัง Reset สำเ