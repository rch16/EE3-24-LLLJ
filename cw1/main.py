# use MicroPython to communicate between ESP8266 and LIS3DH via I2C

print('\n\n\nBegin main.py')

# imports
import ujson
import time
import LIS3DH

# parameters
sleep_time_seconds = 0.2

# variables
data = {}

# main program
def main():
    LIS3DH.init()

    print('range: +/- {0}g'.format(LIS3DH.range_g))   # display range
    print('unit: g')                                        # display unit (g)

    while True:
        # read x,y,z acceleration data from sensor and convert to JSON format
        data = ujson.dumps(LIS3DH.read_from_sensor())
        print(data)                         # print raw JSON data
        time.sleep(sleep_time_seconds)      # sleep for some time before reading next data

main()