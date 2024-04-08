# Liontron-BMS-BLE-Reader

This Python script reads data from a Liontron BMS over BLE and stores it in a JSON file. It also calculates the battery load and stores it in the database.

## Requirements

* Python 3.x
* `pexpect` library
* A Raspberry Pi or other compatible device with Bluetooth LE

## Setup

1. Install the required libraries:



- pip install pexpect

2. Retrieve the MAC address of the battery
    


## Usage

1. Include the script:

from battery import Battery


2. The script will connect to the BMS, read data, and store it in a file called `data.json`. The battery load will also be calculated and stored in the database.


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


## Disclaimer

This code is provided for informational purposes only and should not be used in critical applications without proper testing and validation.


I hope this is helpful!
