# use MicroPython to communicate between ESP8266 and LIS3DH via I2C

print('Begin main.py')

import LIS3DH

LiIS3DH.init(scl = 5, sda = 4, freq = 400000)

print('init finished')

LIS3DH.begin()

print('begin finished')

LIS3DH.read()
