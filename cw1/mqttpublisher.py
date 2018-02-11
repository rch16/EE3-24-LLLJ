''' MQTT for MicroPython test'''



#//////////////////// imports ////////////////////
from umqtt.simple import MQTTClient
import machine
import ujson
import utime
import network
import usocket



#//////////////////// parameters ////////////////////
CLIENT_ID = machine.unique_id() # b'K\x9b\xc6\x00'
BROKER_ADDRESS = '192.168.0.10'
TOPIC = '/esys/LLLJ/pedometer'
ESSID = 'EEERover'
PASSWORD = 'exhibition'
RECONNECT_INTERVAL = 1  # unit: second. Time interval attempting reconnect to Wi-Fi
WLAN_TIMEOUT = 10       # unit: second. Timeout for connecting to WLAN



#//////////////////// variables ////////////////////
sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
client = MQTTClient(CLIENT_ID, BROKER_ADDRESS)



#//////////////////// functions ////////////////////
def init():
    global client

    print('MQTT client ID: {0}'.format(CLIENT_ID))

    #all_wlan = str(sta_if.scan()) # show all available WLAN
    #if all_wlan.find(ESSID) == -1:
    #    print('{0} not found!'.format(ESSID))

    print('Connecting to Wi-Fi', end='')
    start_time = utime.time()
    time_elapsed = 0
    is_timed_out = False
    while (not sta_if.isconnected()) and (not is_timed_out):
        sta_if.connect(ESSID, PASSWORD)
        print('.', end='')
        utime.sleep(RECONNECT_INTERVAL)      # wait before attempting to reconnect
        time_elapsed = utime.time() - start_time
        if time_elapsed >= WLAN_TIMEOUT:
            is_timed_out = True
    print(' ')
    if is_timed_out:
        return False
    else:
        print('Connected!')

        print('Connecting to MQTT broker...')
        client.connect()
        print('Connected!')
        
        return True

def publish(data):
    global client

    payload = ujson.dumps(data) # JSON data
    client.publish(TOPIC, bytes(payload, 'utf-8'))
    print('Data published: {0}'.format(payload))
