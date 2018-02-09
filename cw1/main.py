# use MicroPython to communicate between ESP8266 and LIS3DH via I2C

# imports
import ujson
import time
import math
import LIS3DH

# functions
def accel_mag(accel_data):
    mag = math.sqrt(math.pow(accel_data['x'],2) + math.pow(accel_data['y'],2) + math.pow(accel_data['z'],2))
    return mag

# parameters
time_interval = 0.1 # second

# variables
accel = {}
accel_accumulate = {}
distance = 0

# main program
def main():
    LIS3DH.init()

    print('range: +/- {0}g'.format(LIS3DH.range_g))   # display range
    print('unit: g')                                  # display unit (g)

    while True:
        accel = LIS3DH.get_accel()  # read x,y,z acceleration data from sensor
        print(ujson.dumps(accel))   # print raw JSON data
        time.sleep(time_interval)   # sleep for some time before reading next data
        print(accel_mag(accel))

main()