''' use MicroPython to communicate between ESP8266 and LIS3DH via I2C '''



#//////////////////// imports /////////////////////////////////////////////////
import machine
import math
import ujson
import utime
import lis3dh
import tmp007
import mqttpublisher as mp



#//////////////////// class ///////////////////////////////////////////////////
class User:                     # user data for calories estimation
    def __init__(self, _age, _weight, _height, _pace):
        self.age =    _age      # unit: years
        self.weight = _weight   # unit: kg
        self.height = _height   # unit: m
        self.pace =   _pace     # unit: km/h

        self.stride_length = 0  # unit: m. Length of stride
        self.met           = 0  # metabolic equivalent of activity
        self.cal_factor    = 0  # for estimating expended calories

        self.stride_length = self.height * 0.415

        met_lookup = {0:2, 3.2:2.5, 4:3, 4.8:3.5, 6.4:5, 7.2:6.3, 8:5}
        for speed, m in met_lookup.items():
            if self.pace >= speed:
                self.met = m

        self.cal_factor = self.weight * self.met / self.pace * \
                          self.stride_length / 1000



#//////////////////// variables ///////////////////////////////////////////////
rtc = machine.RTC()                     # RTC clock
rtc.datetime((2018,2,15,5,09,23,0,0))   # initialise

u = User(20, 70, 1.80, 3.5)



#//////////////////// parameters //////////////////////////////////////////////
SEND_INTERVAL = 4       # unit: second. Time interval for publishing to MQTT



#//////////////////// functions ///////////////////////////////////////////////
def accel_mag(accel_data):
    mag = math.sqrt(math.pow(accel_data['x'], 2) + math.pow(accel_data['y'], 2)
        + math.pow(accel_data['z'], 2))
    return mag

def formatted_datetime(datetime):
    return '{:d}-{:d}-{:d} {:02d}:{:02d}:{:02d}'.format(datetime[0],
        datetime[1], datetime[2], datetime[4], datetime[5], datetime[6])

def calories(user, steps):
    return steps * user.cal_factor

def compile_data():
    steps = lis3dh.get_steps()
    data = {}
    data['temp'] = tmp007.read_obj_temp_c()             # add temperature
    data['time'] = formatted_datetime(rtc.datetime())   # add time stamp
    data['steps'] = steps                               # add step
    data['cal'] = calories(u, steps)                    # add expended calories
    return data



#//////////////////// main program definition /////////////////////////////////
def main():
    # initialise sensors and MQTT publisher
    if not tmp007.init():
        print('TMP007 initialisation unsuccessful - is the sensor connected?')
        return

    if not lis3dh.init(2, 20):
        print('LIS3DH initialisation unsuccessful - is the sensor connected?')
        return

    if not mp.init():
        print('Error connecting to MQTT: connection timed out.')
        return

    # display info about pedometer
    print(
    '''LIS3DH pedometer
    Acceleration
        unit: g
        range: +/- {0}g.
    Distance
        unit: m
TMP007
    unit: C (Celsius)
    range: +/- 256C'''.format(lis3dh.range_g))

    # keep reading data to keep everything updated, but transmission to MQTT is
    #   less frequent in order to reduce network traffic, as much of the data
    #   values are repeated
    send_timer = -SEND_INTERVAL
    while True:
        data = compile_data()
        if utime.time() - send_timer >= SEND_INTERVAL:
            # print(ujson.dumps(data))
            mp.publish(data)
            send_timer = utime.time()



#//////////////////// call main() /////////////////////////////////////////////
main()