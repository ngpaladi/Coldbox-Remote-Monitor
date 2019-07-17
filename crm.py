import RemoteMultimeter as RM
import time
from datetime import datetime
import os
import sys
import json
import subprocess
import argparse
import webbrowser
import atexit
from pathlib import Path 

# Important Info
__version__ = "0.0.5"


# Settings
default_csv_filename = "Run_"+str(int(time.time()))+".csv"
time_interval = 5 #s
start_delay = 10 #s

# Functions
def now():
    return time.time_ns() / (10 ** 9)



parser = argparse.ArgumentParser(
    description='Collect data from a Keithley 2701 Multimeter and monitor using a web page')
parser.add_argument("-c", "--config", action="store", default="default.cfg",
                    dest="config_filename", help="Specify the configuration file")
parser.add_argument("-o", "--output", action="store", default=default_csv_filename,
                    dest="csv_filename", help="Give the name of the output file")
parser.add_argument('--version', action='version',
                    version='%(prog)s '+__version__)
results = parser.parse_args()

config_filename = Path(results.config_filename)
csv_filename = Path("csv")
csv_filename = csv_filename / Path(results.csv_filename).name

print('---------------------\n\n      CRM '+__version__ +
      '      \n\n    Noah Paladino    \n        2019         \n\n---------------------\n')
print('Settings:\n\nConfiguration: '+str(results.config_filename) +
      '\nData Storage: '+str(csv_filename)+'\n\n---------------------')

if csv_filename.exists() or not os.path.isdir(os.path.dirname(csv_filename.folder)):
    print('WARNING: Output File Exists!') 
    for x in range(5):
        print('Overwriting in'+ str(5-x) + 'seconds', end='\r')
        time.sleep(1)
    print('Overwriting...')

if not config_filename.is_file():
    raise Exception("Invalid Configuration")



dmm = RM.RemoteMultimeter("192.168.69.102", 1394)
dmm.connect()
dmm.setTemperatureChannels([125], "C")
dmm.setPressureChannels([126], "bar")
dmm.setupChannels()
print(dmm)
print(dmm.makeCsvHeader())

# Test how long a scan takes

baseline = dmm.scan(0)
with open(str(results.csv_filename), "w+") as csv_file:
    csv_file.write(dmm.makeCsvHeader())
time_a = time.time_ns()
temp_time1 = time.time_ns()
temp_time2 = time.time_ns()
temp_time_elapsed = (temp_time2-temp_time1) / (10 ** 9)
time_b = time.time_ns()
fine_tune_time = (time_b-time_a) / (10 ** 9)


start_time = now() + start_delay
print('\nStart Time:\n'+str(start_time)+'\n'+str(datetime.utcfromtimestamp(int(start_time)).strftime('%Y-%m-%d %H:%M:%S')))
dmm.display("WAITING")

# Start monitoring webpage 
p1 = subprocess.Popen("python -m http.server 8888", "web")
webbrowser.open("http://127.0.0.1:8888",1)


# Set up exit handler for when we kill loop
def exit_handler():
    dmm.display("DONE")
    p1.terminate()
    p1.wait()
    dmm.disconnect()

atexit.register(exit_handler)

while now() < start_time:
    time.sleep(0.05)

while 1:
    t1 = time.time_ns()
    timestamp = now() - start_time
    result = dmm.scan(timestamp)
    with open(str(results.csv_filename), "a") as csv_file:
        csv_file.write(result.makeCsvRow())

    t2 = time.time_ns()
    scan_time_elapsed = (t2-t1) / (10 ** 9)
    
    time.sleep(time_interval-scan_time_elapsed-fine_tune_time)
