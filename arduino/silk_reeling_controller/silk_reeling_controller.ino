#include <Keypad.h>
#include <TM1637Display.h>

// --- PIN DEFINITIONS ---
const int RELAY_PIN = 7;
const int HALL_PIN = 5;

// TM1637 Display 1 (Current Count)
const int TM1637_1_CLK = 4;
const int TM1637_1_DIO = 6;
TM1637Display display1(TM1637_1_CLK, TM1637_1_DIO);

// TM1637 Display 2 (Target Count)
const int TM1637_2_CLK = 9;
const int TM1637_2_DIO = 10;
TM1637Display display2(TM1637_2_CLK, TM1637_2_DIO);

// Keypad
const byte ROWS = 4;
const byte COLS = 4;
char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

// Using A0-A3 for Rows, A4-A7 for Cols (A6, A7 may need change depending on board)
byte rowPins[ROWS] = {A0, A1, A2, A3};
byte colPins[COLS] = {A4, A5, A6, A7}; 
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// --- VARIABLES ---
volatile long currentCount = 0;
long targetCount = 0;
String inputString = "";
bool isRunning = false;
bool emergencyStop = false;
unsigned long lastSerialTime = 0;
const int SERIAL_INTERVAL = 500; // ms

void setup() {
  Serial.begin(115200);
  
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  
  pinMode(HALL_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(HALL_PIN), countPulse, FALLING); // Use pin 2 or 3 for hardware interrupt on UNO
  // Note: Pin 5 is NOT an external interrupt pin on Arduino UNO.
  // We need to use Pin 2 or Pin 3. We will stick to the spec but handle it via Pin Change Interrupt if possible
  // For simplicity, we will check pin state in loop if attachInterrupt fails, but UNO only supports INT0/1 on pins 2, 3.
  // Wait, the specification says HALL_PIN = 5. I will implement polling or Pin Change Interrupt.
  // Let's use polling for pin 5 since it's not a standard external interrupt on UNO.
  // (Actually, let's just do standard polling in the loop for now to be safe with Pin 5, or setup PCINT)
  
  // For PCINT on Pin 5 (PCINT21 / PORTD 5)
  PCICR |= B00000100;  // Enable PCIE2
  PCMSK2 |= B00100000; // Enable PCINT21 (Pin 5)
  
  display1.setBrightness(0x0f);
  display2.setBrightness(0x0f);
  
  display1.showNumberDec(currentCount);
  display2.showNumberDec(targetCount);
}

// ISR for Pin Change Interrupt on Port D (Pins 0-7)
ISR(PCINT2_vect) {
  static bool lastState = HIGH;
  bool currentState = digitalRead(HALL_PIN);
  if (lastState == HIGH && currentState == LOW) {
    // Falling edge detected
    if (isRunning) {
      currentCount++;
    }
  }
  lastState = currentState;
}

void countPulse() {
  // If pin 2 or 3 was used
  if (isRunning) {
    currentCount++;
  }
}

void loop() {
  handleKeypad();
  handleSerial();
  checkTarget();
  sendStatus();
}

void startMachine() {
  if (!emergencyStop) {
    isRunning = true;
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println("STATUS,RUNNING");
  }
}

void stopMachine(String reason = "") {
  isRunning = false;
  digitalWrite(RELAY_PIN, LOW);
  if (reason != "") {
    Serial.println("STATUS,STOPPED");
  } else {
    Serial.println("STATUS,STOPPED");
  }
}

void handleKeypad() {
  char key = keypad.getKey();
  if (key) {
    if (key >= '0' && key <= '9') {
      inputString += key;
      display2.showNumberDec(inputString.toInt());
    } else if (key == '*') {
      if (inputString.length() > 0) {
        inputString.remove(inputString.length() - 1);
        display2.showNumberDec(inputString.toInt());
      } else {
        display2.showNumberDec(targetCount);
      }
    } else if (key == '#') {
      if (inputString.length() > 0) {
        targetCount = inputString.toInt();
        inputString = "";
        display2.showNumberDec(targetCount);
        Serial.print("TARGET,");
        Serial.println(targetCount);
      }
    } else if (key == 'A') {
      if (isRunning) {
        stopMachine();
      } else {
        startMachine();
      }
    } else if (key == 'B') {
      inputString = "";
      display2.showNumberDec(targetCount);
    } else if (key == 'D') {
      // Reset
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
      stopMachine(cmd); // Can be STOP,NO_SILK, etc.
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
  if (isRunning && targetCount > 0 && currentCount >= targetCount) {
    stopMachine("TARGET_REACHED");
    Serial.println("TARGET_REACHED");
  }
}

void sendStatus() {
  if (millis() - lastSerialTime >= SERIAL_INTERVAL) {
    lastSerialTime = millis();
    display1.showNumberDec(currentCount);
    Serial.print("COUNT,");
    Serial.println(currentCount);
  }
}
