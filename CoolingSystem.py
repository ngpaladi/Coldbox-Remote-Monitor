import RemoteMultimeter as RM
import time
import math
import CoolProp.CoolProp as CP
import json
from pathlib import Path 
import numpy as np

PHASE_TOLERANCE = 0.01  # * 100%

CO2_TRIPLE_POINT_TEMP = -56.57 + 273.15  # k
CO2_TRIPLE_POINT_PRESSURE = 5.11 * 1.01325  # bar
CO2_CRITICAL_POINT_TEMPERATURE = 30.98 + 273.15  # k
CO2_CRITICAL_POINT_PRESSURE = 72.79 * 1.01325 # bar
COLOR_LIST = ['#CABC40','#88B509','#44A662','#084B66','#1A5751','#DD5C30','#DBC252','#143C4C','#344F3C','#5DAA79','#EF9038','red','blue','hotpink','orange','yellow','darkgreen','cyan','navy','brown','gray','black','limegreen','navajowhite','steelblue','darkkhaki','lavender','magenta','purple','teal','greenyellow']

class PTFit:
    def __init__(self):
        self.A = float(3.4800623889616004e+003)/100 # t^0
        self.B = float(9.0359026674679797e+001)/100 # t^1
        self.C = float(8.9559206133742097e-001)/100 # t^2
        self.D = float(5.7677062060042597e-003)/100 # t^3
        self.E = float(3.2023333559056788e-005)/100 # t^4
    def Evaluate(self, temperature:float):
        t = temperature
        a = self.A
        b = self.B
        c = self.C
        d = self.D
        e = self.E
        return (e*(t**4)+d*(t**3)+c*(t**2)+b*(t)+a)
    def EvaluateDerivative(self, temperature:float):
        t = temperature
        b = self.B
        c = self.C
        d = self.D
        e = self.E
        return (4*e*(t**3)+3*d*(t**2)+2*c*(t)+b)
    def EvaluateDistance(self, temperature:float, pressure:float):
        return np.sqrt(self.Evaluate(temperature)-pressure)
            

    

def CO2State(temp:float, pres:float) -> str:
    temp_kelvin = temp + 273.15
    pres_pa = 100000 * pres
    return CP.PhaseSI( 'P', pres_pa, 'T',temp_kelvin,'CarbonDioxide')

class ChannelPair:
    def __init__(self, name: str, temperature_channel_id: int, pressure_channel_id: int):
        self.name = str(name)
        self.temperature_channel_id = int(temperature_channel_id)
        self.pressure_channel_id = int(pressure_channel_id)
    @classmethod
    def FromDict(cls, s):
        return ChannelPair(s["name"],s["temperature_channel_id"],s["pressure_channel_id"])
    def ToDict(self):
        return { "name": self.name, "temperature_channel_id": self.temperature_channel_id, "pressure_channel_id": self.pressure_channel_id}


