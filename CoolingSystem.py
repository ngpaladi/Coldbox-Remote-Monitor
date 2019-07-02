import RemoteMultimeter as RM
import time
import math
import CoolProp.CoolProp as CP

PHASE_TOLERANCE = 0.01  # * 100%

CO2_TRIPLE_POINT_TEMP = -56.57 + 273.15  # k
CO2_TRIPLE_POINT_PRESSURE = 5.11 * 1.01325  # bar
CO2_CRITICAL_POINT_TEMPERATURE = 30.98 + 273.15  # k
CO2_CRITICAL_POINT_PRESSURE = 72.79 * 1.01325 # bar


def CO2State(temp:float, pres:float) -> str:
    # From https://webbook.nist.gov/cgi/cbook.cgi?ID=C124389&Mask=4&Type=ANTOINE&Plot=on
    temp_kelvin = temp + 273.15
    pres_pa = 100000 * pres
    print(CP.PropsSI('Phase', 'P', pres_pa, 'T',temp_kelvin,'CarbonDioxide'))



class ChannelPair:
    def __init__(self, name: str, temperature_channel_id: int, pressure_channel_id: int):
        self.name = str(name)
        self.temperature_channel_id = int(temperature_channel_id)
        self.pressure_channel_id = int(pressure_channel_id)


class CoolingSystemSetup:
    def __init__(self, channel_list, channel_pair_list):
        self.channels = channel_list
        self.channel_pair_list = channel_pair_list


class CoolingSystemState:
    def __init__(self, setup: CoolingSystemSetup, scan_result: RM.ScanResult):
        self.scan_result = scan_result
        self.co2_checkpoints = {}
        for pair in setup.channel_pair_list:
            temp = scan_result.readings[pair.temperature_channel_id].value
            pres = scan_result.readings[pair.pressure_channel_id].value
            #state = CO2State(temp, pres)
            self.co2_checkpoints[pair.name] = [str(temp) + " " + str(scan_result.readings[pair.temperature_channel_id].unit), str(
                pres) + " " + str(scan_result.readings[pair.pressure_channel_id].unit), state]
