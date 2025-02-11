"""
This module interfaces with the OTT Parsivel2 and writes data to text file
before upload to Beehive via Waggle

To display currently available serial ports:
python -m serial.tools.list_ports
"""

import time
import argparse
import csv
import os

from datetime import datetime, timezone
from pathlib import Path

import serial

from waggle.plugin import Plugin

def define_telegram(site):
    """Fuction to define the telegram for the specific site"""
    if site == "adm" or site == "ADM":
        # instrument configured for following telegram:
        #%13;%21;%20;%18;%25;%17;%16;%27;%28;%12;%01;%02;%07;%11;%60;%90;%91;%93
        telegram = ["Timestamp (UTC)",
                    "\tSensor Serial Num (%13)",
                    "\tSensor Date (%21)",
                    "\tSensor Time (%20)", 
                    "\tSensor Status (%18)",
                    "\tError Code (%25)",
                    "\tPower Supply Voltage (%17)",
                    "\tSensor Head Heating Current (%16)",
                    "\tTemperature in the right sensor head (%27)",
                    "\tTemperature in the left sensor head (%28)",
                    "\tSensor Heating Temperature (%12)",
                    "\tRain Intensity (%01)",
                    "\tRain Amount Accumulated (%02)",
                    "\tRadar Reflectivity (%07)",
                    "\tNumber of Particles Validated (%11)",
                    "\tNumber of Particles Detected (%60)",
                    "\tN(d) (%90)",
                    "\tv(d) (%91)",
                    "\tRaw Data (%93)"]
        telegram_units = ["YYYY-MM-DDTHH:MM:SS",
                          "\t#",
                          "\tDD.MM.YYYY",
                          "\thh:mm:ss",
                          "\t#",
                          "\t#",
                          "\tV",
                          "\tA",
                          "\tdegC",
                          "\tdegC",
                          "\tdegC",
                          "\tmm/hr",
                          "\tmm",
                          "\tdBZ",
                          "\t#",
                          "\t#",
                          "\tlog10(1/m3 mm)",
                          "\tm/s",
                          "\t#"]

    elif site == "atmos" or site == "ATMOS":
        # instrument configured for following telegram:
        #%13;%21;%20;%18;%25;%17;%16;%27;%28;%12;%01;%02;%07;%11;%60;%90;%91;%93
        telegram = ["Timestamp (UTC)",
                    "\tSensor Serial Num (%13)",
                    "\tSensor Date (%21)",
                    "\tSensor Time (%20)", 
                    "\tSensor Status (%18)",
                    "\tError Code (%25)",
                    "\tPower Supply Voltage (%17)",
                    "\tSensor Head Heating Current (%16)",
                    "\tTemperature in the right sensor head (%27)",
                    "\tTemperature in the left sensor head (%28)",
                    "\tSensor Heating Temperature (%12)",
                    "\tRain Intensity (%01)",
                    "\tRain Amount Accumulated (%02)",
                    "\tRadar Reflectivity (%07)",
                    "\tNumber of Particles Validated (%11)",
                    "\tNumber of Particles Detected (%60)",
                    "\tN(d) (%90)",
                    "\tv(d) (%91)",
                    "\tRaw Data (%93)"]
        telegram_units = ["YYYY-MM-DDTHH:MM:SS",
                          "\t#",
                          "\tDD.MM.YYYY",
                          "\thh:mm:ss",
                          "\t#",
                          "\t#",
                          "\tV",
                          "\tA",
                          "\tdegC",
                          "\tdegC",
                          "\tdegC",
                          "\tmm/hr",
                          "\tmm",
                          "\tdBZ",
                          "\t#",
                          "\t#",
                          "\tlog10(1/m3 mm)",
                          "\tm/s",
                          "\t#"]
    else:
        # default telegram from the factory
        # %13;%01;%02;%03;%07;%08;%34;%12;%10;%11;%18;
        telegram = ["Timestamp (UTC)",
                    "\tSensor Serial Number (%13)",
                    "\tRain Intensity (%01)",
                    "\tRain Amount Accumulated (%02)",
                    "\tWeather Code SYNOP (%03)",
                    "\tRadar Reflectivity (%07)",
                    "\tMOR Visibilty in Precip (%08)",
                    "\tKinetic Energy (%34)",
                    "\tTemperature in the Sensor Housing (%12)",
                    "\tSignal Amplitude of the laser strip (%10)",
                    "\tNumber of Particles Detected and Validated (%11)",
                    "\tSensor Status (%18)"]
        telegram_units = ["YYYY-MM-DDTHH:MM:SS",
                          "\t#",
                          "\tmm/h",
                          "\tmm",
                          "\t#",
                          "\tdBz",
                          "\tm",
                          "\tJ/(m^2h)",
                          "\tdegC",
                          "\t#",
                          "\t#",
                          "\t#"]

    return telegram, telegram_units

