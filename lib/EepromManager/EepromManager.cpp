#include "EepromManager.h"
#include <EEPROM.h>

const int EepromManager::MAGIC_NUMBER;

// Constructor
EepromManager::EepromManager()
    : stepsPerMl(0), hasLoadedFromEeprom(false)
{
}

// Save the stepsPerMl to EEPROM
void EepromManager::saveToEeprom() const
{
    EEPROM.put(EEPROM_ADDR_MAGIC, MAGIC_NUMBER);
    EEPROM.put(EEPROM_ADDR_STEPS_PER_ML, stepsPerMl);
}

// Load the stepsPerMl from EEPROM
void EepromManager::loadFromEeprom()
{
    int magic;
    EEPROM.get(EEPROM_ADDR_MAGIC, magic);

    if (magic != MAGIC_NUMBER)
    {
        // EEPROM is not initialized, set default values
        stepsPerMl = 0;

        // Save the default values to EEPROM
        saveToEeprom();
    }
    else
    {
        // Load the saved value from EEPROM
        EEPROM.get(EEPROM_ADDR_STEPS_PER_ML, stepsPerMl);
    }
}

// Get the value of stepsPerMl
int EepromManager::getStepsPerMl()
{
    if (!hasLoadedFromEeprom)
    {
        hasLoadedFromEeprom = true;
        loadFromEeprom();
    }
    return stepsPerMl;
}

// Set the value of stepsPerMl
void EepromManager::setStepsPerMl(int steps)
{
    stepsPerMl = steps;
    saveToEeprom();
}
