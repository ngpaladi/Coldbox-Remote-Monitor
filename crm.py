import RemoteMultimeter as RM
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

# Important Info
__version__ = "0.1.0"


# Settings
default_csv_filename = "Run_"+str(int(time.time()))+".csv"
time_interval = 5  # s
start_delay = 10  # s

# Functions

def now():
    return time.time_ns() / (10 ** 9)


# Parse Arguments

parser = argparse.ArgumentParser(
    description='Collect data from a Keithley 2701 Multimeter and monitor using a web page')
parser.add_argument("-c", "--config", action="store", default="cfg/default.cfg",
                    dest="config_filename", help="Specify the configuration file")
parser.add_argument("-o", "--output", action="store", default=default_csv_filename,
                    dest="csv_filename", help="Give the name of the output file")
parser.add_argument('--version', action='version',
                    version='%(prog)s '+__version__)
results = parser.parse_args()

if not os.path.exists("csv"):
    os.makedirs("csv")

# Load in paths

config_filename = Path(results.config_filename)
csv_filename = Path("csv/"+str(Path(results.csv_filename).name))

# Print Welcome Info

print('---------------------\n\n      CRM '+__version__ +
      '      \n\n    Noah Paladino    \n        2019         \n\n---------------------\n')
print('Settings:\n\nConfiguration: '+str(Path(results.config_filename)) +
      '\nData Storage: '+str(csv_filename)+'\n\n---------------------')

# Check if CSV and configuration exist

if csv_filename.exists():
    print('WARNING: Output File Exists!')
    for x in range(5):
        print('Overwriting in' + str(5-x) + 'seconds', end='\r')
        time.sleep(1)
    print('Overwriting...')

if not config_filename.is_file():
    config_filename = Path("config") / config_filename.name
    print("Couldn't find it, trying " + str(config_filename))

if not config_filename.is_file():
    raise Exception("Invalid Configuration: File does not exist")

# Load in configuration
with open(config_filename) as config_file:
    config = CS.CoolingSystemConfig.FromJSON(config_file)
if not isinstance(config, CS.CoolingSystemConfig):
    raise Exception("Invalid Configuration: Wrong file type")

# Delete old json states
if os.path.exists(Path("web/CoolingSystemState.json")):
    os.remove(Path("web/CoolingSystemState.json"))
    print("Old State Removed...")
if os.path.exists(Path("web/CoolingSystemSetup.json")):
    os.remove(Path("web/CoolingSystemSetup.json"))
    print("Old Setup Removed...")


# Connect to multimeter

dmm = RM.RemoteMultimeter(config.ip_address, config.port)
dmm.connect()
dmm.setThermocoupleChannels(
    config.thermocouple_channels, config.temperature_units)
dmm.setThermistorChannels(
    config.thermistor_channels, config.temperature_units)
dmm.setPressureChannels(config.pressure_channels, config.pressure_units)
dmm.setupChannels()
print(dmm)

# Do test scan
baseline = dmm.scan(0)

# Print out csv header
with open(str(csv_filename), "w") as csv_file:
    csv_file.write(dmm.makeCsvHeader())

# Figure out how long the timing process takes to fine tune the delay

time_a = time.time_ns()
temp_time1 = time.time_ns()
temp_time2 = time.time_ns()
temp_time_elapsed = (temp_time2-temp_time1) / (10 ** 9)
time_b = time.time_ns()
fine_tune_time = (time_b-time_a) / (10 ** 9)

# Figure out the start time

start_time = now() + start_delay
print('\nStart Time:\n'+str(start_time)+'\n' +
      str(datetime.utcfromtimestamp(int(start_time)).strftime('%Y-%m-%d %H:%M:%S')))
dmm.display("WAITING")

# Load and write the setup

setup = CS.CoolingSystemSetup(
    config, start_time, "./csv/"+str(csv_filename.name))
setup.WriteJSON()
time.sleep(0.25*start_delay)

# Start monitoring webpage
p1 = subprocess.Popen("python -m http.server 8888")
webbrowser.open("http://127.0.0.1:8888", 1)


# Set up exit handler for when we kill loop
def exit_handler():
    dmm.display("DONE")
    p1.terminate()
    p1.wait()
    dmm.disconnect()


atexit.register(exit_handler)

# Loop counter
index = 0

# Wait for proper time
while now() < start_time:
    time.sleep(0.05)

while 1:
    t1 = time.time_ns()
    timestamp = now() - start_time
    result = dmm.scan(timestamp)
    print(result.raw_result)
    with open(str(csv_filename), "a") as csv_file:
        csv_file.write(result.makeCsvRow())
    state = CS.CoolingSystemState(setup, result)
    state.WriteJSON(index)
    index += 1
    t2 = time.time_ns()
    scan_time_elapsed = (t2-t1) / (10 ** 9)

    time.sleep(time_interval-scan_time_elapsed-fine_tune_time)
