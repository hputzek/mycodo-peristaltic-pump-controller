# 🚀 Peristaltic Pump Controller (Mycodo compatible)
![Header image](/assets/header.jpg)

## 📑 Overview
Simplistic peristaltic pump controller firmware to control 6 pumps (4 stepper-based and 2 regular DC motor-based) via serial commands.

In addition, a stirring output is available, which automatically switches on/off to pre-stir the liquids before the pumps activate.

For use with [Mycodo](https://kizniche.github.io/Mycodo/) a custom output is available in `mycodo` folder.
### 🔧 Hardware
[For how to prepare the hardware refer to the hardware docs](./docs/setup-hardware.md)

## 📝 How to Use
For use with [Mycodo](https://kizniche.github.io/Mycodo/) refer to 

### [setup in mycodo](./mycodo/README.md)

### For direct control via serial commands:

1. Connect the controller to your computer or any device capable of sending serial commands.
2. Open a serial terminal or use a program to send commands.
3. Use the command format as described below to send instructions to the device.
4. The device will execute the command and provide feedback through the serial connection.

## 💬 Serial Commands

ℹ️ All commands must be terminated with a newline (`\n`)

| Command | Description                                                             | Parameters                                                                                                                                           |
|---------|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1       | Dispense a specified amount of liquid using a designated stepper motor. | - `stepperNumber` (integer): ID of the stepper motor (1 to 4). <br> - `amount` (float): Amount of liquid in milliliters.                             |
| 2       | Start calibration mode for stepper motors                               | - `stepperNumber` (integer): ID of the stepper motor (1 to 4). <br> - `amountMl` (integer): Amount of liquid in milliliters for calibration.         |
| 3       | Ping device to confirm connection and briefly activate stirrer.         | None                                                                                                                                                |
| 4       | Immediately stop all stepper motors.                                    | None                                                                                                                                                |
| 5       | Dispense a specified amount of liquid using a regular DC motor.         | - `motorNumber` (integer): ID of the motor (1 to 2). <br> - `amount` (float): Amount of liquid in milliliters.                                       |
| 6       | Start calibration mode for regular DC motors                            | - `motorNumber` (integer): ID of the motor (1 to 2). <br> - `amountMl` (integer): Amount of liquid in milliliters for calibration.                   |
| 7       | Stop calibration mode for regular DC motors                             | None                                                                                                                                                |
| 8       | Stop calibration mode for stepper motors                                | None                                                                                                                                                |
| 9       | Check if device is alive                                                | None                                                                                                                                                |

### 🧪 1. Dose Amount - Stepper Motors (`1 stepperNumber amount`)
- **Description**: Dispense a specified amount of liquid using a designated stepper motor. 
- 🚨Can only be used after calibration (see commands 2 and 8)
- **Parameters**:
    - `stepperNumber` (integer): The ID of the stepper motor (1 to 4).
    - `amount` (float): The amount of liquid to be dispensed in milliliters.
- **Example**:
  ```plaintext
  1 2 15.5
  ```
  This command will instruct stepper motor 2 to dispense 15.5 milliliters of liquid.

### ⚙️ 2. Set Calibration Mode - Stepper Motors (`2 stepperNumber amountMl`)
- **Description**: Choose a stepper motor, enter calibration mode to measure and calibrate the steps per milliliter.
- **How to use**:
    * ⚠️ Calibration procedure: the result is used for all four steppers/pumps. You don't need to do it separately for each of the steppers/pumps
    * Get a measuring cup to dispense the liquid in during measurement
    * Start calibration mode and set the amount of liquid you want to use for calibration (e.g. 300ml)
    * The pump will immediately start to dispense
    * Watch the measuring cup
    * Stop the calibration mode (using command 8) as soon as the selected amount was dispensed
    * Calibration is done
- **Parameters**:
    - `stepperNumber` (integer): The ID of the stepper motor (1 to 4).
    - `amountMl` (integer): The amount of liquid in milliliters for calibration. Defaults to 300 ml if not specified.
- **Example**:
  ```plaintext
  2 3 250
  ```
  This command will set stepper motor 3 to calibration mode to measure 250 milliliters of liquid.

### 📡 3. Ping (`3`)
- **Description**: Respond with a simple message to confirm the connection and briefly activate the stirrer output for 5 seconds.
- **Parameters**: None.
- **Example**:
  ```plaintext
  3
  ```
  This command will trigger a response message "{"device":"PumpsX4", "version":"1.0"}" and activate the stirrer output for 5 seconds.

### 🆑 4. Reset All (`4`)
- **Description**: Immediately stop all stepper motors by resetting their positions.
- **Parameters**: None.
- **Example**:
  ```plaintext
  4
  ```
  This command will reset all stepper motors and stop their movements, returning `Stopped all pumps.` as confirmation.

### 🧪 5. Dose Amount - Regular Motors (`5 motorNumber amount`)
- **Description**: Dispense a specified amount of liquid using a regular DC motor pump. 
- 🚨Can only be used after calibration (see commands 6 and 7)
- **Parameters**:
    - `motorNumber` (integer): The ID of the motor (1 to 2).
    - `amount` (float): The amount of liquid to be dispensed in milliliters.
- **Example**:
  ```plaintext
  5 1 15.5
  ```
  This command will instruct regular motor 1 to dispense 15.5 milliliters of liquid.

### ⚙️ 6. Start Calibration Mode - Regular Motors (`6 motorNumber amountMl`)
- **Description**: Choose a regular DC motor, enter calibration mode to measure and calibrate the time per milliliter.
- **How to use**:
    * Get a measuring cup to dispense the liquid in during measurement
    * Start calibration mode and set the amount of liquid you want to use for calibration (e.g. 300ml)
    * The motor will immediately start to dispense
    * Watch the measuring cup
    * Stop the calibration mode using command 7 as soon as the selected amount was dispensed
    * Calibration is done
- **Parameters**:
    - `motorNumber` (integer): The ID of the motor (1 to 2).
    - `amountMl` (integer): The amount of liquid in milliliters for calibration. Defaults to 300 ml if not specified.
- **Example**:
  ```plaintext
  6 2 250
  ```
  This command will start calibration mode on regular motor 2 to measure 250 milliliters of liquid.

### 🛑 7. Stop Calibration Mode - Regular Motors (`7`)
- **Description**: Stop calibration mode for regular DC motors, save the calibration data, and calculate time per milliliter.
- **Parameters**: None.
- **Example**:
  ```plaintext
  7
  ```
  This will stop the calibration mode for regular motors, calculate the time per milliliter based on the measured amount, and turn off both DC motors.

### 🛑 8. Stop Calibration Mode - Stepper Motors (`8`)
- **Description**: Stop calibration mode for stepper motors, save the calibration data, and calculate steps per milliliter.
- **Parameters**: None.
- **Example**:
  ```plaintext
  8
  ```
  This will stop the calibration mode for stepper motors, calculate the steps per milliliter based on the measured amount, and disable the stepper motor.

### 🔄 9. Is Alive Check (`9`)
- **Description**: Check if the device is responding and get basic device information without activating the stirrer.
- **Parameters**: None.
- **Example**:
  ```plaintext
  9
  ```
  This command will return device information in JSON format: `{"device":"PumpsX4", "version":"1.0"}`.