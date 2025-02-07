import serial
import time
import argparse
import csv

from datetime import datetime, timezone

# To display current ports:
# python -m serial.tools.list_ports

# Function to generate the filename based on the current time
def define_filename(site):
    current_time = datetime.now(timezone.utc).strftime('%Y%m%d.%H%M%S')
    return site + '.parsivel2.' + current_time + '.csv'
    
def main(args):
    # Initialize the Serial Connection:
    i = 0
    with serial.Serial(args.device,
                       args.baud_rate,
                       parity=serial.PARITY_NONE, 
                       stopbits=serial.STOPBITS_ONE,
                       bytesize=serial.EIGHTBITS,
                       timeout = 1) as ser:
        # Define the Filename for the initial Output file
        nout = define_filename(args.site)
        print(f"Initializing Output File: {nout}")
        # Open the file and create the CSV writer
        nfile = open(nout, mode='w', newline='')
        writer = csv.writer(nfile, delimiter=';')
        # Write the file header information
        ## NOTE - dependent on telegram programmed into the instrument
        telegram = ["Timestamp",
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
        writer.writerow(telegram)
        writer.writerow(telegram_units)
        try:
            last_timestamp = time.gmtime()  # Keep track of the last time we checked
            while True:
                # Check current time, if past the define frequency, generate new file
                current_timestamp = time.gmtime() 
                if current_timestamp.tm_min % args.freq == 0 and current_timestamp.tm_min != last_timestamp.tm_min:
                    # Close the current file and create a new one
                    nfile.close()
                    # Define a new filename
                    current_filename = define_filename(args.site)
                    print(f"Switching to a new file: {current_filename}")
                    # Open the new file
                    nfile = open(current_filename, mode='w', newline='')
                    writer = csv.writer(nfile, delimiter=';')
                    # Update the last checked time
                    last_timestamp = current_timestamp
                    # Write the file header information
                    writer.writerow(telegram)
                    writer.writerow(telegram_units)
                # Check the serial connection. If not defined, re-establish.
                try: 
                    if ser == None:
                        ser = serial.Serial(args.device,
					                        args.baud_rate,
					                        parity=serial.PARITY_NONE,
					                        stopbits=serial.STOPBITS_ONE,
					                        bytesize=serial.EIGHTBITS,
					                        timeout = 1)
                        print("Reconnecting Serial Connection")
                    data = ser.readlines()
                    if args.verbose:
                        print(i, datetime.now(timezone.utc).strftime('%Y%m%d.%H%M%S'))
                        print("\n")
                        print(data)
                    if data:
                        # Assemble the output list
                        data_out = [datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')]
                        data_out.extend(data[0].decode('utf-8').strip().split(';'))
                        writer.writerow(data_out)
                        nfile.flush()
                    i += 1
                except:
                    if(not(ser == None)):
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

