# use MicroPython to communicate between ESP8266 and LIS3DH via I2C

# LIS3DH library for MicroPython

print('\n\n\nBegin main.py')

### imports
from machine import Pin, I2C

# address
LIS3DH_DEFAULT_ADDRESS  = 0x18 # if SDO/SA0 is 3V, it's 0x19

# registers
LIS3DH_REG_STATUS1      = 0x07
LIS3DH_REG_OUTADC1_L    = 0x08
LIS3DH_REG_OUTADC1_H    = 0x09
LIS3DH_REG_OUTADC2_L    = 0x0A
LIS3DH_REG_OUTADC2_H    = 0x0B
LIS3DH_REG_OUTADC3_L    = 0x0C
LIS3DH_REG_OUTADC3_H    = 0x0D
LIS3DH_REG_INTCOUNT     = 0x0E
LIS3DH_REG_WHOAMI       = 0x0F
LIS3DH_REG_TEMPCFG      = 0x1F
LIS3DH_REG_CTRL1        = 0x20
LIS3DH_REG_CTRL2        = 0x21
LIS3DH_REG_CTRL3        = 0x22
LIS3DH_REG_CTRL4        = 0x23
LIS3DH_REG_CTRL5        = 0x24
LIS3DH_REG_CTRL6        = 0x25
LIS3DH_REG_REFERENCE    = 0x26
LIS3DH_REG_STATUS2      = 0x27
LIS3DH_REG_OUT_X_L      = 0x28
LIS3DH_REG_OUT_X_H      = 0x29
LIS3DH_REG_OUT_Y_L      = 0x2A
LIS3DH_REG_OUT_Y_H      = 0x2B
LIS3DH_REG_OUT_Z_L      = 0x2C
LIS3DH_REG_OUT_Z_H      = 0x2D
LIS3DH_REG_FIFOCTRL     = 0x2E
LIS3DH_REG_FIFOSRC      = 0x2F
LIS3DH_REG_INT1CFG      = 0x30
LIS3DH_REG_INT1SRC      = 0x31
LIS3DH_REG_INT1THS      = 0x32
LIS3DH_REG_INT1DUR      = 0x33
LIS3DH_REG_CLICKCFG     = 0x38
LIS3DH_REG_CLICKSRC     = 0x39
LIS3DH_REG_CLICKTHS     = 0x3A
LIS3DH_REG_TIMELIMIT    = 0x3B
LIS3DH_REG_TIMELATENCY  = 0x3C
LIS3DH_REG_TIMEWINDOW   = 0x3D
LIS3DH_REG_ACTTHS       = 0x3E
LIS3DH_REG_ACTDUR       = 0x3F

# range
LIS3DH_RANGE_16_G       = 0b11 # +/- 16g
LIS3DH_RANGE_8_G        = 0b10 # +/- 8g
LIS3DH_RANGE_4_G        = 0b01 # +/- 4g
LIS3DH_RANGE_2_G        = 0b00 # +/- 2g (default)

# axis
LIS3DH_AXIS_X           = 0x0
LIS3DH_AXIS_Y           = 0x1
LIS3DH_AXIS_Z           = 0x2

# data rate: used with LIS3DH_REG_CTRL_REG1 to set bandwidth
LIS3DH_DATARATE_400_HZ          = 0b0111 # 400Hz 
LIS3DH_DATARATE_200_HZ          = 0b0110 # 200Hz
LIS3DH_DATARATE_100_HZ          = 0b0101 # 100Hz
LIS3DH_DATARATE_50_HZ           = 0b0100 # 50Hz
LIS3DH_DATARATE_25_HZ           = 0b0011 # 25Hz
LIS3DH_DATARATE_10_HZ           = 0b0010 # 10Hz
LIS3DH_DATARATE_1_HZ            = 0b0001 # 1Hz
LIS3DH_DATARATE_POWERDOWN       = 0
LIS3DH_DATARATE_LOWPOWER_1K6HZ  = 0b1000
LIS3DH_DATARATE_LOWPOWER_5KHZ   = 0b1001


### variables
_i2c_port = 0
_i2c_addr = -1

### functions

# initialisation
# def init(i2c_addr = LIS3DH_DEFAULT_ADDRESS, scl = 5, sda = 4, freq = 400000):
   # _i2c_addr = i2c_addr
   # _i2c_port = I2C(Pin(scl), Pin(sda), freq)

# begin I2C communication
def begin():
    print("Beginning I2C communication")
    
    device_id = _i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_WHOAMI, 1)
    print('device_id:', hex(ord(device_id)));
    if ord(device_id) != 0x33:
        print("FAILURE: LIS3DH not detected at {0}".format(_i2c_addr))
        return False
    else:
        print("SUCCESS: LIS3DH detected at {0}".format(_i2c_addr))
        _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_CTRL1, bytearray([0x07]))    # enable all axes, normal mode
        set_data_rate(LIS3DH_DATARATE_400_HZ)  # 400Hz rate
        _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_CTRL4, bytearray([0x88]))    # High res & BDU enabled
        _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_CTRL3, bytearray([0x10]))    # DRDY on INT1
        _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_TEMPCFG, bytearray([0x80]))  # enable adcs
        return True

def set_data_rate(data_rate):
    ctl1 = ord(_i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_CTRL1, 1))
    ctl1 &= ~(0xF0) # mask off bits
    ctl1 |= (data_rate << 4)
    _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_CTRL1, bytearray([ctl1]))

# read x y z at once
def read_from_sensor():
    data = []

    range = get_range()
    divider = 1
    if (range == LIS3DH_RANGE_16_G):
        divider = 1365 # different sensitivity at 16g
    if (range == LIS3DH_RANGE_8_G):
        divider = 4096
    if (range == LIS3DH_RANGE_4_G):
        divider = 8190
    if (range == LIS3DH_RANGE_2_G):
        divider = 16380

    x_MSB = ord(_i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_OUT_X_H, 1)) # read X high byte register
    x_LSB = ord(_i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_OUT_X_L, 1)) # read X low byte register
    y_MSB = ord(_i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_OUT_Y_H, 1))
    y_LSB = ord(_i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_OUT_Y_L, 1))
    z_MSB = ord(_i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_OUT_Z_H, 1))
    z_LSB = ord(_i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_OUT_Z_L, 1))

    data.append(uin16_to_int16((x_MSB << 8) | (x_LSB))/divider)
    data.append(uin16_to_int16((y_MSB << 8) | (y_LSB))/divider)
    data.append(uin16_to_int16((z_MSB << 8) | (z_LSB))/divider)
    
    return data

def uin16_to_int16(uint16):
    result = uint16
    if result > 32767:
        result -= 65536
    return result

def get_range():
    # read the data format register to preserve bits
    r = ord(_i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_CTRL4, 1))
    r = (r >> 4) & 0x03
    return r


#import LIS3DH

#init(i2c_addr = LIS3DH_DEFAULT_ADDRESS, scl = 5, sda = 4, freq = 400000)
_i2c_addr = LIS3DH_DEFAULT_ADDRESS
_i2c_port = I2C(scl = Pin(5), sda = Pin(4), freq = 400000)

print('init() finished')

#print(_i2c_port.scan())
#LIS3DH.begin()
begin()

print('begin() finished')
get_range

#data = LIS3DH.read()
d = 0

range = get_range()
print('range', range)

while True:
#for i in range(5):
    d = read_from_sensor()
    print("x=%.4f,\ty=%.4f,\tz=%.4f" % (d[0], d[1], d[2]))
