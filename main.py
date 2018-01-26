# use MicroPython to communicate between ESP8266 and LIS3DH via I2C

import LIS3DH

LIS3DH.init(scl = 5, sda = 4, freq = 400000)

LIS3DH.begin()

data = LIS3DH.read()