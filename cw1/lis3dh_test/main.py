''' LIS3DH library for MicroPython
    LIS3DH: a triple-axis accelerometer
    register size: 8 bits
'''



#//////////////////// imports ////////////////////
from machine import Pin, I2C
import utime



#//////////////////// constants ////////////////////
# register addresses etc.
LIS3DH_DEFAULT_ADDRESS  = 0x18 # default I2C address. If SDO/SA0 is 3V -> 0x19
LIS3DH_DEVICE_ID        = 0x33 # device ID expected to be found in LIS3DH_REG_WHOAMI

LIS3DH_REG_STATUS1      = 0x07 # registers
LIS3DH_REG_OUTADC1_L    = 0x08
LIS3DH_REG_OUTADC1_H    = 0x09
LIS3DH_REG_OUTADC2_L    = 0x0A
LIS3DH_REG_OUTADC2_H    = 0x0B
LIS3DH_REG_OUTADC3_L    = 0x0C
LIS3DH_REG_OUTADC3_H    = 0x0D
LIS3DH_REG_INTCOUNT     = 0x0E
LIS3DH_REG_WHOAMI       = 0x0F # register storing device ID (for checking if sensor connected)
LIS3DH_REG_TEMPCFG      = 0x1F
LIS3DH_REG_CTRL1        = 0x20
LIS3DH_REG_CTRL2        = 0x21
LIS3DH_REG_CTRL3        = 0x22
LIS3DH_REG_CTRL4        = 0x23
LIS3DH_REG_CTRL5        = 0x24
LIS3DH_REG_CTRL6        = 0x25
LIS3DH_REG_REFERENCE    = 0x26
LIS3DH_REG_STATUS2      = 0x27
LIS3DH_REG_OUT_X_L      = 0x28 # X-axis low byte
LIS3DH_REG_OUT_X_H      = 0x29 # X-axis high byte
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

LIS3DH_RANGE_16_G       = 0b11 # range. +/- 16g
LIS3DH_RANGE_8_G        = 0b10 # +/- 8g
LIS3DH_RANGE_4_G        = 0b01 # +/- 4g
LIS3DH_RANGE_2_G        = 0b00 # +/- 2g (default)

LIS3DH_AXIS_X           = 0x0  # axis
LIS3DH_AXIS_Y           = 0x1
LIS3DH_AXIS_Z           = 0x2

LIS3DH_DATARATE_400_HZ          = 0b0111 # data rate: for setting bandwidth. 400Hz 
LIS3DH_DATARATE_200_HZ          = 0b0110 # 200Hz
LIS3DH_DATARATE_100_HZ          = 0b0101 # 100Hz
LIS3DH_DATARATE_50_HZ           = 0b0100 # 50Hz
LIS3DH_DATARATE_25_HZ           = 0b0011 # 25Hz
LIS3DH_DATARATE_10_HZ           = 0b0010 # 10Hz
LIS3DH_DATARATE_1_HZ            = 0b0001 # 1Hz
LIS3DH_DATARATE_POWERDOWN       = 0
LIS3DH_DATARATE_LOWPOWER_1K6HZ  = 0b1000
LIS3DH_DATARATE_LOWPOWER_5KHZ   = 0b1001




#//////////////////// variables ////////////////////

_i2c_addr = LIS3DH_DEFAULT_ADDRESS
_i2c_port = I2C(scl = Pin(5), sda = Pin(4), freq = 400000)

range_g = 0 # sensor range as +/- *g
divider = 1 # depends on range. Acceleration in g = sensor data / divider

GRAVITY = 9806.65 # unit: mm s^(-2)



#//////////////////// functions ////////////////////

## "private" functions

