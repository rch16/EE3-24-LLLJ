# Coursework 1: smart pedometer

## Chips used
| Name | Description |
|-|-|
| ESP8266 | Wi-Fi module |
| LIS3DH | Tri-axis accelerometer |
| TMP007 | Contact-less temperature sensor |

## Functionality
- use MicroPython to communicate between ESP8266 and sensors (LIS3DH and TMP007)
- use MQTT to publish/subscribe to sensor data
- step counting and calories calculation done on ESP8266

## Usage

- install `ampy` for Python 3

  ```
  sudo pip3 install adafruit-ampy
  ```

- connect the sensors to ESP8266 via I2C

- connect ESP8266 to a PC via USB

- upload `main.py` to ESP8266

  ```
  sudo ampy --port /dev/ttyS* put main.py
  ```

- open serial port to communicate with the ESP8266

  ```
  sudo microcom -p /dev/ttyS* -s 115200
  ```

## References

- [Adafruit `ampy` usage](https://cdn-learn.adafruit.com/downloads/pdf/micropython-basics-load-files-and-run-code.pdf)

- [`microcom` usage](http://manpages.ubuntu.com/manpages/xenial/man1/microcom.1.html)