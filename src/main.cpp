#include <AccelStepper.h>
#include "EepromManager.h"
#include "arduino-timer.h"

#define debug_print

#if defined debug_print
#define debug_begin(x)   Serial.begin(x)
#define debug(x)         Serial.print(x)
#define debugln(x)       Serial.println(x)
#else
   #define debug_begin(x)
   #define debug(x)
   #define debugln(x)
#endif

// stepper related
#define MOTOR_INTERFACE_TYPE 1
#define STEPPER_ENABLE_PIN 8

#define DIR_PIN_X 5
#define DIR_PIN_Y 6
#define DIR_PIN_Z 7
#define DIR_PIN_A 13

#define STEP_PIN_X 2
#define STEP_PIN_Y 3
#define STEP_PIN_Z 4
#define STEP_PIN_A 12

#define DEGREES_PER_STEP 1.8f
#define MICRO_STEPS 8

// stirrer pins
#define LIMIT_Z_AXIS 11
#define STIRRING_DISABLE_PIN LIMIT_Z_AXIS // Connect to GND with a jumper to disable Stirring output mode
#define LIMIT_Y_AXIS 10
#define STIRRING_OUTPUT_PIN LIMIT_Y_AXIS // Output pin for stirrer on/off

// motor pins (on&off)
#define ABORT_PIN 14
#define HOLD_PIN 15
#define MOTOR1_PIN ABORT_PIN
#define MOTOR2_PIN HOLD_PIN

EepromManager eepromManager;

// steppers
auto stepper1 = AccelStepper(MOTOR_INTERFACE_TYPE, STEP_PIN_X, DIR_PIN_X);
auto stepper2 = AccelStepper(MOTOR_INTERFACE_TYPE, STEP_PIN_Y, DIR_PIN_Y);
auto stepper3 = AccelStepper(MOTOR_INTERFACE_TYPE, STEP_PIN_Z, DIR_PIN_Z);
auto stepper4 = AccelStepper(MOTOR_INTERFACE_TYPE, STEP_PIN_A, DIR_PIN_A);
AccelStepper* steppers[] = {&stepper1, &stepper2, &stepper3, &stepper4};

unsigned long calibrationStepCounter = 0;
int calibrationStepperNumber = 0;
int calibrationMeasureAmountMl = 0;

unsigned long remainingTicksMotor1 = 0;
unsigned long remainingTicksMotor2 = 0;

auto stirTimer = timer_create_default();
auto motorTimer = timer_create_default();
bool stirringModeEnabled = false;
bool stirrerActive = false;
bool pumpStartDelayActive = false;


bool motor1State = LOW;
bool motor2State = LOW;

void setMotorState(int motorPin, bool& motorState, unsigned long& remainingTicks)
{
    if (remainingTicks > 0)
    {
        if (motorState != HIGH)
        {
            debugln("Motor " + String(motorPin) + " on");
            digitalWrite(motorPin, HIGH);
            motorState = HIGH;
        }
        remainingTicks--;
    }
    else
    {
        if (motorState != LOW)
        {
            debugln("Motor " + String(motorPin) + " off");
            digitalWrite(motorPin, LOW);
            motorState = LOW;
        }
    }
}

bool handleMotors(void*)
{
    setMotorState(MOTOR1_PIN, motor1State, remainingTicksMotor1);
    setMotorState(MOTOR2_PIN, motor2State, remainingTicksMotor2);
    return true;
}


// rotations to steps
long rpsToSteps(const float rps)
{
    return (360.0f / DEGREES_PER_STEP) * MICRO_STEPS * rps;
}

bool steppersActive = false;

void disableSteppers()
{
    if (steppersActive)
    {
        debugln("Disable steppers");
        steppersActive = false;
        stepper1.disableOutputs();
    }
}

void initStepperWithDefaults(AccelStepper& stepper)
{
    stepper.setEnablePin(STEPPER_ENABLE_PIN);
    stepper.setPinsInverted(false, false, true);
    stepper.setMaxSpeed(4000);
    stepper.setAcceleration(stepper.maxSpeed() / 8);
}

