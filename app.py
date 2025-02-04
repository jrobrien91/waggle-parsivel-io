import serial
import time
import argparse
import csv

from datetime import datetime

# To display current ports:
# python -m serial.tools.list_ports

## needs a search ports functionality
    
def main(args):
    # start serial connection:
    print(args.baud_rate)
    i = 0
    with serial.Serial(args.device,
                       args.baud_rate,
                       parity=serial.PARITY_NONE, 
                       stopbits=serial.STOPBITS_ONE,
                       bytesize=serial.EIGHTBITS,
                       timeout = 1) as ser:
        while True:
            print(i)
            print("\n")
            joe = ser.readlines()
            print(joe)
            i += 1

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
                         help="output file format (csv or nc)"
                         )
     parser.add_argument("--frequency",
                         type=int,
                         default=1,
                         dest="freq",
                         help="Temporal frequency of the data aquesition"
                         )
     args = parser.parse_args()

     main(args)

