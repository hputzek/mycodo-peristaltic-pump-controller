//
// Created by Hendrik Putzek on 29.09.24.
//

#include <AccelStepper.h>

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

float rpsToSteps(const float rps)
{
    return (360.0f / degreesPerStep) * microSteps * rps;
}

void initStepperWithDefaults(AccelStepper& stepper)
{
    stepper.setEnablePin(stepperEnablePin);
    stepper.setPinsInverted(false, false, true);
    stepper.setMaxSpeed(5000);
    stepper.setAcceleration(stepper.maxSpeed() / 2);
    stepper.enableOutputs();
}

void setup()
{
    debug_begin(9600);
    for (auto& stepper : steppers)
    {
        initStepperWithDefaults(*stepper);
    }
    stepper2.moveTo(rpsToSteps(5));
    stepper1.moveTo(rpsToSteps(6));
    stepper3.moveTo(rpsToSteps(3));
    stepper4.moveTo(rpsToSteps(1));
}

void loop()
{
    for (auto& stepper : steppers)
    {
        while (stepper->distanceToGo() != 0)
        {
            stepper->run();
        }
        if (stepper->distanceToGo() == 0)
        {
            stepper->moveTo(-stepper->currentPosition());
            debugln("Revert position");
        }
    }
}
