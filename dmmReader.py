import RemoteMultimeter as RM
import time

dmm = RM.RemoteMultimeter("192.168.69.102",1394)
dmm.connect()
dmm.setupChannels([125],[126])
print(dmm)
print("Time,Temp,Pressure")
start_time = time.time_ns() / (10 ** 9)
for i in range(10):
    print(dmm.scan().getCsvRow(start_time))
    time.sleep(2)

dmm.display("DONE")
time.sleep(3)
dmm.disconnect()