class CoolingSystemConfig:
    def __init__(self, ip_address: str, port: int, thermocouple_channels = [], thermistor_channels = [], temperature_units = "C", pressure_channels = [], pressure_units = "bar", pressure_supply_voltage=8.0, channel_pairs=[]):
        self.ip_address = str(ip_address)
        self.port = int(port)
        self.thermocouple_channels = list(thermocouple_channels)
        self.thermistor_channels = list(thermistor_channels)
        self.temperature_channels = list(self.thermocouple_channels)
        self.temperature_channels.extend(list(self.thermistor_channels))
        self.temperature_units = str(temperature_units)
        self.pressure_channels = list(pressure_channels)
        self.pressure_units = str(pressure_units)
        self.pressure_supply_voltage = float(pressure_supply_voltage)
        self.channel_pairs = list(channel_pairs)

        self.channels = []
        for ch in self.temperature_channels :
            self.channels.append(RM.Channel(ch,self.temperature_units))
        for ch in self.pressure_channels :
            self.channels.append(RM.Channel(ch,self.pressure_units))
    @classmethod
    def FromJSON(cls, in_file):
        c = {}
        if isinstance(in_file, (str, bytes, Path)):
            with open(in_file, 'r') as f:
                c = json.load(f)
        else:
            c = json.load(in_file)

        ch_pairs = []
        for index in range(len(c["channel_pairs"])):
            ch_pairs.append(ChannelPair.FromDict(c["channel_pairs"][index]))

        cfg = CoolingSystemConfig(c["ip_address"],c["port"], c["thermocouple_channels"], c["thermistor_channels"], c["temperature_units"],c["pressure_channels"],c["pressure_units"],c["pressure_supply_voltage"],ch_pairs)
        return cfg

    def WriteJSON(self, in_file):
        c = {}
        c["ip_address"] = self.ip_address
        c["port"] = self.port
        c["thermocouple_channels"] = self.thermocouple_channels
        c["thermistor_channels"] = self.thermistor_channels
        c["temperature_units"] = self.temperature_units
        c["pressure_channels"] = self.pressure_channels
        c["pressure_units"] = self.pressure_units
        c["pressure_supply_voltage"] = self.pressure_supply_voltage
        c["channel_pairs"]=[]
        for p in self.channel_pairs:
            c["channel_pairs"].append(p.ToDict())

        if isinstance(in_file, (str, bytes, Path)):
            with open(in_file, 'w+') as f:
                f.write(json.dumps(c))
        else:
            in_file.write(json.dumps(c))

    
    def __str__(self):
        pairs=""
        for pair in self.channel_pairs:
            pairs = pairs+"\n    Name: "+str(pair.name)+"\n        Temperature Channel: "+str(pair.temperature_channel_id)+"\n        Pressure Channel: "+str(pair.pressure_channel_id)+"\n"
        return "IP: "+str(self.ip_address)+"\nPort: "+str(self.port)+"\n Thermocouple Channels: "+ str(self.thermocouple_channels) +"\n Thermistor Channels: "+ str(self.thermistor_channels)+"\nPressure Channels: "+ str(self.pressure_channels) + "\nPairs:"+ pairs+"\n"



class CoolingSystemSetup:
    def __init__(self, config, start_time, csv_name):
        self.channels = config.channels
        self.channel_pair_list = config.channel_pairs
        self.start_time = start_time
        self.csv_name = csv_name
    def WriteJSON(self):
        writable_dict = {}
        writable_dict["start_time"] = self.start_time
        writable_dict["header"] = []
        writable_dict["checkpoint_names"] = []
        writable_dict["csv"] = self.csv_name

        for pair in self.channel_pair_list:
            writable_dict["checkpoint_names"].append(str(pair.name))
        for channel in self.channels:
            writable_dict["header"].append("CH " + str(channel.id)+" Time (s)")
            writable_dict["header"].append("CH " + str(channel.id)+" Val ("+str(channel.unit)+")")
        
        with open(Path("web/CoolingSystemSetup.json"),"w+") as f:
            f.write(json.dumps(writable_dict))
            print("Setup written")






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
            fit = PTFit()
            distance = fit.EvaluateDistance(temp,pres)
            sign = ""
            if pres > fit.Evaluate(temp):
                sign="+"
            elif pres < fit.Evaluate(temp):
                sign="-"
            self.co2_checkpoints.append({"name": str(pair.name), "temperature": str(round(temp,2)) + " " + str(scan_result.readings[pair.temperature_channel_id].unit),"pressure": str(round(pres,2)) + " " + str(scan_result.readings[pair.pressure_channel_id].unit), "state":state, "distance":(sign+str(round(distance,3))+ " " + str(scan_result.readings[pair.pressure_channel_id].unit))})
        
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
        with open(Path("web/CoolingSystemState.json"),"w+") as f:
            f.write(json.dumps(writable_dict))

    