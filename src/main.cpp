#include <AccelStepper.h>
#include "EepromManager.h"

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

#define motorInterfaceType 1
#define stepperEnablePin 8

#define dirPinX 5
#define dirPinY 6
#define dirPinZ 7
#define dirPinA 13

#define stepPinX 2
#define stepPinY 3
#define stepPinZ 4
#define stepPinA 12

#define degreesPerStep 1.8f
#define microSteps 8

auto stepper1 = AccelStepper(motorInterfaceType, stepPinX, dirPinX);
auto stepper2 = AccelStepper(motorInterfaceType, stepPinY, dirPinY);
auto stepper3 = AccelStepper(motorInterfaceType, stepPinZ, dirPinZ);
auto stepper4 = AccelStepper(motorInterfaceType, stepPinA, dirPinA);
AccelStepper* steppers[] = {&stepper1, &stepper2, &stepper3, &stepper4};
EepromManager eepromManager;

long calibrationStepCounter = 0;
int calibrationStepperNumber = 0;
int calibrationMeasureAmountMl = 0;

// rotations to steps
long rpsToSteps(const float rps)
{
    return (360.0f / degreesPerStep) * microSteps * rps;
}

void initStepperWithDefaults(AccelStepper& stepper)
{
    stepper.setEnablePin(stepperEnablePin);
    stepper.setPinsInverted(false, false, true);
    stepper.setMaxSpeed(5000);
    stepper.setAcceleration(stepper.maxSpeed() / 8);
}

bool f01doseAmount(const int stepperNumber, const float doseAmount)
{
    if (stepperNumber < 0 || stepperNumber > 4) return false;

    const long stepsToGo = static_cast<long>(doseAmount * eepromManager.getStepsPerMl());
    debug("Dosing result in steps: ");
    debugln(stepsToGo);
    steppers[stepperNumber - 1]->enableOutputs();
    steppers[stepperNumber - 1]->move(steppers[stepperNumber - 1]->distanceToGo() + stepsToGo);
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

void f03Ping()
{
    Serial.println("PumpsX4");
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

        if (f01doseAmount(stepperNumber, amount))
        {
            debug("Dosing ml: ");
            debugln(amount);
        }
        else
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
    else
    {
        debug("Unknown function number: ");
        debugln(functionNumber);
    }
}

void pollSerial()
{
    if (Serial.available() > 0)
    {
        String input = Serial.readStringUntil('\n');
        parseSerialCommand(input);
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
                break;
            }
        }

        if (mustDisableSteppers)
        {
            stepper1.disableOutputs();
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
    f03Ping();
}

void loop()
{
    runSteppers();
    pollSerial();
}
