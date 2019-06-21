import RemoteMultimeter as RM
import time

dmm = RM.RemoteMultimeter("192.168.69.102",1394)
dmm.connect()
time.sleep(3)
dmm.display("LOADING")
time.sleep(3)
print(dmm.identify())
dmm.disconnect()

