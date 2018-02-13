''' use MicroPython to communicate between ESP8266 and LIS3DH via I2C '''



#//////////////////// imports ////////////////////
import machine
import math
import ujson
import utime
import lis3dh
import tmp007
import mqttpublisher as mp



#//////////////////// functions ////////////////////
def accel_mag(accel_data):
    mag = math.sqrt(math.pow(accel_data['x'],2) + math.pow(accel_data['y'],2) + math.pow(accel_data['z'],2))
    return mag

def formatted_datetime(datetime):
    return '{:d}-{:d}-{:d} {:02d}:{:02d}:{:02d}'.format(datetime[0], datetime[1], datetime[2], datetime[4], datetime[5], datetime[6])

def compile_data():
    data = {}
    data['temp'] = tmp007.read_obj_temp_c()             # add temperature
    data['time'] = formatted_datetime(rtc.datetime())   # add time stamp
    data['steps'] = lis3dh.get_steps()                  # add step
    return data



#//////////////////// parameters ////////////////////
# READ_INTERVAL = 0.1     # unit: second. Time interval for reading from sensor
SEND_INTERVAL = 4       # unit: second. Time interval for publishing to MQTT




#//////////////////// variables ////////////////////
rtc = machine.RTC()                     # RTC clock
rtc.datetime((2018,2,10,5,17,23,0,0))   # initialise



#//////////////////// main program ////////////////////
def main():
    if not tmp007.init():
        print('TMP007 initialisation unsuccessful - is the sensor connected?')
        return

    if not lis3dh.init(2, 20):
        print('LIS3DH initialisation unsuccessful - is the sensor connected?')
        return

    if not mp.init():
        print('Connection timed out.')
        return

    print('LIS3DH pedometer')
    print('    Acceleration')
    print('        unit: g')
    print('        range: +/- {0}g'.format(lis3dh.range_g))
    print('    Distance')
    print('        unit: m')
    print('TMP007')
    print('    unit: C (Celsius)')
    print('    range: +/- 256C')

    send_timer = -SEND_INTERVAL
    while True:
        data = compile_data()
        if utime.time() - send_timer >= SEND_INTERVAL:
            print(ujson.dumps(data))
            mp.publish(data)
            send_timer = utime.time()



#//////////////////// call main() ////////////////////
main()