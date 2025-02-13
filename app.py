"""
This module interfaces with the OTT Parsivel2 and writes data to text file
before upload to Beehive via Waggle

To display currently available serial ports:
python -m serial.tools.list_ports
"""

import time
import argparse
import csv
import threading

from datetime import datetime, timezone
from pathlib import Path

import serial

from waggle.plugin import Plugin, get_timestamp

def define_telegram(site):
    """
    Fuction to define the telegram for the specific site
    
    Parameters
    ----------
    site : str
        Site Identifier to specify instrument configuration

    Output
    ------
    telegram : list (str)
        Parameter descriptions for the instrument configuration
    telegram_units : list (str)
        Parameter units for the instrument configuration
    publish_list : list (int)
        Integers of parameters to keep to publish to beehive separately from
        the csv files.
    publish_parms : list (str)
        Short names of parameters to publish to beehive.
    """
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
        publish_list = [4, 5, 6, 11, 12, 13]
        publish_parms = ["parsivel.house.status",
                         "parsivel.house.error",
                         "parsivel.house.voltage",
                         "parsivel.rain.intensity",
                         "parsivel.rain.accum",
                         "parsivel.radar"]
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
        publish_list = [4, 5, 6, 11, 12, 13]
        publish_parms = ["parsivel.house.status",
                         "parsivel.house.error",
                         "parsivel.house.voltage",
                         "parsivel.rain.intensity",
                         "parsivel.rain.accum",
                         "parsivel.radar"]
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
        publish_list = [2, 3, 5, 8, 11]
        publish_parms = ["parsivel.rain.intensity",
                         "parsivel.rain.accum",
                         "parsivel.radar",
                         "parsivel.house.temp",
                         "parsivel.house.status"]

    return telegram, telegram_units, publish_list, publish_parms

def list_files(img_dir):
    """
    Lists all files within a directory and their sizes in bytes.

    Parameters:
        img_dir: The path to the directory to list files from within
            the DockerFile image.
    """
    dir_path = Path(img_dir)
    saved_files = sorted(list(dir_path.glob("*.csv")))
    if saved_files:
        print('updated path/files: ')
        for sfile in saved_files:
            file_size = sfile.stat().st_size
            print(f"{sfile}: {file_size} bytes")

def define_filename(site, outdir):
    """Function to generate the filename based on the current time"""
    nout = (site +
            '.parsivel2.' +
            datetime.now(timezone.utc).strftime("%Y%m%d.%H%M%S") +
            '.csv')
    # Define the Path to the CSV file
    csv_path = Path(outdir) / nout
    # Ensure the parent directory exists
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    return csv_path

def publish_file(file_path):
    """Utilizing threading, publish file to Beehive"""
    def upload_file(file_path):
        """Call the Waggle Plugin"""
        with Plugin() as plugin:
            plugin.upload_file(file_path, timestamp=get_timestamp())
            print(f"Published {file_path}")
    # Define threads
    thread = threading.Thread(target=upload_file, args=(file_path,))
    thread.start()
    thread.join()

def main(input_args):
    """Establish Serial Connection and Write Parsivel Data to file"""

    # Initialize the Serial Connection:
    with serial.Serial(input_args.device,
                       input_args.baud_rate,
                       parity=serial.PARITY_NONE,
                       stopbits=serial.STOPBITS_ONE,
                       bytesize=serial.EIGHTBITS,
                       timeout = 1) as ser:
        print(f"Serial connection to {input_args.device} is open")
        # Define the Filename for the initial Output file
        csv_path = define_filename(input_args.site, input_args.outdir)
        # Open the file
        nfile = open(csv_path, mode='w', encoding="ascii", newline='')
        writer = csv.writer(nfile, delimiter=';')
        print(f"Initializing file: {nfile.name}")
        # Write the file header information
        ## NOTE - dependent on telegram programmed into the instrument
        telegram, telegram_units, publish_list, publish_parms = define_telegram(input_args.site)
        writer.writerow(telegram)
        writer.writerow(telegram_units)
        try:
            last_timestamp = time.gmtime()  # Keep track of the last time we checked
            while True:
                # Check current time, if past the defined temporal frequency,
                # generate new file
                current_timestamp = time.gmtime()
                if (current_timestamp.tm_min % input_args.freq == 0
                        and current_timestamp.tm_min != last_timestamp.tm_min):
                    # Close the current file and create a new one
                    nfile.close()
                    # if desired, check on current files and file sizes
                    if input_args.verbose:
                        # check on the files
                        list_files(input_args.outdir)
                   # Upload file via Waggle
                    publish_file(nfile.name)
                    # Define a new filename
                    csv_path = define_filename(input_args.site, input_args.outdir)
                    # Open the new file
                    nfile = open(csv_path, mode='w', encoding="ascii", newline='')
                    writer = csv.writer(nfile, delimiter=';')
                    print(f"Initializing new file: {nfile.name}")
                    # Write the file header information
                    writer.writerow(telegram)
                    writer.writerow(telegram_units)
                    # Update the last checked time
                    last_timestamp = current_timestamp
                # Check the serial connection. If not defined, re-establish.
                try:
                    if ser is None:
                        ser = serial.Serial(input_args.device,
					                        input_args.baud_rate,
					                        parity=serial.PARITY_NONE,
					                        stopbits=serial.STOPBITS_ONE,
					                        bytesize=serial.EIGHTBITS,
					                        timeout = 1)
                        print(f"Reconnecting Serial Connection with {input_args.device}")
                    # Read data from the instrument
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
                        # If select parameter publishing is desired, upload via Waggle
                        if input_args.publish:
                            # Publish to the node
                            with Plugin() as plugin:
                                i = 0
                                for parm in publish_list:
                                    plugin.publish(publish_parms[i],
                                                   value=data_out[parm],
                                                   meta={"units" : telegram_units[parm],
                                                         "sensor" : "parsivel2",
                                                         "description" : telegram[parm],
                                                   },
                                                   scope="node",
                                                   timestamp=get_timestamp()
                                    )
                                    i += 1

                except serial.SerialException:
                    if not ser is None:
                        ser.close()
                        ser = None
                        print(f"Disconnecting from serial port {input_args.device}")
                    print(f"No Connection with serial port {input_args.device}")
                    time.sleep(2)
        except KeyboardInterrupt:
            print(f"Program interrupted, closing serial port {input_args.device}")
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
                        default=False,
                        help=("[Boolean|Default False] Enable Publishing " +
                              "of Select Parameters to Beehive")
                        )
    parser.add_argument("--device",
                        type=str,
                        dest='device',
                        default="/dev/ttyUSB1",
                        help="[str] Specific Serial Port for Device Communication"
                        )
    parser.add_argument("--baudrate",
                        type=int,
                        dest='baud_rate',
                        default=19200,
                        help="[int] Baud Rate for Serial Device Communication"
                        )
    parser.add_argument("--format",
                        type=str,
                        dest='output',
                        default="csv",
                        help="[str] output file format (csv or )"
                        )
    parser.add_argument("--freq",
                        type=int,
                        default=5,
                        dest="freq",
                        help="[int] Temporal Frequency of File Generation"
                        )
    parser.add_argument("--site",
                        type=str,
                        default="atmos",
                        dest="site",
                        help="[str] Site Identifer for Deployment location"
                        )
    parser.add_argument("--outdir",
                        type=str,
                        dest="outdir",
                        default=".",
                        help="[str] Directory where to output files to"
                        )
    args = parser.parse_args()

    main(args)
