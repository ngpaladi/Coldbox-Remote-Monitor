import RemoteMultimeter as RM
import time
import math
import CoolProp.CoolProp as CP
import json

PHASE_TOLERANCE = 0.01  # * 100%

CO2_TRIPLE_POINT_TEMP = -56.57 + 273.15  # k
CO2_TRIPLE_POINT_PRESSURE = 5.11 * 1.01325  # bar
CO2_CRITICAL_POINT_TEMPERATURE = 30.98 + 273.15  # k
CO2_CRITICAL_POINT_PRESSURE = 72.79 * 1.01325 # bar
COLOR_LIST = ['red','blue','hotpink','orange','yellow','darkgreen','cyan','navy','brown','gray','black','limegreen','navajowhite','steelblue','darkkhaki','lavender','magenta','purple','teal','greenyellow']


def CO2State(temp:float, pres:float) -> str:
    temp_kelvin = temp + 273.15
    pres_pa = 100000 * pres
    return CP.PhaseSI( 'P', pres_pa, 'T',temp_kelvin,'CarbonDioxide')



class ChannelPair:
    def __init__(self, name: str, temperature_channel_id: int, pressure_channel_id: int):
        self.name = str(name)
        self.temperature_channel_id = int(temperature_channel_id)
        self.pressure_channel_id = int(pressure_channel_id)


class CoolingSystemConfig:
    def __init__(self, ip_address: str, port: int, temperature_channels = [], temperature_units = "", pressure_channels = [], pressure_units = "", channel_pairs=[]):
        self.ip_address = str(ip_address)
        self.port = int(port)
        self.temperature_channels = list(temperature_channels)
        self.temperature_units = str(temperature_units)
        self.pressure_channels = list(pressure_channels)
        self.pressure_units = str(pressure_units)
        self.channel_pairs = list(channel_pairs)

        self.channels = []
        for ch in self.temperature_channels :
            self.channels.append(RM.Channel(ch,self.temperature_units))
        for ch in self.pressure_channels :
            self.channels.append(RM.Channel(ch,self.pressure_units))

class CoolingSystemSetup:
    def __init__(self, config, start_time):
        self.channels = config.channels
        self.channel_pair_list = config.channel_pairs
        self.start_time = start_time
    def WriteJSON(self):
        writable_dict = {}
        writable_dict["start_time"] = self.start_time
        writable_dict["header"] = []
        writable_dict["checkpoint_names"] = []

        for pair in self.channel_pair_list:
            writable_dict["checkpoint_names"].append(str(pair.name))
        for channel in self.channels:
            writable_dict["header"].append("CH " + str(channel.id)+" Time (s)")
            writable_dict["header"].append("CH " + str(channel.id)+" Val ("+str(channel.unit)+")")
        
        with open("CoolingSystemSetup.json","w+") as f:
            f.write(json.dumps(writable_dict))




class CoolingSystemState:
    def __init__(self, setup: CoolingSystemSetup, scan_result: RM.ScanResult):
        self.temperature_dataset = []


        i=0
        for ch in scan_result.readings:
            paired_ch = False
            for pair in setup.channel_pair_list:
                if (ch == pair.temperature_channel_id or ch == pair.pressure_channel_id or (not scan_result.readings[ch].unit in ['C','k','F'])):
                    paired_ch = True
            if not paired_ch:
                self.temperature_dataset.append({"label":"CH"+str(ch),"borderColor":COLOR_LIST[i % len(COLOR_LIST)], "data":[{"x":scan_result.readings[ch].time,"y":scan_result.readings[ch].value}]})
                i += 1  

        self.co2_checkpoints = []
        for pair in setup.channel_pair_list:
            temp = scan_result.readings[pair.temperature_channel_id].value
            pres = scan_result.readings[pair.pressure_channel_id].value
            state = CO2State(temp, pres)
            self.co2_checkpoints.append({"name": str(pair.name), "temperature": str(round(temp,2)) + " " + str(scan_result.readings[pair.temperature_channel_id].unit),"pressure": str(round(pres,2)) + " " + str(scan_result.readings[pair.pressure_channel_id].unit), "state":state})
        
        self.table_row = []
        for channel in scan_result.channels:
            self.table_row.append(str(round(scan_result.readings[channel.id].time,3)))
            self.table_row.append(str(round(scan_result.readings[channel.id].value,3)))
    
    def WriteJSON(self,state_id):
        writable_dict = {}
        writable_dict["id"] = state_id
        writable_dict["temperatures"] = self.temperature_dataset
        writable_dict["checkpoints"] = self.co2_checkpoints
        writable_dict["row"] = self.table_row
        with open("CoolingSystemState.json","w+") as f:
            f.write(json.dumps(writable_dict))

    