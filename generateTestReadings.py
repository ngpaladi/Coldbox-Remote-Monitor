import RemoteMultimeter as RM
import CoolingSystem as CS
import time
import random
import subprocess
import webbrowser

temp_channels = [125,126,127,128,129,130,131,132,133]
pres_channels = [110,111,112,113]
pairs = [CS.ChannelPair("Point 1",125,110),CS.ChannelPair("Point 2",126,111),CS.ChannelPair("Point 3",127,112),CS.ChannelPair("Point 4",128,113)]


def FakeMeasurements():
    fake_measurements = []
    for i in range(len(temp_channels)):
        fake_measurements.append(str((random.random()-0.5)*20))
        fake_measurements.append(str(0.01364*i)+"SECS")
        fake_measurements.append(str(float(i))+"RDNG#")
    for i in range(len(pres_channels)):
        fake_measurements.append(str(random.random()*6.4+.8))
        fake_measurements.append(str(0.01364*(i+len(temp_channels)))+"SECS")
        fake_measurements.append(str(float(i+len(temp_channels)))+"RDNG#")
    return fake_measurements

config = CS.CoolingSystemConfig("192.168.69.102", 1394, temp_channels,"C",pres_channels,"bar",pairs)
setup = CS.CoolingSystemSetup(config,time.time_ns() / (10 ** 9)+10)
setup.WriteJSON()
print(FakeMeasurements)
p1 = subprocess.Popen("python -m http.server 8800", shell=True)

webbrowser.open("http://127.0.0.1:8800",1)
time.sleep(9.8)
for i in range(0,129600):
    state = CS.CoolingSystemState(setup,RM.ScanResult(setup.channels,FakeMeasurements(),5*i))
    state.WriteJSON(i)
    time.sleep(5)
p1.terminate()
p1.wait()
