import RemoteMultimeter as RM
import time
import os
import sys
import json
import subprocess
import argparse
import webbrowser

parser = argparse.ArgumentParser(description='Collect data from a Keithley 2701 Multimeter and monitor using a web page')
parser.add_argument("-c", "--config", help="Specify the configuration file")
