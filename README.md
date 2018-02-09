# LLLJ

EE3-24 Embedded Systems group project

Group name: LLLJ

Description:

Coursework 1: use MicroPython to communicate between ESP8266 (WiFi module) and LIS3DH (motion sensor)

## Usage

- install `ampy`

  `sudo pip3 install adafruit-ampy`

- connect ESP8266 to a PC via USB

- upload `main.py` to ESP8266

  `sudo ampy --port /dev/ttyS* put main.py`

- open serial port to communicate with the ESP8266

  `sudo microcom -p /dev/ttyS* -s 115200`

## References

- [Adafruit `ampy` usage](https://cdn-learn.adafruit.com/downloads/pdf/micropython-basics-load-files-and-run-code.pdf)

- [`microcom` usage](http://manpages.ubuntu.com/manpages/xenial/man1/microcom.1.html)