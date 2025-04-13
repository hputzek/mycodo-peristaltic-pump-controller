#ifndef EepromManager_h
#define EepromManager_h

class EepromManager
{
public:
    EepromManager();
    void saveToEeprom() const;
    void loadFromEeprom();

    int getStepsPerMl();
    void setStepsPerMl(int steps);
    int getTimePerMl();
    void setTimePerMl(int time);

private:
    static const int MAGIC_NUMBER = 0x1234; // Magic number to check if EEPROM is initialized
    static const int EEPROM_ADDR_MAGIC = 0;
    static const int EEPROM_ADDR_STEPS_PER_ML = 4;
    static const int EEPROM_ADDR_TIME_PER_ML = 8;

    int stepsPerMl;
    int timePerMl;
    bool hasLoadedFromEeprom;
};

#endif