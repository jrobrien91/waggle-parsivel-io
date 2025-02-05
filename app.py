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
    # start serial connection:
    i = 0
    with serial.Serial(args.device,
                       args.baud_rate,
                       parity=serial.PARITY_NONE, 
                       stopbits=serial.STOPBITS_ONE,
                       bytesize=serial.EIGHTBITS,
                       timeout = 2) as ser:
        # Generate the output file
        nout = define_filename(args.site)
        print(nout)
        nfile = open(nout, mode='w', newline='')
        writer = csv.writer(nfile)
        try:
            last_timestamp = time.gmtime()  # Keep track of the last time we checked
            while True:
                # Check if the current time is a multiple of 5 minutes
                current_timestamp = time.gmtime()
                if current_timestamp.tm_min % args.freq == 0 and current_timestamp.tm_min != last_timestamp.tm_min:
                    # Close the current file and create a new one
                    print(f"Switching to a new file: {current_filename}")
                    nfile.close()
                    current_filename = get_csv_filename(args.site)
                    nfile = open(current_filename, mode='w', newline='')
                    writer = csv.writer(nfile)
                    writer.writerow(['Timestamp', 'Data'])  # Header row for the new file
                    last_timestamp = current_timestamp  # Update the last checked time
                try: 
                    if ser == None:
                        ser = serial.Serial(args.device,
					                        args.baud_rate,
					                        parity=serial.PARITY_NONE,
					                        stopbits=serial.STOPBITS_ONE,
					                        bytesize=serial.EIGHTBITS,
					                        timeout = 2)
                        print("Reconnecting Serial Connection")
                    print(i)
                    print("\n")
                    data = ser.readlines()
                    if args.verbose:
                        print(i)
                        print("\n")
                        print(data)
                    if data:
                        writer.writerow([datetime.now(timezone.utc).strftime('%Y%m%d.%H%M%S'), data])
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

