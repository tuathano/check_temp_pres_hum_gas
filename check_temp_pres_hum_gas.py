#!/usr/bin/env python

# check_temp_pres_hum_gas.py
#
# python 3 script to poll BME680 enviromental sensor and return Nagios exit codes
# T. O'Shea / R. Trouncer 2020
#
# v1:   22/01/2020:     Initial version
# v1.1: 24/01/2020:     Minor edit; changed - to : in output string to avoid confusion with minus sign.
# v2:   28/01/2020:     Added median filtering of raw sensor data. User can input 2 additional arguments from command
#                       line to modify the total length and time interval (s) between points for the filter.
# v3:   29/01/2020:     Combine all sensor checks into one serial god-awful check as the BME680 chip cannot cope with lots of seperate polling.
# v3.1: 30/01/2020:     Minor bug fix in WARNING condition
#
# Nagios exit codes:
# 0 - Service is OK
# 1 - Service is WARNING
# 2 - Service is in a CRITICAL status
# 3 - Service status is UNKNOWN
#
# Usage example:
#
# check_temp_pres_hum_gas.py <selected_meas> (<crit_min> <crit_max> <warn_min> <warn_max> x4) <filt_pts> <filt_int>
#
# e.g. check_temp_pres_hum_gas.py 12 28 18 25 10 100 20 80 10000 10000000 500000 9000000 900 1070 920 1060 5 1
#
# The first set of crit_min/max and warn_min/max values are for temperature, then humidity, then gas and finally pressure.
# <filt_pts> is the number of points to use when median filtering the raw data and <filt_int> is the time interval (in seconds) between the points.

# Required libraries
import sys
import board
import busio
import adafruit_bme680
import time
import statistics

all_sensors = ["temp", "humidity", "gas", "pressure"] # define all the sensors to check
exit_code_lst = [] # empty lists to store the exit code and measured value for each sensor
meas_val_lst = []
unit_lst = []

input_arguments = sys.argv # read in command line arguments
filt_pts=int(input_arguments[17]) # median filter input settings
filt_int=float(input_arguments[18])

i2c = busio.I2C(board.SCL, board.SDA) # load i2c protocol

def test_limits(meas_val,crit_min,crit_max,warn_min,warn_max):
    """Compare measurement agains the warning and critical values"""
    if meas_val < crit_min or meas_val > crit_max:
        return 2

    if meas_val < warn_min or meas_val > warn_max:
        return 1

    return 0

def sensor_filt(selected_meas, filt_pts, filt_int):
    """filter the measured values"""
    sensor_polls=[]

    for i in range(0, filt_pts):
        try:
            sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c)
            command = {"temp":sensor.temperature, "humidity":sensor.humidity, "gas":sensor.gas, "pressure":sensor.pressure}
            cur_poll=command[selected_meas]
        except:
            print("UNKNOWN: sensor polling error")
            sys.exit(3)

        sensor_polls.append(cur_poll)
        sensor = None
        time.sleep(filt_int) # sleep for input number of seconds

    filt_val = statistics.median(sensor_polls)

    return filt_val, sensor_polls

