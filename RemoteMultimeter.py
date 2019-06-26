import visa
import time

# Global Settings Declarations
PRESSURE_SENSOR_SUPPLY_VOLTAGE = 8
REFERENCE_PRESSURE = 1.013  # bar
MAX_PRESSURE = 59  # bar
MIN_PRESSURE = -1  # bar


class ScanResult:
    # Helper class for ease of reading returned values

    def voltageToPressure(self, voltage_reading, supply_voltage):

        # Will convert voltage to pressure
        pressure = (voltage_reading - 0.1*supply_voltage)*(MAX_PRESSURE-MIN_PRESSURE)/(0.8*supply_voltage) + \
            MIN_PRESSURE+REFERENCE_PRESSURE  # Some linear function of voltage reading and supply voltage
        return pressure

    def __init__(self, raw_result, timestamp, num_temp, num_pres=0):
        self.raw_result = raw_result
        self.timestamp = timestamp

        # Grab Temperatures
        self.temperatures = []
        i = 0
        for val in raw_result[:num_temp*3]:
            if i % 3 == 0:
                self.temperatures.append(float(val))
            i += 1

        # Grab Pressures
        self.pressures = []
        i = 0
        for val in raw_result[:num_temp*3]:
            if i % 3 == 0:
                self.pressures.append(self.voltageToPressure(
                    float(val[:-3]), PRESSURE_SENSOR_SUPPLY_VOLTAGE))
            i += 1

        # Grab Average Times
        self.timestamps = []
        i = 0
        for val in raw_result[:num_temp*3]:
            if i % 3 == 1:
                self.timestamps.append(float(val[:-4]))
            i += 1
        self.average_time = sum(self.timestamps)/len(self.timestamps)

    def getCsvRow(self, start_time):
        return str(self.average_time+self.timestamp-start_time)+","+','.join(map(str, self.temperatures+self.pressures))

    def __str__(self):
        return str(self.raw_result)


class RemoteMultimeter:
    # Class for interacting with the multimeter

    def __init__(self, ip, port):
        # Set IP and Port
        self.ip = ip
        self.port = port
        self.connected = False

    def connect(self):
        # Start visa resource manager
        self.rm = visa.ResourceManager("@py")

        # Open a socket connection to the Keithley 2701 device and configure read/write termination
        self.dev = self.rm.open_resource(
            'TCPIP::'+str(self.ip)+'::'+str(self.port)+'::SOCKET')
        self.dev.read_termination = '\n'
        self.dev.write_termination = '\n'

        # Reset and clear device
        self.dev.write("*RST")
        self.dev.write("*CLS")
        self.dev.write("TRAC:CLE")

        # Setup display
        self.dev.write("DISP:TEXT:STAT ON")
        self.dev.write("DISP:TEXT:DATA 'READY'")

        self.connected = True

    def setupTemperatureChannels(self, list_of_channels):
        # Sets each channel in the list for a thermistor
        self.dev.write("UNIT:TEMP C")
        for channel in list_of_channels:
            self.dev.write("FUNC 'TEMP',(@"+str(channel)+")")

    def setupVoltageChannels(self, list_of_channels):
        # Sets each channel in the list
        for channel in list_of_channels:
            self.dev.write("FUNC 'VOLT',(@"+str(channel)+")")
            self.dev.write("VOLT:RANG 10, (@"+str(channel)+")")

    def setupChannels(self, list_of_temp_channels, list_of_volt_channels):
        # Save channel lists
        self.list_of_temp_channels = list_of_temp_channels
        self.list_of_volt_channels = list_of_volt_channels

        # Create the total list of channels
        list_of_channels = list_of_temp_channels + list_of_volt_channels
        self.list_of_channels = list_of_channels

        list_of_channels_str = ""
        for channel in list_of_channels:
            list_of_channels_str = list_of_channels_str+str(channel)+","
        list_of_channels_str = list_of_channels_str[:-1]
        self.list_of_channels_str = list_of_channels_str

        # Start setup for Keithley 2700
        self.dev.write("TRAC:CLE")
        self.dev.write("INIT:CONT OFF")
        self.dev.write("TRIG:COUN 1")

        # List channels
        self.setupTemperatureChannels(self.list_of_temp_channels)
        self.setupVoltageChannels(self.list_of_volt_channels)
        self.dev.write("SAMP:COUN "+str(len(self.list_of_channels)))
        self.dev.write("ROUT:SCAN (@"+self.list_of_channels_str+")")

        self.dev.write("ROUT:SCAN:TSO IMM")
        self.dev.write("ROUT:SCAN:LSEL INT")

    def scan(self):
        timestamp = time.time_ns() / (10 ** 9)
        self.last_scan_result = ScanResult(
            [x.strip() for x in self.dev.query("READ?").split(',')], timestamp, len(self.list_of_temp_channels))
        return self.last_scan_result

    def identify(self):
        return self.dev.query("*IDN?")

    def display(self, string):
        self.dev.write("DISP:TEXT:DATA '"+string+"'")

    def disconnect(self):
        # close the socket connection
        self.dev.write("DISP:TEXT:DATA 'CLOSING'")
        time.sleep(3)
        self.dev.write("DISP:TEXT:STAT OFF")
        self.dev.write("ROUT:OPEN:ALL")

    # The following functions act as "pass-throughs" for SCPI commands
    def write(self, string):
        return self.dev.write(string)

    def query(self, string):
        return self.dev.query(string)

    def read(self, string):
        return self.dev.read(string)

    def __str__(self):
        if self.connected:
            return "Connected to device at "+str(self.ip)+":"+str(self.port)+"\n"+self.identify()
        else:
            return "Device at "+str(self.ip)+":"+str(self.port)+" is not yet connected"