def list_files(img_dir):
    """
    Lists all files within a directory and their sizes in bytes.

    Input:
        dir: The path to the directory to list files from within the DockerFile
            image.
    """
    for fname in os.listdir(img_dir):
        fpath = os.path.join(img_dir, fname)
        print("filepath: ", fpath)
        if os.path.isfile(fpath):
            file_size = os.path.getsize(fpath)
            print(f"{fname}: {file_size} bytes")

def define_filename(site):
    """Function to generate the filename based on the current time"""
    current_time = datetime.now(timezone.utc).strftime('%Y%m%d.%H%M%S')
    return site + '.parsivel2.' + current_time + '.csv'

def main(input_args):
    """Establish Serial Connection and Write Parsivel Data to file"""
    # Initialize the Serial Connection:
    with serial.Serial(input_args.device,
                       input_args.baud_rate,
                       parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE,
                       bytesize=serial.EIGHTBITS,
                       timeout = 1) as ser:
        # Define the Filename for the initial Output file
        nout = define_filename(input_args.site)
        print(f"Initializing Output File: {nout}")
        # Open the file and create the CSV writer
        nfile = open(nout, mode='w', encoding="ascii", newline='')
        writer = csv.writer(nfile, delimiter=';')
        # Write the file header information
        ## NOTE - dependent on telegram programmed into the instrument
        telegram, telegram_units = define_telegram(input_args.site)
        writer.writerow(telegram)
        writer.writerow(telegram_units)
        try:
            last_timestamp = time.gmtime()  # Keep track of the last time we checked
            # check on the files
            print('current path/files: ', list_files('.'))
            while True:
                # Check current time, if past the defined temporal frequency,
                # generate new file
                current_timestamp = time.gmtime()
                if (current_timestamp.tm_min % input_args.freq == 0
                        and current_timestamp.tm_min != last_timestamp.tm_min):
                    # Close the current file and create a new one
                    nfile.close()
                    # Define a new filename
                    current_filename = define_filename(input_args.site)
                    print(f"Switching to a new file: {current_filename}")
                    # Open the new file
                    nfile = open(current_filename,
                                 mode='w',
                                 encoding="ascii",
                                 newline='')
                    writer = csv.writer(nfile, delimiter=';')
                    # Update the last checked time
                    last_timestamp = current_timestamp
                    # Write the file header information
                    writer.writerow(telegram)
                    writer.writerow(telegram_units)
                    # check on the files
                    print('updated path/files: ', list_files('.'))
                # Check the serial connection. If not defined, re-establish.
                try:
                    if ser is None:
                        ser = serial.Serial(input_args.device,
					                        input_args.baud_rate,
					                        parity=serial.PARITY_NONE,
					                        stopbits=serial.STOPBITS_ONE,
					                        bytesize=serial.EIGHTBITS,
					                        timeout = 1)
                        print("Reconnecting Serial Connection")
                    data = ser.readlines()
                    if input_args.verbose:
                        print(datetime.now(timezone.utc).strftime('%Y%m%d.%H%M%S'))
                        print("\n")
                        print(data)
                    if data:
                        # Assemble the output list
                        data_out = [datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')]
                        data_out.extend(data[0].decode('utf-8').strip().split(';'))
                        writer.writerow(data_out)
                        nfile.flush()
                except serial.SerialException:
                    if not ser is None:
                        ser.close()
                        ser = None
                        print("Disconnecting")
                    print("No Connection")
                    time.sleep(2)
        except KeyboardInterrupt:
            print("Program interrupted, closing serial port...")
        finally:
            if ser:
                ser.close()
            nfile.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Script for interfacing with OTT Parsivel2 datastream")

    parser.add_argument("--verbose",
                        action="store_true",
                        dest='verbose',
                        help="Enable Output of Serial Communication to Screen"
                        )
    parser.add_argument("--publish",
                        type=bool,
                        dest="publish",
                        default=True,
                        help="Enable Publishing of Files to Beehive")
    parser.add_argument("--device",
                        type=str,
                        dest='device',
                        default="/dev/ttyUSB1",
                        help="Specific Serial Port for Device Communication"
                        )
    parser.add_argument("--baudrate",
                        type=int,
                        dest='baud_rate',
                        default=19200,
                        help="Baud Rate for Serial Device Communication"
                        )
    parser.add_argument("--format",
                        type=str,
                        dest='output',
                        default="csv",
                        help="output file format (csv or )"
                        )
    parser.add_argument("--frequency",
                        type=int,
                        default=5,
                        dest="freq",
                        help="Temporal Frequency of File Generation"
                        )
    parser.add_argument("--site",
                        type=str,
                        default="atmos",
                        dest="site",
                        help="Site Identifer for Deployment location"
                        )
    args = parser.parse_args()

    main(args)