// when stirring is enabled, delay the activation of the pumps and start stirring
void setPumpStartDelay()
{
    if (stirringModeEnabled)
    {
        digitalWrite(STIRRING_OUTPUT_PIN, HIGH);
        debugln("Activate stirrer");

        pumpStartDelayActive = true;
        stirrerActive = true;
        stirTimer.cancel();
        stirTimer.in(5000, [](void*) -> bool
        {
            pumpStartDelayActive = false;
            return false;
        });
    }
}


bool pumpStopDelayActive = false;
void handlePumpStopDelay()
{
    bool steppersActive = false;
    for (auto& stepper : steppers)
    {
        if (stepper->distanceToGo() > 0)
        {
            steppersActive = true;
            break;
        }
    }
    if (stirringModeEnabled && remainingTicksMotor1 == 0 && remainingTicksMotor2 == 0 && stirrerActive && !pumpStopDelayActive && !pumpStartDelayActive && !steppersActive)
    {
        pumpStopDelayActive = true;
        stirTimer.in(2000, [](void*) -> bool
        {
            pumpStopDelayActive = false;
            stirrerActive = false;
            digitalWrite(STIRRING_OUTPUT_PIN, LOW);
            debugln("Deactivate stirrer");
            return false;
        });
    }
}

bool f01doseAmountSteppers(const int stepperNumber, const float doseAmount)
{
    if (stepperNumber < 0 || stepperNumber > 4) return false;

    const long stepsToGo = static_cast<long>(doseAmount * eepromManager.getStepsPerMl());
    debugln(
        "Pump " + String(stepperNumber) + ": dosing " + String(doseAmount) + "ml / " + String(stepsToGo) + " steps");
    setPumpStartDelay();
    steppers[stepperNumber - 1]->enableOutputs();
    steppers[stepperNumber - 1]->move(steppers[stepperNumber - 1]->distanceToGo() + stepsToGo);
    steppersActive = true;
    return true;
}

// When enabled, stepper will immediately start rotating and counting the steps it made.
// When disabling, stepper will stop and the measured steps will be saved.
bool f02setCalibrationMode(int stepperNumber, bool status, const int amountMl = 0)
{
    if (stepperNumber < 1 || stepperNumber > 4 || amountMl == 0) return false;

    if (status)
    {
        calibrationMeasureAmountMl = amountMl;
        calibrationStepperNumber = stepperNumber;
        steppers[stepperNumber - 1]->setSpeed(2500);
        calibrationStepCounter = 1;
        stepper1.enableOutputs();
    }
    else
    {
        debugln("------- CALIBRATION RESULT ------");
        debug("Steps: ");
        debugln(calibrationStepCounter);
        debug("Liquid Amount: ");
        debugln(calibrationMeasureAmountMl);
        debug("Steps/ml: ");
        debugln(calibrationStepCounter / calibrationMeasureAmountMl);
        eepromManager.setStepsPerMl(calibrationStepCounter / calibrationMeasureAmountMl);
        steppers[stepperNumber - 1]->disableOutputs();
        steppers[stepperNumber - 1]->setCurrentPosition(0);
        calibrationStepCounter = 0;
        calibrationMeasureAmountMl = 0;
    }
    return true;
}

Timer<>::Task stirringTask = nullptr;

void f03Ping()
{
    Serial.println(R"({"device":"PumpsX4", "version":"1.0"})");
    digitalWrite(STIRRING_OUTPUT_PIN, HIGH);

    if (stirringTask != nullptr)
    {
        stirTimer.cancel(stirringTask);
    }

    stirringTask = stirTimer.in(5000, [](void*) -> bool
    {
        digitalWrite(STIRRING_OUTPUT_PIN, LOW);
        stirringTask = nullptr;
        return true;
    });
}

void f04ResetAll()
{
    for (auto& stepper : steppers)
    {
        stepper->setCurrentPosition(0);
    }
    Serial.println("Stopped all pumps.");
}

bool f05doseAmountMotors(const int motorNumber, const float doseAmount)
{
    if (motorNumber < 1 || motorNumber > 2) return false;
    if (doseAmount > 0)
    {
        debugln("Motor " + String(motorNumber) + ": dosing " + String(doseAmount));
        setPumpStartDelay();
        if (motorNumber == 1)
        {
            if (remainingTicksMotor1 != 0)
            {
                debugln(" + remaining " + String(remainingTicksMotor1));
            }
            remainingTicksMotor1 += doseAmount;
        }
        else
        {
            if (remainingTicksMotor2 != 0)
            {
                debugln(" + remaining " + String(remainingTicksMotor2));
            }
            remainingTicksMotor2 += doseAmount;
        }
    }
    return true;
}


