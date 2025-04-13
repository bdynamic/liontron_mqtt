#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pexpect


import subprocess
import os
import json
import argparse
import pexpect
import logging

class Battery:
    def __init__(self, MAC):
        self._MAC = MAC
        self._raw_data = None

    def __getBMSData(self):
        child = pexpect.spawn("gatttool -I -b " + self._MAC)

        for attempt in range(10):
            try:
                logging.debug(f"BMS connecting (Try: {attempt+1})")  
                child.sendline("connect")
                child.expect("Connection successful", timeout=1)
            except pexpect.TIMEOUT:
                continue
            else:
                logging.debug("BMS connection successful")  
                break
        else:
            logging.debug("BMS Connect timeout! Exit")  
            child.sendline("exit")
            return -1

        # Get main status data (voltage, current, SoC, etc.)
        for attempt in range(10):
            try:
                resp = b''
                child.sendline("char-write-req 0x0015 dda50300fffd77")
                child.expect("Notification handle = 0x0011 value: ", timeout=1)
                child.expect("\r\n", timeout=0)
                resp += child.before
                child.expect("Notification handle = 0x0011 value: ", timeout=1)
                child.expect("\r\n", timeout=0)
                resp += child.before
            except pexpect.TIMEOUT:
                continue
            else:
                break
        else:
            resp = b''

        # Get per-cell voltages
        for attempt in range(10):
            try:
                resp2 = b''
                child.sendline("char-write-req 0x0015 dda50400fffc77")
                child.expect("Notification handle = 0x0011 value: ", timeout=1)
                child.expect("\r\n", timeout=0)
                resp2 += child.before
            except pexpect.TIMEOUT:
                continue
            else:
                break
        else:
            resp2 = b''

        # Get BMS name (ASCII encoded)
        for attempt in range(10):
            try:
                resp3 = b''
                child.sendline("char-write-req 0x0015 dda50500fffb77")
                child.expect("Notification handle = 0x0011 value: ", timeout=1)
                child.expect("\r\n", timeout=0)
                resp3 += child.before
            except pexpect.TIMEOUT:
                continue
            else:
                break
        else:
            resp3 = b''

        # Close BLE connection
        child.sendline("disconnect")
        child.sendline("exit")

        # Process received data
        resp = resp[:-1]
        resp2 = resp2[:-1]
        resp3 = resp3[:-1]

        response = bytearray.fromhex(resp.decode())
        response2 = bytearray.fromhex(resp2.decode())
        response3 = bytearray.fromhex(resp3.decode())

        rawdat = {}

        # Decode main status message
        if response.endswith(b'w') and response.startswith(b'\xdd\x03'):
            response = response[4:]

            rawdat['Vmain'] = int.from_bytes(response[0:2], 'big', signed=True) / 100.0
            rawdat['Imain'] = int.from_bytes(response[2:4], 'big', signed=True) / 100.0
            rawdat['RemainAh'] = int.from_bytes(response[4:6], 'big', signed=True) / 100.0
            rawdat['NominalAh'] = int.from_bytes(response[6:8], 'big', signed=True) / 100.0
            rawdat['NumberCycles'] = int.from_bytes(response[8:10], 'big')
            rawdat['ProtectState'] = int.from_bytes(response[16:18], 'big')
            rawdat['ProtectStateBin'] = format(rawdat['ProtectState'], '016b')
            rawdat['SoC'] = response[19]
            rawdat['TempC1'] = (int.from_bytes(response[23:25], 'big', signed=True) - 2731) / 10.0
            rawdat['TempC2'] = (int.from_bytes(response[25:27], 'big', signed=True) - 2731) / 10.0

            # Decode protection state text
            psb = rawdat['ProtectStateBin']
            if psb.startswith('0000000000000'):
                rawdat['ProtectStateText'] = "ok"
            elif psb[0] == "1":
                rawdat['ProtectStateText'] = "CellBlockOverVolt"
            elif psb[1] == "1":
                rawdat['ProtectStateText'] = "CellBlockUnderVol"
            elif psb[2] == "1":
                rawdat['ProtectStateText'] = "BatteryOverVol"
            elif psb[3] == "1":
                rawdat['ProtectStateText'] = "BatteryUnderVol"
            elif psb[4] == "1":
                rawdat['ProtectStateText'] = "ChargingOverTemp"
            elif psb[5] == "1":
                rawdat['ProtectStateText'] = "ChargingLowTemp"
            elif psb[6] == "1":
                rawdat['ProtectStateText'] = "DischargingOverTemp"
            elif psb[7] == "1":
                rawdat['ProtectStateText'] = "DischargingLowTemp"
            elif psb[8] == "1":
                rawdat['ProtectStateText'] = "ChargingOverCurrent"
            elif psb[9] == "1":
                rawdat['ProtectStateText'] = "DischargingOverCurrent"
            elif psb[10] == "1":
                rawdat['ProtectStateText'] = "ShortCircuit"
            elif psb[11] == "1":
                rawdat['ProtectStateText'] = "ForeEndICError"
            elif psb[12] == "1":
                rawdat['ProtectStateText'] = "MOSSoftwareLockIn"

        # Decode cell voltages
        if response2.endswith(b'w') and response2.startswith(b'\xdd\x04'):
            response2 = response2[4:-3]
            for cell in range(len(response2) // 2):
                rawdat[f'Vcell{cell+1}'] = int.from_bytes(response2[cell*2:cell*2+2], 'big') / 1000.0

        # Decode name
        if response3.endswith(b'w') and response3.startswith(b'\xdd\x05'):
            response3 = response3[4:-3]
            rawdat['Name'] = response3.decode("ASCII")

        # store
        self._raw_data = rawdat

    def getBatteryload(self):
        """
        Public method to retrieve all battery data from the BMS directly.

        Returns:
            dict: Battery data dictionary if available, or an error dictionary on failure.
        """
        if self.__getBMSData() == -1:
            return {"error": "Failed to retrieve data from BMS"}

        return self._raw_data if hasattr(self, "_raw_data") else {"error": "No data available"}


    def __del__(self):
        """
        Destructor for cleanup if needed.
        """
        return



def main() -> None:
    """
    Main function to test the library
    """
    logging.basicConfig(level=logging.DEBUG) 
    MAC = "A4:AA:BB:CC:DD:EE"  #100Ah
    bat1 = Battery(MAC)
    logging.debug(bat1.getBatteryload()) 


if __name__ == "__main__":
    main()