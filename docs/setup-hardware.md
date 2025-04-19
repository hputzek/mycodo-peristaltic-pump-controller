# 🔧 Hardware
* Arduino Uno
* [CNC shield v3](https://www.az-delivery.de/en/products/az-delivery-cnc-shield-v3) + drivers
* 4x Peristaltic Pump with stepper motor ([e.g. from AliExpress](https://de.aliexpress.com/item/1005004240331933.html))
* optional: 2x Peristaltic pump with "normal" DC motor
* optional: stirring mechanism to stir up the liquids before dispensing

## 🛠️ Compile Firmware
[This is a Platformio project.](https://platformio.org/) please refer to their docs on how to upload the firmware to your arduino uno.

## Auto stirring
**Connect a stirring mechanism to the corresponding output to stir the liquids before enabling the pumps.**

ℹ️ Can be disabled via jumper, see "setup hardware"

When auto stirring is enabled via jumper, the stirring output is enabled and pump output is delayed 5 seconds.
It will shut off again 2 seconds after all pumps are done.

Additional hardware e.g. a magnetic stirrer is needed. The board just provides the digital out for a stirring mechanism

### set reference voltage for stepper drivers
[See here](https://all3dp.com/2/vref-calculator-tmc2209-tmc2208-a4988/)

## Setup hardware

You can connect the following external components:
* 4x servo motor for peristaltic pumps
* 2x DC motor → you need additional components to switch the motor load(s), e.g. a [MOS FET](https://de.aliexpress.com/item/1005006221334574.html)
* The stirrer output can be used as a status indicator, too if you connect a led.

### configure CNC shield with jumpers
![](/assets/cnc-shield-v3-setup_with_motors.png)

### Pinout arduino ↔️ CNC shield
![](/assets/cnc-shield-v3-arduino-pinout.png)
