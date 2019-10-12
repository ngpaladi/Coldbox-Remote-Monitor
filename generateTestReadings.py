import py2700 as RM
import CoolingSystem as CS
import time
import random
import subprocess
import webbrowser
import math
import atexit
import os
from pathlib import Path

tmst_channels = [121,122,123,124,125]
tcpl_channels = [101,102,103]
temp_channels = list(tcpl_channels)
temp_channels.extend(tmst_channels)
pres_channels = [111,112,113]
pairs = [CS.ChannelPair("Point 1",101,111),CS.ChannelPair("Point 2",102,112),CS.ChannelPair("Point 3",103,113)]


def FakeMeasurements(t):
    fake_measurements = []
    for i in range(len(pres_channels)):
        fake_measurements.append(str((random.random()-0.5)*20))
        fake_measurements.append(str(0.01364*i)+"SECS")
        fake_measurements.append(str(float(i))+"RDNG#")

    for i in range(len(temp_channels)-len(pres_channels)):
        fake_measurements.append(str((70/(1+math.exp(-1*(t-5000)/1000)))+(random.gauss(0,2))-40))
        fake_measurements.append(str(0.01364*(i+len(pres_channels)))+"SECS")
        fake_measurements.append(str(float(i+len(pres_channels)))+"RDNG#")

    for i in range(len(pres_channels)):
        fake_measurements.append(str(random.random()*4+.8))
        fake_measurements.append(str(0.01364*(i+len(temp_channels)))+"SECS")
        fake_measurements.append(str(float(i+len(temp_channels)))+"RDNG#")

    return fake_measurements

# Delete old json states
if os.path.exists(Path("web/CoolingSystemState.json")):
    os.remove(Path("web/CoolingSystemState.json"))
    print("Old State Removed...")
if os.path.exists(Path("web/CoolingSystemSetup.json")):
    os.remove(Path("web/CoolingSystemSetup.json"))
    print("Old Setup Removed...")
config = CS.CoolingSystemConfig("192.168.69.102", 1394, tcpl_channels, tmst_channels,"C",pres_channels,"bar",8.0,pairs)
setup = CS.CoolingSystemSetup(config,time.time_ns() / (10 ** 9)+10, "none")
setup.WriteJSON()
time.sleep(2)
print(FakeMeasurements)
p1 = subprocess.Popen("python -m http.server 8800", shell=True)
def exit_handler():
    p1.terminate()
    p1.wait()

atexit.register(exit_handler)
webbrowser.open("http://127.0.0.1:8800",1)
time.sleep(7.8)
for i in range(0,129600):
    state = CS.CoolingSystemState(setup,RM.ScanResult(setup.channels,FakeMeasurements(5*i),5*i))
    state.WriteJSON(i)
    time.sleep(5)
p1.terminate()
p1.wait()
