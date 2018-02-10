# MQTT for Micropython test

from umqtt.simple import MQTTClient
import machine
import ujson
import utime
import network

# parameters
CLIENT_ID = machine.unique_id() # b'K\x9b\xc6\x00'
BROKER_ADDRESS = '192.168.0.10'
TOPIC = 'esys/LLLJ/pedometer'
ESSID = 'EEERover'
PASSWORD = 'exhibition'

print('Client ID: {0}'.format(CLIENT_ID))

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

#all_wlan = str(sta_if.scan()) # show all available WLAN
#if all_wlan.find(ESSID) == -1:
#    print('{0} not found!'.format(ESSID))

print('Connecting to Wi-Fi...')
while not sta_if.isconnected():
    sta_if.connect(ESSID, PASSWORD)
    utime.sleep(1)      # wait before attempting to reconnect
print('Connected!')

print('Connecting to MQTT broker...')
client = MQTTClient(CLIENT_ID, BROKER_ADDRESS)
client.connect()
print('Connected!')

print('Sending data...')
while True:
    # get new data
    data = ujson.dumps({'x':0, 'y':0, 'z':1}) # JSON data
    client.publish(TOPIC, bytes(data, 'utf-8'))
    print('Data published: {0}'.format(data))
