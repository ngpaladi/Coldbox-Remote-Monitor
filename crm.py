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

# Important Info
__version__ = "0.1.1"


# Settings
default_csv_filename = "Run_"+str(int(time.time()))+".csv"
time_interval = 5  # s
start_delay = 10  # s
junction_thermistor_shift = 0.716 # degrees C

# Functions

def now():
    return time.time_ns() / (10 ** 9)
    
def guarantee_over_zero(f:float):
    if f < float(0):
        return float(0)
    else:
        return f


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

# Make sure you run from the directory you cloned this into, otherwise web server will crash
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
    config_filename = Path("cfg") / config_filename.name
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
dmm = RM.Multimeter('TCPIP::'+str(config.ip_address) +
                    '::'+str(config.port)+'::SOCKET')
# Set the default temperature units
dmm.set_temperature_units(config.temperature_units)

# Set the timeout in ms
dmm.set_timeout(5000)

dmm.define_channels([101], RM.MeasurementType.thermistor(2252))

dmm.define_channels(
    config.thermocouple_channels, RM.MeasurementType.thermocouple('K', 'EXT'))
dmm.define_channels(config.thermistor_channels,
                    RM.MeasurementType.thermistor(2252))
dmm.define_channels(config.pressure_channels, RM.MeasurementType.dc_voltage())
dmm.setup_scan()
print(dmm)

# Do test scan
baseline = dmm.scan(0)

# Turn Voltages to Pressures
for ch in config.pressure_channels:
    baseline.readings[ch].value = CS.VoltageToPressure(baseline.readings[ch].value,config.pressure_supply_voltage)
    baseline.readings[ch].unit = "bar"

# Print out csv header
with open(str(csv_filename), "w") as csv_file:
    csv_file.write(baseline.make_csv_header())

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
    config, start_time, str(csv_filename))
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

    # Shift thermocouple readings after calibrating the thermistor that determines junction temperature
    result.readings[101].value = result.readings[101].value + junction_thermistor_shift
    for ch in config.thermocouple_channels:
        result.readings[ch].value = result.readings[ch].value + junction_thermistor_shift


    # Turn Voltages to Pressures
    for ch in config.pressure_channels:
        result.readings[ch].value = CS.VoltageToPressure(result.readings[ch].value,config.pressure_supply_voltage)
        result.readings[ch].unit = "bar"
    
    # Write CSV row
    with open(str(csv_filename), "a") as csv_file:
        csv_file.write(result.make_csv_row())
    
    # Write state for browser to read
    state = CS.CoolingSystemState(setup, result)
    state.WriteJSON(index)

    print('Reading Number: ' + str(index), end='\r')
    index += 1
    t2 = time.time_ns()
    scan_time_elapsed = (t2-t1) / (10 ** 9)

    #Sleep appropriate amount to ensure loop takes exactly 5 seconds
    time.sleep(guarantee_over_zero(time_interval-scan_time_elapsed-fine_tune_time))
