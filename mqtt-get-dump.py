#!/usr/bin/python
import argparse

try:
    import mosquitto
except ImportError:
    import paho.mqtt.client as mosquitto

import time, random
import sys



def on_mqtt_message(arg0, arg1, arg2=None):
    #
    #~ print "on_mqtt_message", arg0, arg1, arg2
    if arg2 is None:
        mosq, obj, msg = None, arg0, arg1
    else:
        mosq, obj, msg = arg0, arg1, arg2


    if msg.topic != retain_hack_topic:
        print "%s\t%s" % (msg.topic, msg.payload)
    else:


        #~ print "done!"
        client.disconnect()
        sys.exit(0)


if __name__ =='__main__':
    parser = argparse.ArgumentParser(description='MQTT retained message deleter', add_help=False)

    parser.add_argument('-h', '--host', dest='host', type=str,
                     help='MQTT host', default='localhost')

    parser.add_argument('-u', '--username', dest='username', type=str,
                     help='MQTT username', default='')

    parser.add_argument('-P', '--password', dest='password', type=str,
                     help='MQTT password', default='')

    parser.add_argument('-p', '--port', dest='port', type=int,
                     help='MQTT port', default='1883')

    parser.add_argument('topic' ,  type=str,
                     help='Topic mask to unpublish retained messages from. For example: "/devices/my-device/#"')

    args = parser.parse_args()


    client = mosquitto.Mosquitto()

    if args.username:
        client.username_pw_set(args.username, args.password)

    client.connect(args.host, args.port)
    client.on_message = on_mqtt_message


    client.subscribe(args.topic)

    # hack to get retained settings first:
    retain_hack_topic = "/tmp/%s/retain_hack" % ( client._client_id)
    client.subscribe(retain_hack_topic)
    client.publish(retain_hack_topic, '1')

    while 1:
        rc = client.loop()
        if rc != 0:
            break