def check_param(selected_meas):
    """Return sensor measurement data and comparison with limits"""
    if selected_meas == "temp":

        crit_min=float(input_arguments[1]) # critical and warning levels
        crit_max=float(input_arguments[2])
        warn_min=float(input_arguments[3])
        warn_max=float(input_arguments[4])

        filt_val, sensor_polls = sensor_filt(selected_meas, filt_pts, filt_int)
        meas_val = round(filt_val,2)
        exit_code = test_limits(meas_val,crit_min,crit_max,warn_min,warn_max)
        unit = "C"

    elif selected_meas == "humidity":

        crit_min=float(input_arguments[5]) # critical and warning levels
        crit_max=float(input_arguments[6])
        warn_min=float(input_arguments[7])
        warn_max=float(input_arguments[8])

        filt_val, sensor_polls = sensor_filt(selected_meas, filt_pts, filt_int)
        meas_val = round(filt_val,2)
        exit_code = test_limits(meas_val,crit_min,crit_max,warn_min,warn_max)
        unit = "%"

    elif selected_meas == "gas":

        crit_min=float(input_arguments[9]) # critical and warning levels
        crit_max=float(input_arguments[10])
        warn_min=float(input_arguments[11])
        warn_max=float(input_arguments[12])

        filt_val, sensor_polls = sensor_filt(selected_meas, filt_pts, filt_int)
        meas_val = round(filt_val,2)
        exit_code = test_limits(meas_val,crit_min,crit_max,warn_min,warn_max)
        unit = "ohms"

    elif selected_meas == "pressure":

        crit_min=float(input_arguments[13]) # critical and warning levels
        crit_max=float(input_arguments[14])
        warn_min=float(input_arguments[15])
        warn_max=float(input_arguments[16])

        filt_val, sensor_polls = sensor_filt(selected_meas, filt_pts, filt_int)
        meas_val = round(filt_val,2)
        exit_code = test_limits(meas_val,crit_min,crit_max,warn_min,warn_max)
        unit = "mBar"

    return meas_val, exit_code, unit

def status_msg(exit_code_lst, meas_val_lst):
    """configure NRPE/Nagios output data"""
    if (all(v == 0 for v in exit_code_lst)) == True:
        print("OK:" + " temperature=" + str(meas_val_lst[0]) + str(unit_lst[0]) + ", humidity=" + str(meas_val_lst[1]) + str(unit_lst[1]) + ", gas=" + str(meas_val_lst[2]) + str(unit_lst[2]) + ", pressure=" + str(meas_val_lst[3]) + str(unit_lst[3]) + " | 'temperature_C'=" + str(meas_val_lst[0])  + "; 'humidity_rel'=" + str(meas_val_lst[1]) + "; 'gas_ohms'=" + str(meas_val_lst[2]) + "; 'pressure_mbar'=" + str(meas_val_lst[3]) + ";")
        sys.exit(0)

    elif ((any(v == 1 for v in exit_code_lst)) == True) and ((any(v == 2 for v in exit_code_lst)) == False):
        print("WARNING:" + " temperature=" + str(meas_val_lst[0]) + str(unit_lst[0]) + ", humidity=" + str(meas_val_lst[1]) + str(unit_lst[1]) + ", gas=" + str(meas_val_lst[2]) + str(unit_lst[2]) + ", pressure=" + str(meas_val_lst[3]) + str(unit_lst[3]) + " | 'temperature_C'=" + str(meas_val_lst[0])  + "; 'humidity_rel'=" + str(meas_val_lst[1]) + "; 'gas_ohms'=" + str(meas_val_lst[2]) + "; 'pressure_mbar'=" + str(meas_val_lst[3]) + ";")
        sys.exit(1)

    elif (any(v == 2 for v in exit_code_lst)) == True:
        print("CRITICAL:" + " temperature=" + str(meas_val_lst[0]) + str(unit_lst[0]) + ", humidity=" + str(meas_val_lst[1]) + str(unit_lst[1]) + ", gas=" + str(meas_val_lst[2]) + str(unit_lst[2]) + ", pressure=" + str(meas_val_lst[3]) + str(unit_lst[3]) + " | 'temperature_C'=" + str(meas_val_lst[0])  + "; 'humidity_rel'=" + str(meas_val_lst[1]) + "; 'gas_ohms'=" + str(meas_val_lst[2]) + "; 'pressure_mbar'=" + str(meas_val_lst[3]) + ";")
        sys.exit(2)

    else:
        print("UNKNOWN")
        sys.exit(3)

    return None

# loop through the individual sensors
for indv_sensor in all_sensors:

  selected_meas = indv_sensor
  meas_val, exit_code, unit  = check_param(selected_meas) # compare the selected sensor with input critical and warning levels

  exit_code_lst.append(exit_code) # append list with exit code, filtered value and measurement unit
  meas_val_lst.append(meas_val)
  unit_lst.append(unit)

status_msg(exit_code_lst, meas_val_lst) # output data for NRPE/Nagios
