#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Tinkerforge colour temperature and illuminance sensor with redbrick
# 2017-09-01 francesco.anselmo@arup.com

from config import *
import time, datetime
import signal
import sys
from os.path import join
from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_color import BrickletColor
from tinkerforge.brick_master import BrickMaster
from tinkerforge.brick_red import RED
from influxdb import InfluxDBClient

col_temp_inst = 0
ill_inst = 0

col_temp = []
ill = []

prev_time = 0
prev_integ_time = 0

# Callback function for colour reading (reflective) callback (not used)
def cb_color(r, g, b, cc):
    print("Color[R]: " + str(r))
    print("Color[G]: " + str(g))
    print("Color[B]: " + str(b))
    print("Color[C]: " + str(cc))
    print("")

def cb_color_temperature(cc):
    global col_temp, col_temp_inst
    col_temp_inst = cc
    col_temp.append(col_temp_inst)
    #print("Colour Temperature: " + str(col_temp_inst))
    #print("")

def cb_illuminance(ii):
    global ill, ill_inst
    ill_inst = ii
    ill.append(ill_inst)
    #print("Illuminance: " + str(ill_inst))
    #print("")

def exit_handler(signal, frame):
        print('Exiting and closing connections and files')
        # Close connection and files
        ipcon.disconnect()
        finst.close()
        favg.close()
        sys.exit(0)


if __name__ == "__main__":
    ipcon = IPConnection() # Create IP connection
    cb = BrickletColor(UID, ipcon) # Create device object
    master = BrickMaster(MASTERBRICK_UID, ipcon) # Create device object
    # redbrick = RED(REDBRICK_UID, ipcon) # Create device object

    ipcon.connect(HOST, PORT) # Connect to brickd

    cb.set_config(0,4) # set colour sensor gain to capture exterior values
    #print(cb.get_config())

    # Register colour callback to function cb_color
    #cb.register_callback(cb.CALLBACK_COLOR, cb_color)
    cb.register_callback(cb.CALLBACK_COLOR_TEMPERATURE, cb_color_temperature)
    cb.register_callback(cb.CALLBACK_ILLUMINANCE, cb_illuminance)

    # Set period for color callback to 1s (1000ms)
    # Note: The color callback is only called every second
    #       if the color has changed since the last call!
    #cb.set_color_callback_period(1000)
    cb.set_color_temperature_callback_period(1000)
    cb.set_illuminance_callback_period(1000)

    # Turn off blue LED on master brick so that it doesn't interfere with colour temperature measurements
    master.disable_status_led()

    # Open data files
    print("Opening intantaneous datalogging file %s" % FILENAMEINST)
    finst = open(FILENAMEINST, "a")
    print("Opening integrated datalogging file %s" % FILENAMEAVG)
    favg = open(FILENAMEAVG, "a")

    # Connect to InfluxDB server
    if useInflux:
        print("Connecting to InfluxDB server %s" % INFLUXserver)
        client = InfluxDBClient(INFLUXserver, INFLUXport, INFLUXdbuser, INFLUXdbuser_password, INFLUXdbname)

    prev_time = time.time()
    prev_integ_time = time.time()

    signal.signal(signal.SIGINT, exit_handler)

    while True:
        # Get timestamp
        ts = time.time()
        #print(time.time(), prev_time)
        datestr = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        # Write values on file and to InfluxDB at instantaneous interval
        if time.time()-prev_time > INTERVAL:
            ct = col_temp_inst #col_temp[-1]
            illum = ill_inst #ill[-1]
            #print (datestr, col_temp, ill)
            print ("instantaneous measurement at "+str(INTERVAL)+" s", datestr, ct, illum)
            finst.write(datestr + "," + str(ct) + "," + str(illum) +'\n')
            finst.flush()
            if useInflux:
                # Write colour_temperature to influxdb server
                json_body = [
                    {
                    "measurement": SENSORNAME+"_"+'colour_temperature',
                    "tags": {
                        "sensor": SENSORNAME+"_average",
                    },
                    "time": datestr,
                    "fields": {
                        "value": ct,
                        }
                    }
                ]
                client.write_points(json_body)
                # Write illuminance
                json_body = [
                    {
                    "measurement": SENSORNAME+"_"+'illuminance',
                    "tags": {
                        "sensor": SENSORNAME+"_average",
                    },
                    "time": datestr,
                    "fields": {
                        "value": illum,
                        }
                    }
                ]
                client.write_points(json_body)
            # Reset time counter
            prev_time = time.time()

        # Write values at integration interval
        if time.time()-prev_integ_time > INTEGRATIONTIME:
            ct = sum(col_temp)/(len(col_temp)+1) #col_temp[-1]
            illum = sum(ill)/(len(ill)+1) #ill[-1]
            print (datestr, col_temp, ill)
            print ("integrated measurement at "+str(INTEGRATIONTIME)+" s", datestr, ct, illum)
            favg.write(datestr + "," + str(ct) + "," + str(illum) +'\n')
            favg.flush()
            if useInflux:
                # write colour_temperature to influxdb server
                json_body = [
                    {
                    "measurement": SENSORNAME+"_"+'colour_temperature_average',
                    "tags": {
                        "sensor": SENSORNAME+"_average",
                    },
                    "time": datestr,
                    "fields": {
                        "value": ct,
                        }
                    }
                ]
                client.write_points(json_body)
                # Write illuminance
                json_body = [
                    {
                    "measurement": SENSORNAME+"_"+'illuminance_average',
                    "tags": {
                        "sensor": SENSORNAME+"_average",
                    },
                    "time": datestr,
                    "fields": {
                        "value": illum,
                        }
                    }
                ]
                client.write_points(json_body)
            # Reset arrays and time couter
            col_temp = []
            ill = []
            prev_integ_time = time.time()
