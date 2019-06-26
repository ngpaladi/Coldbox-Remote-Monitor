import RemoteMultimeter as RM
import time

dmm = RM.RemoteMultimeter("192.168.69.102",1394)
dmm.connect()
dmm.setupChannels([125],[126])
print(dmm)
print(dmm.scan())
time.sleep(3)
print(dmm.scan())
dmm.display("LOADING")
time.sleep(3)
dmm.disconnect()

