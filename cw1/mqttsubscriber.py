#!/usr/bin/python3.5



#//////////////////// imports /////////////////////////////////////////////////
import paho.mqtt.client as mqtt
import json



#//////////////////// parameters //////////////////////////////////////////////
TOPIC = '/esys/LLLJ/pedometer'
BROKER_ADDRESS = '192.168.0.10'



#//////////////////// functions ///////////////////////////////////////////////
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(TOPIC)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    process_data(msg.payload)

# Process received data
def process_data(d):
    data = json.loads(d.decode("utf-8"))
    print('''Time: {0}
Steps: {1}
Calories Expended: {2} cal
Temperature: {3} Celsius
'''.format(data['time'], data['steps'], data['cal'], data['temp']))



#//////////////////// main program ////////////////////////////////////////////
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_ADDRESS, 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()