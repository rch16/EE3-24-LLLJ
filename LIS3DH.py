# LIS3DH library for MicroPython

### imports
from machine import Pin, I2C

### I2C

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
def init(i2c_addr = LIS3DH_DEFAULT_ADDRESS, scl = -1, sda = -1, freq = 400000):
    _i2c_addr = i2c_addr
    _i2c_port = I2C(scl, sda, freq)

# begin I2C communication
def begin():
    print("Beginning I2C communication")
    
    device_id = _i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_WHOAMI, 1)
    if deviceid != 0x33:
        print("FAILURE: LIS3DH not detected at {0}".format(_i2c_addr))
        return false
    else:
        print("SUCCESS: LIS3DH detected at {0}".format(_i2c_addr))
        _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_CTRL1, 0x07)    # enable all axes, normal mode
        set_data_rate(_i2c_addr, LIS3DH_DATARATE_400_HZ)  # 400Hz rate
        _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_CTRL4, 0x88)    # High res & BDU enabled
        _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_CTRL3, 0x10)    # DRDY on INT1
        _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_TEMPCFG, 0x80)  # enable adcs
        return true

def set_data_rate(data_rate):
    ctl1 = _i2c_port.readfrom_mem(_i2c_addr, LIS3DH_REG_CTRL1, 1)
    ctl1 &= ~(0xF0) # mask off bits
    ctl1 |= (data_rate << 4)
    _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_CTRL1, ctl1)

# read x y z at once
def read():
    _i2c_port.writeto_mem(_i2c_addr, LIS3DH_REG_OUT_X_L | 0x80)
    data = _i2c_port.readfrom(_i2c_addr, 6)
    print("data: {0}".format(data))

