import RemoteMultimeter as RM
import time
import os
import sys
import json
import subprocess

def now():
    return time.time_ns()  / (10 ** 9)

dmm = RM.RemoteMultimeter("192.168.69.102", 1394)
dmm.connect()
dmm.setTemperatureChannels([125], "C")
dmm.setPressureChannels([126], "bar")
dmm.setupChannels()
print(dmm)
print(dmm.makeCsvHeader())

# Test how long a scan takes
t1 = time.time_ns()
baseline = dmm.scan(0)
t2 = time.time_ns()
scan_time_elapsed = (t2-t1)/ (10 ** 9)

print(baseline)


start_time = now() +5
dmm.display("WAITING")
p1 = subprocess.Popen("python -m http.server 8081")
while now() < start_time:
    time.sleep(0.1)

for i in range(10):
    timestamp = now() - start_time
    result = dmm.scan(timestamp)
    print(result.makeCsvRow())
    time.sleep(2-scan_time_elapsed)

dmm.display("DONE")
time.sleep(3)
p1.terminate()
p1.wait()
dmm.disconnect()
