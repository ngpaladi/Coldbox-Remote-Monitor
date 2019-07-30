import pyvisa as visa
import time

# Global Settings Declarations
REFERENCE_PRESSURE = 1.013  # bar
MAX_PRESSURE = 59  # bar
MIN_PRESSURE = -1  # bar

TIMEOUT = 5000 # ms

# Unit Abbreviation Map
UNIT_ABBREVATION_MAP = {"celsius": "C", "voltage": "V", "bar": "bar"}

# Acceptable Units
TEMPERATURE_UNITS = ["C"]
VOLTAGE_UNITS = ["V"]
PRESSURE_UNITS = ["bar"]


def RemoveUnits(string: str) -> str:
    while not (string[-1] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
        string = string[:-1]
    return string


def VoltageToPressure(voltage_reading: float, supply_voltage: float) -> float:
   
     # Will convert voltage to pressure
    pressure = (abs(voltage_reading) - 0.1*supply_voltage)*(MAX_PRESSURE-MIN_PRESSURE)/(0.8*supply_voltage) + \
        MIN_PRESSURE+REFERENCE_PRESSURE  # Some linear function of voltage reading and supply voltage
    return pressure


class Channel:
    def __init__(self, id: int, unit: str):
        self.id = int(id)
        self.unit = str(unit)

    def __str__(self):
        return str(self.id)


class Measurement:
    def __init__(self, channel: Channel, time: float, value: float):
        self.channel = int(channel.id)
        self.time = float(time)
        self.value = float(value)
        self.unit = str(channel.unit)


class ScanResult:
    # Helper class for ease of reading returned values

    def __init__(self, channels: list, raw_result: list, timestamp: float, pressure_supply_voltage: float):
        self.raw_result = list(raw_result)
        self.channels = list(channels)
        self.initial_timestamp = float(timestamp)
        self.readings = {}
        self.pressure_supply_voltage = float(pressure_supply_voltage)

        entry_index = 0
        channel_index = 0
        last_value = 0.
        last_time = 0.
        for entry in raw_result:
            if entry_index % 3 == 0:
                last_value = float(RemoveUnits(entry))
            if entry_index % 3 == 1:
                last_time = float(RemoveUnits(entry))
                if(channels[channel_index].unit in PRESSURE_UNITS):
                    self.readings[channels[channel_index].id] = Measurement(
                        channels[channel_index], self.initial_timestamp+last_time, VoltageToPressure(last_value, self.pressure_supply_voltage))
                else:
                    self.readings[channels[channel_index].id] = Measurement(
                        channels[channel_index], self.initial_timestamp+last_time, last_value)
                channel_index += 1
            entry_index += 1

    def makeCsvRow(self) -> str:
        string = ""
        for channel in self.channels:
            string = string + \
                str(self.readings[channel.id].time)+"," + \
                str(self.readings[channel.id].value)+","
        return string[:-1]+"\n"

    def makeCsvHeader(self) -> str:
        string = ""
        for channel in self.channels:
            string = string + "Channel " + \
                str(channel.id)+" Time (s),Channel " + \
                str(channel.id)+" Value ("+str(channel.unit)+"),"
        return string[:-1]+"\n"

    def __str__(self):
        return str(self.raw_result)


class RemoteMultimeter:
    # Class for interacting with the multimeter

    def __init__(self, ip: str, port: int):
        # Set IP and Port
        self.ip = str(ip)
        self.port = int(port)
        self.connected = False
        self.channels = []
        self.voltage_channels = []
        self.pressure_channels = []
        self.thermistor_channels = []
        self.thermocouple_channels = []

    def connect(self):
        # Start visa resource manager
        self.resource_manager = visa.ResourceManager("@py")

        # Open a socket connection to the Keithley 2701 device and configure read/write termination
        self.device = self.resource_manager.open_resource(
            'TCPIP::'+str(self.ip)+'::'+str(self.port)+'::SOCKET')
        self.device.read_termination = '\n'
        self.device.write_termination = '\n'

        # Reset and clear device
        self.device.write("*RST")
        self.device.write("*CLS")
        self.device.write("TRAC:CLE")

        # Setup display
        self.device.write("DISP:TEXT:STAT ON")
        self.device.write("DISP:TEXT:DATA 'READY'")

        self.device.timeout = int(TIMEOUT)

        self.connected = True

    def setupThermistorChannels(self):
        # Sets each channel in the list for a thermistor
        self.device.write("UNIT:TEMP C")
        ch_list=""
        for channel in self.thermistor_channels:
            ch_list = ch_list+str(channel)+","
        ch_list = ch_list[:-1]

        temp_ch_list = ""
        for channel in self.temperature_channels:
            temp_ch_list = temp_ch_list+str(channel)+","
        temp_ch_list = temp_ch_list[:-1]

        self.device.write("FUNC 'TEMP',(@"+str(temp_ch_list)+")")
        self.device.write("TEMP:TRAN THER,(@"+str(ch_list)+")")
        self.device.write("TEMP:THER:TYPE 2252,(@"+str(ch_list)+")")

    def setupThermocoupleChannels(self):
        # Sets each channel in the list for a thermocouple
        self.device.write("UNIT:TEMP C")
        ch_list = ""
        for channel in self.thermocouple_channels:
            ch_list = ch_list+str(channel)+","
        ch_list = ch_list[:-1]

        temp_ch_list = ""
        for channel in self.temperature_channels:
            temp_ch_list = temp_ch_list+str(channel)+","
        temp_ch_list = temp_ch_list[:-1]

        self.device.write("FUNC 'TEMP',(@"+str(temp_ch_list)+")")
        self.device.write("TEMP:TRAN TC,(@"+str(ch_list)+")")
        self.device.write("TEMP:TC:TYPE K,(@"+str(ch_list)+")")
        self.device.write("TEMP:TC:RJUN:RSEL EXT,(@"+str(ch_list)+")")

    def setupFRTDChannels(self):
        # Sets each channel in the list for a thermocouple
        self.device.write("UNIT:TEMP C")
        ch_list = ""
        for channel in self.frtd_channels:
            ch_list = ch_list+str(channel)+","
        ch_list = ch_list[:-1]

        temp_ch_list = ""
        for channel in self.temperature_channels:
            temp_ch_list = temp_ch_list+str(channel)+","
        temp_ch_list = temp_ch_list[:-1]

        self.device.write("FUNC 'TEMP',(@"+str(temp_ch_list)+")")
        self.device.write("TEMP:TRAN FRTD,(@"+str(ch_list)+")")
        self.device.write("TEMP:FRTD:TYPE PT100,(@"+str(ch_list)+")")

    def setupVoltageChannels(self):
        # Sets each channel in the list
        ch_list=""
        for channel in list(self.voltage_channels+self.pressure_channels):
            ch_list = ch_list+str(channel)+","
        ch_list = ch_list[:-1]
        self.device.write("FUNC 'VOLT',(@"+str(ch_list)+")")
        self.device.write("VOLT:RANG 10, (@"+str(ch_list)+")")

    def setVoltageChannels(self, channels: list, unit: str):
        if (unit.lower() in UNIT_ABBREVATION_MAP):
            unit = UNIT_ABBREVATION_MAP[unit]
        if (unit not in ["V"]):
            raise Exception("ERROR! Invalid units")

        self.voltage_channels = []
        for id in channels:
            self.voltage_channels.append(Channel(id, unit))

    def setThermocoupleChannels(self, channels: list, unit: str):
        if (unit.lower() in UNIT_ABBREVATION_MAP):
            unit = UNIT_ABBREVATION_MAP[unit]
        if (unit not in ["C"]):
            raise Exception("ERROR! Invalid units")

        self.thermocouple_channels = []
        for id in channels:
            self.thermocouple_channels.append(Channel(id, unit))

    def setThermistorChannels(self, channels: list, unit: str):
        if (unit.lower() in UNIT_ABBREVATION_MAP):
            unit = UNIT_ABBREVATION_MAP[unit]
        if (unit not in ["C"]):
            raise Exception("ERROR! Invalid units")

        self.thermistor_channels = []
        for id in channels:
            self.thermistor_channels.append(Channel(id, unit))

    def setFRTDChannels(self, channels: list, unit: str):
        if (unit.lower() in UNIT_ABBREVATION_MAP):
            unit = UNIT_ABBREVATION_MAP[unit]
        if (unit not in ["C"]):
            raise Exception("ERROR! Invalid units")

        self.frtd_channels = []
        for pr in channels:
            if not isinstance(pr, list) or not len(pr) == 2 or not isinstance(pr[0], int) or not isinstance(pr[1], int):
                raise Exception("Not list of pairs of channels")
            pr.sort()
            self.frtd_channels.append(Channel(pr[0], unit))
            

    def setPressureChannels(self, channels: list, unit: str, voltage: float):
        if (unit.lower() in UNIT_ABBREVATION_MAP):
            unit = UNIT_ABBREVATION_MAP[unit]
        if (unit not in ["bar"]):
            raise Exception("ERROR! Invalid units")

        self.pressure_supply_voltage = float(voltage)

        self.pressure_channels = []
        for id in channels:
            self.pressure_channels.append(Channel(id, unit))

    def setupChannels(self):
        if (self.thermocouple_channels == [] and self.thermistor_channels == [] and self.voltage_channels == [] and self.pressure_channels == []):
            raise Exception("ERROR! No channels to set up")
        # Save channel lists


        self.temperature_channels = list(self.frtd_channels)
        self.temperature_channels.extend(self.thermocouple_channels)
        self.temperature_channels.extend(self.thermistor_channels)

        # Create the total list of channels
        channels = list(self.temperature_channels)
        channels.extend(self.voltage_channels)
        channels.extend(self.pressure_channels)
        self.channels = channels

        list_of_channels_str = ""

        for channel in channels:
            list_of_channels_str = list_of_channels_str+str(channel)+","

        list_of_channels_str = list_of_channels_str[:-1]
        self.list_of_channels_str = list_of_channels_str

        # Start setup for Keithley 2700
        self.device.write("TRAC:CLE")
        self.device.write("INIT:CONT OFF")
        self.device.write("TRIG:COUN 1")

        # List channels
        self.setupFRTDChannels()
        self.setupThermocoupleChannels()
        self.setupThermistorChannels()
        self.setupVoltageChannels()
        self.device.write("SAMP:COUN "+str(len(self.channels)))
        self.device.write("ROUT:SCAN (@"+self.list_of_channels_str+")")

        self.device.write("ROUT:SCAN:TSO IMM")
        self.device.write("ROUT:SCAN:LSEL INT")

    def scan(self, timestamp):
        self.last_scan_result = ScanResult(self.channels,
                                           [x.strip() for x in self.device.query("READ?").split(',')], timestamp,self.pressure_supply_voltage)
        return self.last_scan_result

    def identify(self):
        return self.device.query("*IDN?")

    def display(self, string: str):
        self.device.write("DISP:TEXT:DATA '"+string+"'")

    def disconnect(self):
        # close the socket connection
        self.device.write("DISP:TEXT:DATA 'CLOSING'")
        time.sleep(3)
        self.device.write("DISP:TEXT:STAT OFF")
        self.device.write("ROUT:OPEN:ALL")

    # The following functions act as "pass-throughs" for SCPI commands
    def write(self, string: str) -> str:
        return self.device.write(string)

    def query(self, string: str) -> str:
        return self.device.query(string)

    def read(self, string: str) -> str:
        return self.device.read(string)

    def __str__(self):
        if self.connected:
            return "Connected to device at "+str(self.ip)+":"+str(self.port)+"\n"+self.identify()
        else:
            return "Device at "+str(self.ip)+":"+str(self.port)+" is not yet connected"

    def makeCsvHeader(self) -> str:
        if(self.channels == []):
            raise Exception("ERROR! Channels not yet set up")
        string = ""
        for channel in self.channels:
            string = string + "Channel " + \
                str(channel.id)+" Time (s),Channel " + \
                str(channel.id)+" Value ("+str(channel.unit)+"),"
        return string[:-1]+"\n"
