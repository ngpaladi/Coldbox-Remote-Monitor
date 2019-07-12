# Coldbox Remote Monitoring System
![Screenshot](/img/Monitor_Webpage_Screenshot.png)

A toolkit for reading in data from a Keithley 2701 multimeter in order to test the CO<sub>2</sub> cooling system for the CMS Forward Pixel Detector.

## CRM Tool

The `crm` script can be used to start a data collection session. The script starts a webserver on port 8888 of the local machine with the monitoring interface and opens the default web browser. The user must specify the configuration file used (by default the program uses the included `default.cfg` designed for the setup at Purdue University).

The command should be run from inside the directory as follows:

```cmd
python crm.py -c <config.cfg> -o <output.csv>
```

## CRM-Config Tool

The `crm-config` script can be used to generate a configuration file for the CRM tool. After specifying the output configuration file name, the program will ask a series of questions which the user should respond to, and will result in a complete configuration file.

The command should be run from inside the project directory as follows:

```cmd
python crm-config.py -o <output.cfg>
```