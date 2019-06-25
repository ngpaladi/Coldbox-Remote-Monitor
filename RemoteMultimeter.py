import visa
import time

#Global Settings Declarations
PRESSURE_SENSOR_SUPPLY_VOLTAGE = 8

# Helper class for ease of reading returned values
class ScanResult:
    def volatageToPressure(self, voltage_reading, supply_voltage):
        #Will convert voltage to pressure 
        pressure = 0 #Some linear function of voltage reading and supply voltage
        return pressure
    def __init__(self, raw_result, num_temp):
        self.raw_result = raw_result
        self.raw_result_list = [float(i) for i in raw_result.split(',')]
        self.temperatures = raw_result_list[:num_temp]
        self.pressures = []
        for voltage in raw_result_list[num_temp:]:
            self.pressures.append(self.volatageToPressure(voltage, PRESSURE_SENSOR_SUPPLY_VOLTAGE))
        



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
        

    def setupChannels(self, list_of_temp_channels, list_of_volt_channels):
        #Create the total list of channels
        list_of_channels = list_of_temp_channels
        list_of_channels.extend(list_of_volt_channels)

        list_of_channels_str = ""
        for channel in list_of_channels:
            list_of_channels_str = list_of_channels_str+str(channel)+","
        list_of_channels_str = list_of_channels_str[:-1]

        #Save channel lists
        self.list_of_temp_channels = list_of_temp_channels
        self.list_of_volt_channels = list_of_volt_channels
        self.list_of_channels = list_of_channels

        #Start setup for Keithley 2700
        self.dev.write("TRAC:CLE")
        self.dev.write("INIT:CONT OFF")
        self.dev.write("TRIG:COUN INF")

        #List channels
        self.setupTemperatureChannels(list_of_temp_channels)
        self.setupVoltageChannels(list_of_volt_channels)
        self.dev.write("SAMP:COUN "+str(len(list_of_channels)))
        self.dev.write("ROUT:SCAN (@"+list_of_channels_str+")")
        
        self.dev.write("ROUT:SCAN:TSO IMM")
        self.dev.write("ROUT:SCAN:LSEL INT")
        

    def scan(self):
        self.last_scan_result = ScanResult((self.dev.query("READ?")),len(self.list_of_temp_channels))
        return self.last_scan_result

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

    #The following functions act as "pass-throughs" for SCPI commands
    def write(self, string):
        return self.dev.write(string)

    def query(self, string):
        return self.dev.query(string)

    def read(self, string):
        return self.dev.read(string)

