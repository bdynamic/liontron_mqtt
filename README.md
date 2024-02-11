# Liontron-BMS-BLE-Reader

This Python script reads data from a Liontron BMS over BLE and stores it in a JSON file. It also calculates the battery load and stores it in the database.

## Requirements

* Python 3.x
* `pexpect` library
* `neopixel` library
* `readConfig` library (not provided in the code)
* A Raspberry Pi or other compatible device with Bluetooth LE

## Setup

1. Install the required libraries:


pip install pexpect neopixel


2. Replace the `readConfig` library with your own implementation to read configuration values such as the MAC address of the BMS.

3. Configure the script with your desired settings, such as the pin for the LED indicator.

## Usage

1. Run the script:

bash
python Liontron_BMS_Reader.py


2. The script will connect to the BMS, read data, and store it in a file called `data.json`. The battery load will also be calculated and stored in the database.

## LED Indicator

The script uses an LED to indicate the battery level. The LED will be:

* Green: Battery level is above 80%
* Yellow: Battery level is between 50% and 80%
* Red: Battery level is below 50%

## Data

The script stores the following data in the `data.json` file:

* Vmain: Total battery voltage (V)
* Imain: Battery current (A)
* RemainAh: Remaining battery capacity (Ah)
* NominalAh: Nominal battery capacity (Ah)
* NumberCycles: Number of charge cycles
* ProtectState: Protection state (binary)
* ProtectStateText: Protection state text
* SoC: Battery level (%)
* TempC1: Temperature of cell 1 (°C)
* TempC2: Temperature of cell 2 (°C)
* Vcell1: Voltage of cell 1 (V)
* Vcell2: Voltage of cell 2 (V)
* ... (voltages of all cells)
* Name: Name of the BMS

## Database

The script stores the battery load in a database. The specific database implementation is not provided in the code and needs to be implemented separately.

## Disclaimer

This code is provided for informational purposes only and should not be used in critical applications without proper testing and validation.


I hope this is helpful!
