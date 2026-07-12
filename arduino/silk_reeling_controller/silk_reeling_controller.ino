#include <Keypad.h>
#include <TM1637Display.h>

// --- การกำหนดขา (PIN DEFINITIONS) ---
const int RELAY_PIN = 7;
const int HALL_PIN = 5;

// หน้าจอ TM1637 ตัวที่ 1 (แสดงจำนวนรอบปัจจุบัน)
const int TM1637_1_CLK = 4;
const int TM1637_1_DIO = 6;
TM1637Display display1(TM1637_1_CLK, TM1637_1_DIO);

// หน้าจอ TM1637 ตัวที่ 2 (แสดงจำนวนรอบเป้าหมาย)
const int TM1637_2_CLK = 9;
const int TM1637_2_DIO = 10;
TM1637Display display2(TM1637_2_CLK, TM1637_2_DIO);

// แป้นพิมพ์ (Keypad)
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

// ใช้ A0-A3 สำหรับแถว, A4-A7 สำหรับคอลัมน์ (A6, A7 อาจต้องปรับเปลี่ยนตามบอร์ดที่ใช้)
byte rowPins[ROWS] = {A0, A1, A2, A3};
byte colPins[COLS] = {A4, A5, A6, A7}; 
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// --- ตัวแปร (VARIABLES) ---
volatile long currentCount = 0; // จำนวนรอบปัจจุบัน
long targetCount = 0;           // จำนวนรอบเป้าหมาย
String inputString = "";        // ข้อความรับค่าจากแป้นพิมพ์
bool isRunning = false;         // สถานะเครื่องกำลังทำงาน
bool emergencyStop = false;     // สถานะหยุดฉุกเฉิน
unsigned long lastSerialTime = 0;
const int SERIAL_INTERVAL = 500; // มิลลิวินาทีสำหรับการส่งข้อมูลสถานะ

void setup() {
  Serial.begin(115200);
  
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  
  pinMode(HALL_PIN, INPUT_PULLUP);
  
  // สำหรับ Arduino UNO การทำ Pin Change Interrupt บนขา 5 (PCINT21 / PORTD 5)
  // เพื่อให้อ่านค่าจาก Hall Sensor ได้อย่างแม่นยำ
  PCICR |= B00000100;  // เปิดใช้งาน PCIE2
  PCMSK2 |= B00100000; // เปิดใช้งาน PCINT21 (ขา 5)
  
  // ตั้งค่าความสว่างหน้าจอ
  display1.setBrightness(0x0f);
  display2.setBrightness(0x0f);
  
  // แสดงค่าเริ่มต้นเป็น 0
  display1.showNumberDec(currentCount);
  display2.showNumberDec(targetCount);
}

// ฟังก์ชัน Interrupt (ISR) สำหรับตรวจจับสัญญาณจาก Hall Sensor
ISR(PCINT2_vect) {
  static bool lastState = HIGH;
  bool currentState = digitalRead(HALL_PIN);
  if (lastState == HIGH && currentState == LOW) {
    // ตรวจจับขอบขาลง (Falling edge) แสดงว่าแม่เหล็กผ่านเซ็นเซอร์
    if (isRunning) {
      currentCount++;
    }
  }
  lastState = currentState;
}

void loop() {
  handleKeypad();    // ตรวจสอบการกดปุ่ม
  handleSerial();    // ตรวจสอบคำสั่งที่ได้รับจาก Raspberry Pi
  checkTarget();     // ตรวจสอบว่าถึงจำนวนรอบเป้าหมายหรือยัง
  sendStatus();      // ส่งสถานะปัจจุบันกลับไปให้ Raspberry Pi
}

void startMachine() {
  if (!emergencyStop) {
    isRunning = true;
    digitalWrite(RELAY_PIN, HIGH); // เปิดรีเลย์มอเตอร์
    Serial.println("STATUS,RUNNING");
  }
}

void stopMachine(String reason = "") {
  isRunning = false;
  digitalWrite(RELAY_PIN, LOW); // ปิดรีเลย์มอเตอร์
  Serial.println("STATUS,STOPPED");
}

void handleKeypad() {
  char key = keypad.getKey();
  if (key) {
    if (key >= '0' && key <= '9') {
      inputString += key;
      display2.showNumberDec(inputString.toInt());
    } else if (key == '*') {
      // ลบตัวเลขล่าสุด
      if (inputString.length() > 0) {
        inputString.remove(inputString.length() - 1);
        display2.showNumberDec(inputString.toInt());
      } else {
        display2.showNumberDec(targetCount);
      }
    } else if (key == '#') {
      // ยืนยันจำนวนรอบเป้าหมาย
      if (inputString.length() > 0) {
        targetCount = inputString.toInt();
        inputString = "";
        display2.showNumberDec(targetCount);
        Serial.print("TARGET,");
        Serial.println(targetCount);
      }
    } else if (key == 'A') {
      // เริ่มหรือหยุดการทำงาน
      if (isRunning) {
        stopMachine();
      } else {
        startMachine();
      }
    } else if (key == 'B') {
      // ล้างค่าที่ป้อนเข้ามา
      inputString = "";
      display2.showNumberDec(targetCount);
    } else if (key == 'D') {
      // รีเซ็ตค่าทั้งหมด
      stopMachine();
      currentCount = 0;
      targetCount = 0;
      inputString = "";
      emergencyStop = false;
      display1.showNumberDec(currentCount);
      display2.showNumberDec(targetCount);
    }
  }
}

void handleSerial() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "START") {
      startMachine();
    } else if (cmd.startsWith("STOP")) {
      stopMachine(cmd); // รับค่าเช่น STOP,NO_SILK เป็นต้น
    } else if (cmd == "RESET") {
      stopMachine();
      currentCount = 0;
      targetCount = 0;
      inputString = "";
      display1.showNumberDec(currentCount);
      display2.showNumberDec(targetCount);
    }
  }
}

void checkTarget() {
  // หากจำนวนรอบที่นับได้เท่ากับหรือมากกว่าเป้าหมาย ให้สั่งหยุดเครื่องอัตโนมัติ
  if (isRunning && targetCount > 0 && currentCount >= targetCount) {
    stopMachine("TARGET_REACHED");
    Serial.println("TARGET_REACHED");
  }
}

void sendStatus() {
  // อัปเดตหน้าจอ TM1637 และส่งค่าทาง Serial ทุกๆ 500 ms
  if (millis() - lastSerialTime >= SERIAL_INTERVAL) {
    lastSerialTime = millis();
    display1.showNumberDec(currentCount);
    Serial.print("COUNT,");
    Serial.println(currentCount);
  }
}
