# Silk Reeling Machine & Quality Control System

This repository contains the software for a semi-automated silk reeling machine equipped with an image-processing-based silk quality inspection system.

## Architecture

The system is composed of two primary computational units:
1.  **Arduino UNO R3**: Manages real-time hardware interaction, including reading the 4x4 Keypad, Hall Sensor inputs via Pin Change Interrupts, driving TM1637 7-segment displays, and toggling relays for the motor.
2.  **Raspberry Pi Zero 2 W**: Runs a Python application using OpenCV to process a live feed from a USB Digital Microscope. It measures silk thickness, calculates the Denier value, and coordinates with the Arduino over a serial connection. It also provides a graphical user interface (GUI) on a 3.5-inch TFT display via Pygame.

## Directory Structure

*   `arduino/`: Contains the Arduino sketch (`silk_reeling_controller.ino`).
*   `raspberry_pi/`: Contains the Python source code, configuration files, and requirements.

## Setup Instructions

### Arduino Setup
1.  Open `arduino/silk_reeling_controller/silk_reeling_controller.ino` in the Arduino IDE.
2.  Ensure you have installed the `Keypad` and `TM1637` libraries via the Library Manager.
3.  Upload the sketch to your Arduino UNO R3. Note: The spec defines A6/A7 for keypad columns. If using a standard UNO R3 DIP, these pins might not be exposed. Adjust the pin definitions at the top of the file if necessary.

### Raspberry Pi Setup
1.  Install the required dependencies using pip:
    ```bash
    pip3 install -r raspberry_pi/requirements.txt
    ```
2.  Review `raspberry_pi/silk_qc_config.json` to adjust calibration values, ROI (Region of Interest), and camera indices according to your physical setup.
3.  Run the application:
    ```bash
    python3 raspberry_pi/main.py
    ```

## Serial Communication Protocol
The system uses a 115200 baud UART connection via a Logic Level Shifter to protect the 3.3V Raspberry Pi from the 5V Arduino signals.

*   **Arduino -> RPi**: `STATUS,RUNNING`, `COUNT,125`, `TARGET_REACHED`
*   **RPi -> Arduino**: `START`, `STOP`, `RESET`, `STOP,NO_SILK`
