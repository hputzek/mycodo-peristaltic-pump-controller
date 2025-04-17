#include "EepromManager.h"
#include <EEPROM.h>

const int EepromManager::MAGIC_NUMBER;

// Constructor
EepromManager::EepromManager()
    : stepsPerMl(0), timePerMl(0), hasLoadedFromEeprom(false), isDirty(false)
{
    // We don't load here to avoid slowing startup
    // Data will load automatically on first get
}

// Destructor - ensure any pending changes are saved
EepromManager::~EepromManager()
{
    if (isDirty) {
        saveToEeprom();
    }
}

// Save the stepsPerMl and timePerMl to EEPROM
void EepromManager::saveToEeprom()
{
    // Save data to EEPROM
    EEPROM.put(EEPROM_ADDR_MAGIC, MAGIC_NUMBER);
    EEPROM.put(EEPROM_ADDR_STEPS_PER_ML, stepsPerMl);
    EEPROM.put(EEPROM_ADDR_TIME_PER_ML, timePerMl);
    
    isDirty = false;
}

// Load the stepsPerMl and timePerMl from EEPROM
void EepromManager::loadFromEeprom()
{
    int magic;
    EEPROM.get(EEPROM_ADDR_MAGIC, magic);

    if (magic != MAGIC_NUMBER)
    {
        // EEPROM is not initialized, set default values
        stepsPerMl = 0;
        timePerMl = 0;

        // Save the default values to EEPROM
        isDirty = true;
        saveToEeprom();
    }
    else
    {
        // Load the saved value from EEPROM
        EEPROM.get(EEPROM_ADDR_STEPS_PER_ML, stepsPerMl);
        EEPROM.get(EEPROM_ADDR_TIME_PER_ML, timePerMl);
    }
    
    hasLoadedFromEeprom = true;
    isDirty = false;
}

// Get the value of stepsPerMl
int EepromManager::getStepsPerMl()
{
    if (!hasLoadedFromEeprom)
    {
        loadFromEeprom();
    }
    return stepsPerMl;
}

// Set the value of stepsPerMl
void EepromManager::setStepsPerMl(int steps)
{
    // Only update and save if the value actually changed
    if (stepsPerMl != steps)
    {
        stepsPerMl = steps;
        isDirty = true;
        saveToEeprom();
    }
}

// Get the value of timePerMl
int EepromManager::getTimePerMl()
{
    if (!hasLoadedFromEeprom)
    {
        loadFromEeprom();
    }
    return timePerMl;
}

// Set the value of timePerMl
void EepromManager::setTimePerMl(int time)
{
    // Only update and save if the value actually changed
    if (timePerMl != time)
    {
        timePerMl = time;
        isDirty = true;
        saveToEeprom();
    }
}