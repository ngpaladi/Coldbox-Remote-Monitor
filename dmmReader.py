import RemoteMultimeter as RM
import time
import os
import sys
import json
import subprocess
import argparse

csv_file_name = str(sys.argv[1])
time_interval = 5

def now():
    return time.time_ns() / (10 ** 9)


dmm = RM.RemoteMultimeter("192.168.69.102", 1394)
dmm.connect()
dmm.setTemperatureChannels([125], "C")
dmm.setPressureChannels([126], "bar")
dmm.setupChannels()
print(dmm)
print(dmm.makeCsvHeader())

# Test how long a scan takes

baseline = dmm.scan(0)
with open(csv_file_name, "w+") as csv_file:
    csv_file.write(dmm.makeCsvHeader())
time_a = time.time_ns()
temp_time1 = time.time_ns()
temp_time2 = time.time_ns()
temp_time_elapsed = (temp_time2-temp_time1) / (10 ** 9)
time_b = time.time_ns()
fine_tune_time = (time_b-time_a) / (10 ** 9)


start_time = now() + 5
dmm.display("WAITING")
p1 = subprocess.Popen("python -m http.server 8081")
while now() < start_time:
    time.sleep(0.05)

for i in range(10):
    t1 = time.time_ns()
    timestamp = now() - start_time
    result = dmm.scan(timestamp)
    with open(csv_file_name, "a") as csv_file:
        csv_file.write(result.makeCsvRow())
    print(result.makeCsvRow())
    t2 = time.time_ns()
    scan_time_elapsed = (t2-t1) / (10 ** 9)
    
    time.sleep(time_interval-scan_time_elapsed-fine_tune_time)

dmm.display("DONE")
time.sleep(3)
p1.terminate()
p1.wait()
dmm.disconnect()
