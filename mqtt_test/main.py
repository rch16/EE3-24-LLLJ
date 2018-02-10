# MQTT for Micropython test

from umqtt.simple import MQTTClient
import machine
import ujson
import utime
import network
import usocket

# parameters
CLIENT_ID = machine.unique_id() # b'K\x9b\xc6\x00'
BROKER_ADDRESS = '192.168.0.10'
TOPIC = '/esys/LLLJ/pedometer'
ESSID = 'EEERover'
PASSWORD = 'exhibition'
SEND_INTERVAL = 2       # unit: second. Time interval for publishing to MQTT
RECONNECT_INTERVAL = 1  # unit: second. Time interval attempting reconnect to Wi-Fi

# variable
rtc = machine.RTC()                     # RTC clock
rtc.datetime((2018,2,10,5,17,23,0,0))   # intialise

# functions
def formatted_datetime(datetime):
    return '{:d}-{:d}-{:d} {:02d}:{:02d}:{:02d}'.format(datetime[0], datetime[1], datetime[2], datetime[4], datetime[5], datetime[6])

# main program
print('Client ID: {0}'.format(CLIENT_ID))

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

#all_wlan = str(sta_if.scan()) # show all available WLAN
#if all_wlan.find(ESSID) == -1:
#    print('{0} not found!'.format(ESSID))

print('Connecting to Wi-Fi...')
while not sta_if.isconnected():
    sta_if.connect(ESSID, PASSWORD)
    utime.sleep(RECONNECT_INTERVAL)      # wait before attempting to reconnect
print('Connected!')

print('Connecting to MQTT broker...')
client = MQTTClient(CLIENT_ID, BROKER_ADDRESS)
client.connect()
print('Connected!')

print('Sending data...')
while True:
    # get new data
    data = {'x':0, 'y':0, 'z':1}
    data['time'] = formatted_datetime(rtc.datetime())

    payload = ujson.dumps(data) # JSON data
    client.publish(TOPIC, bytes(payload, 'utf-8'))
    print('Data published: {0}'.format(payload))
    utime.sleep(SEND_INTERVAL)
