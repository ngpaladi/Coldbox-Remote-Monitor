import visa
import time

def VolatageToPressure(voltage_reading, supply_voltage):
    #Will convert voltage to pressure 
    return 0
    


class RemoteMultimeter:
    def __init__(self, ip, port):
        #Set IP and Port
        self.ip = ip
        self.port = port

    def connect(self):
        #Start visa resource manager
        self.rm = visa.ResourceManager("@py")
        
        #Open a socket connection to the Keithley 2701 device and configure read/write termination
        self.dev = self.rm.open_resource('TCPIP::'+str(self.ip)+'::'+str(self.port)+'::SOCKET')
        self.dev.read_termination = '\n'
        self.dev.write_termination = '\n'

        # Reset and clear device
        self.dev.write("*RST")
        self.dev.write("*CLS")
        self.dev.write("TRAC:CLE")
        #self.dev.write("ROUT:OPEN:ALL")
        self.dev.write("INIT:CONT OFF")

        #Setup display
        self.dev.write("DISP:TEXT:STAT ON")
        self.dev.write("DISP:TEXT:DATA 'READY'")
                
    def setupTemperatureChannels(self, list_of_channels):
        #Sets each channel in the list for a thermistor
        self.dev.write("UNIT:TEMP C")
        for channel in list_of_channels:
            self.dev.write("FUNC 'TEMP',(@"+str(channel)+")")
            

    def setupVoltageChannels(self, list_of_channels):
        #Sets each channel in the list
        for channel in list_of_channels:
            self.dev.write("FUNC 'VOLT',(@"+str(channel)+")")
            self.dev.write("VOLT:RANG 10, (@"+str(channel)+")")
        

    def setupChannels(self, list_of_channels):
        list_of_channels_str = ""
        for channel in list_of_channels:
            list_of_channels_str = list_of_channels_str+str(channel)+","
        list_of_channels_str = list_of_channels_str[:-1]
        self.dev.write("ROUT:SCAN (@"+list_of_channels_str+")")


    def identify(self):
        return self.dev.query("*IDN?")

    def display(self, string):
        self.dev.write("DISP:TEXT:DATA '"+string+"'")

    def disconnect(self):
	#close the socket connection
        self.dev.write("DISP:TEXT:DATA 'CLOSING'")
        time.sleep(3)
        self.dev.write("DISP:TEXT:STAT OFF")		
        self.dev.write("ROUT:OPEN:ALL")	

    def scan(self):
        

    #The following functions act as "pass-throughs" for SCPI commands
    def write(self, string):
        return self.dev.write(string)

    def query(self, string):
        return self.dev.query(string)

    def read(self, string):
        return self.dev.read(string)

