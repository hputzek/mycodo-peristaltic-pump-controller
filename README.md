# 🚀 Peristaltic Pump Controller (Mycodo compatible)
![Header image](/assets/header.jpg)

## 📑 Overview
Simplistic peristaltic pump controller firmware to control 4 pumps via serial commands.

In addition, a stirring output is available, which automatically switches on/off to pre-stir the liquids before the pumps activate.

For use with [Mycodo](https://kizniche.github.io/Mycodo/) a custom output is available in `mycodo` folder.
### 🔧 Hardware
[For how to prepare the hardware refer to the hardware docs](./docs/setup-hardware.md)

### 🛠️ Compile Firmware
[This is a Platformio project.](https://platformio.org/)

## 📝 How to Use

1. Connect the controller to your computer or any device capable of sending serial commands.
2. Open a serial terminal or use a program to send commands.
3. Use the command format as described below to send instructions to the device.
4. The device will execute the command and provide feedback through the serial connection.

## 💬 Serial Commands

ℹ️ All commands must be terminated with a newline (`\n`)

| Command | Description                                                             | Parameters                                                                                                                                                                                            |
|---------|-------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1       | Dispense a specified amount of liquid using a designated stepper motor. | - `stepperNumber` (integer): ID of the stepper motor (1 to 4). <br> - `amount` (float): Amount of liquid in milliliters.                                                                              |
| 2       | Activate/deactivate calibration mode                                    | - `stepperNumber` (integer): ID of the stepper motor (1 to 4). <br> - `status` (boolean): `1` to start calibration mode, `0` to finish. <br> - `amountMl` (integer): Amount of liquid in milliliters. |
| 3       | Respond with a simple message to confirm the connection.                | None                                                                                                                                                                                                  |
| 4       | Immediately stop all motors.                                            | None                                                                                                                                                                                                  |

### 🧪 1. Dose Amount (`1 stepperNumber amount`)
- **Description**: Dispense a specified amount of liquid using a designated stepper motor. 
- 🚨Can only be used after calibration (see 2)
- **Parameters**:
    - `stepperNumber` (integer): The ID of the stepper motor (1 to 4).
    - `amount` (float): The amount of liquid to be dispensed in milliliters.
- **Example**:
  ```plaintext
  1 2 15.5
  ```
  This command will instruct stepper motor 2 to dispense 15.5 milliliters of liquid.

### ⚙️ 2. Set Calibration Mode (`2 stepperNumber status amountMl`)
- **Description**: Choose a stepper motor, enter calibration mode to measure and calibrate the steps per milliliter.
- **How to use**:
    * ⚠️ Calibration procedure: the result is used for all four steppers/pumps. You don't need to do it separately for each of the steppers/pumps
    * Get a measuring cup to dispense the liquid in during measurement
    * Start calibration mode and set the amount of liquid you want to use for calibration (e.g. 500ml)
    * The pump will immediately start to dispense
    * Watch the measuring cup
    * Stop the calibration mode as soon as the selected amount was dispensed
    * Calibration is done
- **Parameters**:
    - `stepperNumber` (integer): The ID of the stepper motor (1 to 4).
    - `status` (boolean): `1` to start calibration mode, `0` to stop it.
    - `amountMl` (integer, optional): The amount of liquid in milliliters for calibration. Defaults to 300 ml if not specified.
- **Example**:
  ```plaintext
  2 3 1 250
  ```
  This command will set stepper motor 3 to calibration mode to measure 250 milliliters of liquid. To finish calibration, send:
  ```plaintext
  2 3 0
  ```

### 📡 3. Ping (`3`)
- **Description**: Respond with a simple message to confirm the connection.
- **Parameters**: None.
- **Example**:
  ```plaintext
  3
  ```
  This command will trigger a response message "{"device":"PumpsX4", "version":"1.0"}".

### 🆑 4. Reset All (`4`)
- **Description**: Immediately stop all motors.
- **Parameters**: None.
- **Example**:
  ```plaintext
  4
  ```
  This command will reset all stepper motors and stop their movements.

#### Example Usage

To dose 10 milliliters via stepper motor 1:
```plaintext
1 1 10.0
```

To start calibration mode on stepper motor 2 for 300 milliliters:
```plaintext
2 2 1 300
```

To stop calibration mode on stepper motor 2:
```plaintext
2 2 0
```

To ping the device:
```plaintext
3
```

To stop all pumps:
```plaintext
4
```