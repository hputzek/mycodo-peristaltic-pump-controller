#ifndef EEPROM_MANAGER_H
#define EEPROM_MANAGER_H

class EepromManager {
private:
    int stepsPerMl;
    bool hasLoadedFromEeprom;

    static const int EEPROM_ADDR_MAGIC = 0;
    static const int EEPROM_ADDR_STEPS_PER_ML = 4;
    static const int MAGIC_NUMBER = 0x1234;

public:
    explicit EepromManager();
    void saveToEeprom() const;
    void loadFromEeprom();

    int getStepsPerMl();
    void setStepsPerMl(int steps);
};

#endif // EEPROM_MANAGER_H