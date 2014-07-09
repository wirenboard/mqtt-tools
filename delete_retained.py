#!/usr/bin/python
import argparse

import mosquitto
import time, random
import sys

retain_hack_topic = None
client = None

topics_to_unpublish = set()
unpublished_topics = set()

def on_mqtt_message(msg):
    #~ print "on_mqtt_message", msg
    print msg.topic
    if msg.topic != retain_hack_topic:
        topics_to_unpublish.add(msg.topic)
    else:
        client.on_publish = on_mqtt_publish
        client.unsubscribe(args.topic)
        for topic in topics_to_unpublish:
            print topic
            ret = client.publish(topic, '', retain=True)

            mid = ret[1]
            unpublished_topics.add(mid)
#            print "mid", ret, mid


def on_mqtt_publish(mid):
#    print "on publish", mid
    unpublished_topics.discard(mid)
    if not unpublished_topics:
        print "done!"
        client.disconnect()

if __name__ =='__main__':
    parser = argparse.ArgumentParser(description='MQTT retained message deleter', add_help=False)

    parser.add_argument('-h', '--host', dest='host', type=str,
                     help='MQTT host', default='localhost')

    parser.add_argument('-p', '--port', dest='port', type=int,
                     help='MQTT port', default='1883')

    parser.add_argument('topic' ,  type=str,
                     help='Topic mask to unpublish retained messages from. For example: "/devices/my-device/#"')
    args = parser.parse_args()


    mqtt_device_id = str(time.time()) + str(random.randint(0,100000))
    client = mosquitto.Mosquitto(mqtt_device_id)
    client.connect(args.host, args.port)
    client.on_message = on_mqtt_message


    client.subscribe(args.topic)

    # hack to get retained settings first:
    retain_hack_topic = "/tmp/%s/retain_hack" % ( mqtt_device_id)
    client.subscribe(retain_hack_topic)
    client.publish(retain_hack_topic, '1')

    while 1:
        rc = client.loop()
        if rc != 0:
            break