# begin I2C communication
def begin_i2c():
    print("Begin I2C communication...")
    
    device_id = read_mem_8(LIS3DH_REG_WHOAMI)
    #print('LIS3DH device_id: {0}'.format(hex(device_id)))

    if device_id != LIS3DH_DEVICE_ID:
        print("FAILURE: LIS3DH not detected at address {0}".format(hex(_i2c_addr)))
        return False    # sensor not found
    else:
        print("SUCCESS: LIS3DH detected at {0}".format(hex(_i2c_addr)))
        write_mem_8(LIS3DH_REG_CTRL1, 0x07)       # enable all axes, normal mode
        set_data_rate(LIS3DH_DATARATE_400_HZ)   # 400Hz rate
        write_mem_8(LIS3DH_REG_CTRL4, 0x88)       # high res & BDU enabled
        write_mem_8(LIS3DH_REG_CTRL3, 0x10)       # DRDY on INT1
        write_mem_8(LIS3DH_REG_TEMPCFG, 0x80)     # enable adcs
        return True     # sensor found and initialised

def set_data_rate(data_rate):
    ctl1 = read_mem_8(LIS3DH_REG_CTRL1)
    ctl1 &= ~(0xF0) # mask off bits
    ctl1 |= (data_rate << 4)
    write_mem_8(LIS3DH_REG_CTRL1, ctl1)

def read_from_sensor(): # read x y z at once
    data = {}

    x_MSB = read_mem_8(LIS3DH_REG_OUT_X_H) # read X high byte register
    x_LSB = read_mem_8(LIS3DH_REG_OUT_X_L) # read X low byte register
    y_MSB = read_mem_8(LIS3DH_REG_OUT_Y_H)
    y_LSB = read_mem_8(LIS3DH_REG_OUT_Y_L)
    z_MSB = read_mem_8(LIS3DH_REG_OUT_Z_H)
    z_LSB = read_mem_8(LIS3DH_REG_OUT_Z_L)

    data['x'] = (uint16_to_int16((x_MSB << 8) | (x_LSB))/divider)
    data['y'] = (uint16_to_int16((y_MSB << 8) | (y_LSB))/divider)
    data['z'] = (uint16_to_int16((z_MSB << 8) | (z_LSB))/divider)
    
    return data

def uint16_to_int16(uint16):
    result = uint16
    if result > 32767:
        result -= 65536
    return result

def get_range():        # read the data format register to preserve bits
    r = read_mem_8(LIS3DH_REG_CTRL4)
    r = (r >> 4) & 0x03
    return r

def init_all_param():   # initialise all global parameters
    global divider
    global range_g
    range = get_range()
    if (range == LIS3DH_RANGE_16_G):
        range_g = 16
        divider = 1365  # different sensitivity at 16g
    if (range == LIS3DH_RANGE_8_G):
        range_g = 8
        divider = 4096
    if (range == LIS3DH_RANGE_4_G):
        range_g = 4
        divider = 8190
    if (range == LIS3DH_RANGE_2_G):
        range_g = 2
        divider = 16380

def write_mem_8(reg_addr, data):
    _i2c_port.writeto_mem(_i2c_addr, reg_addr, bytearray([data]))

def read_mem(reg_addr, nbytes):
    str = _i2c_port.readfrom_mem(_i2c_addr, reg_addr, nbytes)
    result = 0
    counter = 0
    for char in str:
        result = result << counter | char
        counter += 8
    return result
    
def read_mem_8(reg_addr):
    return read_mem(reg_addr, 1)

def addr_detected():
    if _i2c_addr in _i2c_port.scan():
        return True
    else:
        return False

# "public" functions

def init():
    if not addr_detected():
        return False
    else:
        begin_i2c()
        init_all_param()
        return True

def get_accel():
    data = read_from_sensor()
    return data

if init():
    while True:
        accel = get_accel()
        print('x = {:f},\ty = {:f},\tz = {:f}'.format(accel['x'],accel['y'],accel['z']))
        utime.sleep(0.1)
else:
    print('Nothing detected at address {0}'.format(_i2c_addr))
    