void parseSerialCommand(const String& command)
{
    int functionNumber = -1;
    char commandCopy[command.length() + 1];
    command.toCharArray(commandCopy, command.length() + 1);

    char* token = strtok(commandCopy, " ");
    if (token != nullptr)
    {
        functionNumber = atoi(token);
    }

    if (functionNumber == 1) // doseAmount function
    {
        int stepperNumber = -1;
        float amount = 0.0f;

        token = strtok(nullptr, " ");
        if (token != nullptr) stepperNumber = atoi(token);

        token = strtok(nullptr, " ");
        if (token != nullptr) amount = atof(token);

        if (!f01doseAmountSteppers(stepperNumber, amount))
        {
            debug("Invalid stepper number or amount: ");
            debugln(stepperNumber);
        }
    }
    else if (functionNumber == 2) // setCalibrationMode function
    {
        int stepperNumber = -1;
        bool status = false;
        int amountMl = 300; // default value

        token = strtok(nullptr, " ");
        if (token != nullptr) stepperNumber = atoi(token);

        token = strtok(nullptr, " ");
        if (token != nullptr) status = atoi(token);

        token = strtok(nullptr, " ");
        if (token != nullptr) amountMl = atoi(token);

        if (f02setCalibrationMode(stepperNumber, status, amountMl))
        {
            debug("Calibration mode ");
            debugln(status == 1 ? "on" : "off");
        }
        else
        {
            debug("Invalid stepper number, status, or amountMl: ");
            debugln(command);
        }
    }
    else if (functionNumber == 3)
    {
        f03Ping();
    }
    else if (functionNumber == 4)
    {
        f04ResetAll();
    }
    else if (functionNumber == 5)
    {
        f05doseAmountMotors(1, 2000);
    }
    else
    {
        debug("Unknown function number: ");
        debugln(functionNumber);
    }
}

void pollSerial()
{
    static String inputString = ""; // A string to hold incoming data
    static bool stringComplete = false; // Whether the string is complete

    // Read the incoming data one character at a time
    while (Serial.available() > 0 && !stringComplete)
    {
        char inChar = (char)Serial.read();
        inputString += inChar;

        // Check if the incoming character is a newline character
        if (inChar == '\n')
        {
            stringComplete = true;
        }
    }

    // When the string is complete, call parseSerialCommand
    if (stringComplete)
    {
        parseSerialCommand(inputString);
        inputString = ""; // Clear the string
        stringComplete = false; // Reset the flag
    }
}

void runSteppers()
{
    // calibration mode
    if (calibrationStepCounter > 0)
    {
        if (steppers[calibrationStepperNumber - 1]->runSpeed())
        {
            calibrationStepCounter++;
        };
    }
    // dosing mode
    else
    {
        bool mustDisableSteppers = true;

        for (auto& stepper : steppers)
        {
            if (stepper->distanceToGo() > 0)
            {
                mustDisableSteppers = false;
                stepper->run();
                // Arduino uno is too slow to handle more than 1 pump running at once.
                // this is why the break is here: it lets only one pump run at a time
                break;
            }
        }

        if (mustDisableSteppers)
        {
            disableSteppers();
        }
    }
}

void setup()
{
    Serial.begin(9600);
    for (auto& stepper : steppers)
    {
        initStepperWithDefaults(*stepper);
    }
    pinMode(STIRRING_DISABLE_PIN, INPUT_PULLUP);
    pinMode(STIRRING_OUTPUT_PIN, OUTPUT);
    pinMode(MOTOR1_PIN, OUTPUT);
    pinMode(MOTOR2_PIN, OUTPUT);
    stirringModeEnabled = digitalRead(STIRRING_DISABLE_PIN) == HIGH;
    motorTimer.every(1, handleMotors);
    f03Ping();
}

void loop()
{
    stirTimer.tick<void>();
    handlePumpStopDelay();
    if (!pumpStartDelayActive || !stirringModeEnabled)
    {
        motorTimer.tick();
        runSteppers();
    }
    pollSerial();
}
