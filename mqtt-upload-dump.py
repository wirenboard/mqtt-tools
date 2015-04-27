#!/usr/bin/python
import argparse

import mosquitto
import time, random
import sys


last_mid = None
def on_mqtt_publish(arg0, arg1, arg2=None):
    #~ global last_mid
    mid = arg1 or arg2
    #~ print mid, last_mid
    if last_mid and (last_mid == mid):
        client.disconnect()
        sys.exit(0)


if __name__ =='__main__':
    parser = argparse.ArgumentParser(description='publish mqtt messages to broker', add_help=False)

    parser.add_argument('-h', '--host', dest='host', type=str,
                     help='MQTT host', default='localhost')

    parser.add_argument('-p', '--port', dest='port', type=int,
                     help='MQTT port', default='1883')

    parser.add_argument('filename' ,  type=str,
                     help='File containing MQTT dump.  Topic and message are separated by tab')

    args = parser.parse_args()


    client = mosquitto.Mosquitto()
    client.connect(args.host, args.port)
    client.on_publish = on_mqtt_publish

    mid = None
    for line in open(args.filename):
        topic, message = line[:-1].split('\t', 1)
        #~ print topic
        status, mid = client.publish(topic, message, retain=True, qos=2)
    last_mid = mid
    #~ print "last: ", last_mid

    while 1:
        rc = client.loop()
        if rc != 0:
            break

