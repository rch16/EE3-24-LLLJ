''' use MicroPython to communicate between ESP8266 and LIS3DH via I2C '''



#//////////////////// imports ////////////////////
import machine
import math
import ujson
import utime
import lis3dh
import mqttpublisher as mp



#//////////////////// functions ////////////////////
def accel_mag(accel_data):
    mag = math.sqrt(math.pow(accel_data['x'],2) + math.pow(accel_data['y'],2) + math.pow(accel_data['z'],2))
    return mag

def formatted_datetime(datetime):
    return '{:d}-{:d}-{:d} {:02d}:{:02d}:{:02d}'.format(datetime[0], datetime[1], datetime[2], datetime[4], datetime[5], datetime[6])

def compile_data():
    data = lis3dh.get_accel()  # read x,y,z acceleration data from sensor
    data['time'] = formatted_datetime(rtc.datetime())   # add time stamp to data
    return data



#//////////////////// parameters ////////////////////
READ_INTERVAL = 0.1     # unit: second. Time interval for reading from sensor
SEND_INTERVAL = 2       # unit: second. Time interval for publishing to MQTT



#//////////////////// variables ////////////////////
rtc = machine.RTC()                     # RTC clock
rtc.datetime((2018,2,10,5,17,23,0,0))   # initialise
accel = {}
accel_accumulate = {}
distance = 0



#//////////////////// main program ////////////////////
def main():
    if not lis3dh.init():
        print('LIS3DH initialisation unsuccessful - is the sensor connected?')
        return
    if not mp.init():
        print('Connection timed out.')
        return

    print('range: +/- {0}g'.format(lis3dh.range_g))   # display range
    print('unit: g')                                  # display unit (g)

    while True:
        data = compile_data()
        mp.publish(data)
        utime.sleep(SEND_INTERVAL)  # sleep for some time before reading next data



#//////////////////// call main() ////////////////////
main()