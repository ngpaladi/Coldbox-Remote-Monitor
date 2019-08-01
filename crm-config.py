import py2700 as RM
import CoolingSystem as CS
import time
from datetime import datetime
import os
import sys
import subprocess
import argparse
import webbrowser
import atexit
from pathlib import Path
import json

# Important Info
__version__ = "1.0.0"


# Functions

def InvalidFilename(input_str) -> bool:
    if (input_str.find(' ') != -1 or input_str.find('$') != -1 or input_str.find('%') != -1 or input_str.find('*') != -1):
        return True
    try:
        print(Path(input_str))
        if str(Path(input_str).name) == str(Path(input_str)):
            return False
        if not os.path.isdir(os.path.dirname(Path(input_str).folder)):
            print('WARNING: Folder Does Not Exist!')
            return True
        return False
    except:
        print("Issue making path")
        return True


def InvalidIP(s):
    a = s.split('.')
    if len(a) != 4:
        return True
    for x in a:
        if not x.isdigit():
            return True
        i = int(x)
        if i < 0 or i > 255:
            return True
    return False



def read(args):
    # Load in configuration
    with open(Path(args.file)) as config_file:
        config = CS.CoolingSystemConfig.FromJSON(config_file)
    if not isinstance(config, CS.CoolingSystemConfig):
        raise Exception("Invalid Configuration: Wrong file type")
    print(config)


def create(args):
    # Load in paths
    config_filename = Path(args.file)

    # Check if configuration exist
    if config_filename.exists():
        print('WARNING: Configuration File Exists!')

    while True:
        if config_filename.exists():
            confirm_str = str(input("Want to overwrite? (Y/n): "))
            confirm_str = confirm_str.lower()
            if confirm_str == "n" or confirm_str == "no":
                input_filename_str = str(
                    input("Please enter the name for this configuration file (e.g. Room303.cfg): "))
                while (InvalidFilename(input_filename_str)):
                    input_filename_str = str(
                        input("Please try again, with no spaces or weird characters: "))
                config_filename = Path(input_filename_str)
            elif confirm_str == "y" or confirm_str == "yes":
                for x in range(6):
                    print('Overwriting in ' + str(5-x) + ' seconds', end='\r')
                    time.sleep(1)
                print('\nOverwriting...')
                break
            else:
                print("Invalid input")
        else:
            break

    print("\n\n")

    # Get IP and Port

    ip = str(input("Please enter the device IP address (IPv4): "))

    while InvalidIP(ip):
        ip = str(input("Not an IPv4 address, please try again: "))

    while True:
        try:
            port = int(input("Please enter the device SCPI port (Probably 1394): "))
            break
        except ValueError:
            print("Not an integer, please try again")

    print("\n")

    pres_supply=0.0

    while True:
        try:
            pres_supply = float(input("Please enter the pressure channel supply voltage: "))
            break
        except ValueError:
            print("Not an number, please try again: ")
    print("\n")

    thermist_channels = []
    thermcpl_channels = []
    pres_channels = []

    while True:
        while True:
            try:
                thermist_channels = list(map(int,input(
                    "Please enter the thermistor channels with spaces between (i.e. 102 103 104): ").strip().split()))
                for ch in thermist_channels:
                    if ch < 102 or ch > 240 or (ch < 202 and ch > 140) or ch == 121 or ch == 221:
                        print("Channel outside range or reserved (like 101, 121, 201, and 221)")
                        continue
                break
            except:
                print("Invalid channel list. Please try again: ")

        while True:
            try:
                thermcpl_channels = list(map(int,input(
                    "Please enter the thermocouple channels with spaces between (i.e. 102 103 104): ").strip().split()))
                for ch in thermcpl_channels:
                    if ch < 102 or ch > 240 or (ch < 202 and ch > 140) or ch == 211 or ch == 111:
                        print("Channel outside range or reserved (like 101, 111, 201, and 211)")
                        continue
                break
            except:
                print("Invalid channel list. Please try again: ")

        while True:
            try:
                pres_channels = list(map(int,input(
                    "Please enter the pressure channels with spaces between (i.e. 102 103 104): ").strip().split()))
                for ch in pres_channels:
                    if ch < 102 or ch > 240 or (ch < 202 and ch > 140) or ch == 211 or ch == 111:
                        print("Channel outside range or reserved (like 101, 111, 201, and 211)")
                        continue
                break
            except:
                print("Invalid channel list. Please try again: ")

        overlap = False

        for ts in thermist_channels:
            for tc in thermcpl_channels:
                for p in pres_channels:
                    if (ts == p) or (ts == tc) or (tc == p):
                        overlap = True
        if overlap:
            print("A channel is set twice, please retry")
            continue
        break

    # Create Pairs

    channel_pairs = []
    print("\n")

    while True:

        while True:
            try:
                pairs_question = int(input("How many channel pairs do you want to make? "))
                break
            except ValueError:
                print("ERROR: Not an integer!")
                continue
        
        if pairs_question <= 0:
            print("No channel pairs will be created")
            break

        for i in range(pairs_question):
            print("\n")
            pair_name = str(input("Name of Pair: "))
            while True:
                try: 
                    pair_temp = int(input("Thermocouple Channel: "))
                    if not pair_temp in thermcpl_channels:
                        print("Not a thermocouple channel!")
                        continue
                    break
                except ValueError:
                    print("Not a channel number!")
                    continue
                
            while True:
                try: 
                    pair_pres = int(input("Pressure Channel: "))
                    if not pair_pres in pres_channels:
                        print("Not a pressure channel!")
                        continue
                    break
                except ValueError:
                    print("Not a channel number!")
                    continue
            
            channel_pairs.append(CS.ChannelPair(
                pair_name, pair_temp, pair_pres))
        break

    # Create Config Object

    config = CS.CoolingSystemConfig(
        ip, port, thermcpl_channels,thermist_channels, "C", pres_channels, "bar", pres_supply, channel_pairs)
    with open(config_filename, "w+") as f:
        config.WriteJSON(f)

    print("\n\n---------------------\n\n         Done!         \n\n---------------------\n\n")




# Parse Arguments


parser = argparse.ArgumentParser(
    description='Configuration generator and viewer for the crm program')
subparsers = parser.add_subparsers()
create_parser = subparsers.add_parser(
    "create", help='Create a configuration file')
read_parser = subparsers.add_parser("read", help='Read a configuration file')
create_parser.add_argument("file", action="store",
                           default="", help="Give the name of the output file")
read_parser.add_argument("file", action="store", default="",
                         help="Give the name of the input file to read")
parser.add_argument('--version', action='version',
                    version='%(prog)s '+__version__)

read_parser.set_defaults(func=read)
create_parser.set_defaults(func=create)

# Print Welcome Info

print('---------------------\n\n   CRM Config '+__version__ +
      '  \n\n    Noah Paladino    \n        2019         \n\n---------------------\n')


args = parser.parse_args()
print(args)
if hasattr(args, 'func'):
    args.func(args)
else:
    parser.print_usage()

