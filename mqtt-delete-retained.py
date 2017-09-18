#!/usr/bin/python
import argparse

try:
    import mosquitto
except ImportError:
    import paho.mqtt.client as mosquitto

import time, random
import progressbar
import sys

pb_widgets=[progressbar.Percentage(), progressbar.Bar(left=" [", right="] "), progressbar.SimpleProgress()]

retain_hack_topic = None
client = None
verbose = False

pb = None
total = 0
published = 0

topics_to_unpublish = set()
unpublished_topics = set()

def on_mqtt_message(arg0, arg1, arg2=None):
    global total, pb

    #
    #~ print "on_mqtt_message", arg0, arg1, arg2
    if arg2 is None:
        mosq, obj, msg = None, arg0, arg1
    else:
        mosq, obj, msg = arg0, arg1, arg2

    if verbose:
        print(msg.topic)

    if msg.topic != retain_hack_topic:
        topics_to_unpublish.add(msg.topic)
        total += 1
    else:
        client.on_publish = on_mqtt_publish
        client.unsubscribe(args.topic)
        if topics_to_unpublish:
            pb = progressbar.ProgressBar(widgets=pb_widgets, maxval=total, term_width=79).start()
            for topic in topics_to_unpublish:
                if verbose:
                    print(topic)
                ret = client.publish(topic, '', retain=True, qos=2)

                mid = ret[1]
                unpublished_topics.add(mid)
        #            print "mid", ret, mid
        else:
            # print "done!"
            if pb:
                pb.finish()
            else:
                print("warning: no messages for this topic")
            client.disconnect()
            sys.exit(0)


def on_mqtt_publish(arg0, arg1, arg2=None):
    global published, pb
    mid = arg1 or arg2
    if pb:
        published += 1
        pb.update(published)
    unpublished_topics.discard(mid)
    if not unpublished_topics:
        if verbose:
            print("topics published")
        if pb:
            pb.finish()
        client.disconnect()
        sys.exit(0)


if __name__ =='__main__':
    parser = argparse.ArgumentParser(description='MQTT retained message deleter', add_help=False)
    parser.add_argument('-v', '--verbose', dest='verbose', action="store_true",
                        help="Verbose output")

    parser.add_argument('-h', '--host', dest='host', type=str,
                     help='MQTT host', default='localhost')

    parser.add_argument('-p', '--port', dest='port', type=int,
                     help='MQTT port', default='1883')

    parser.add_argument('-u', '--username', dest='username', type=str,
                     help='MQTT username', default='')

    parser.add_argument('-P', '--password', dest='password', type=str,
                     help='MQTT password', default='')

    mqtt_device_id = str(time.time()) + str(random.randint(0,100000))

    parser.add_argument('--ret-topic', dest='ret_topic', type=str,
                     help='Topic to write temporary message to', default="/tmp/%s/retain_hack" % ( mqtt_device_id))

    parser.add_argument('topic' ,  type=str,
                     help='Topic mask to unpublish retained messages from. For example: "/devices/my-device/#"')

    args = parser.parse_args()

    verbose = args.verbose

    retain_hack_topic = args.ret_topic
    client = mosquitto.Mosquitto(mqtt_device_id)

    if args.username:
        client.username_pw_set(args.username, args.password)

    client.connect(args.host, args.port)
    client.on_message = on_mqtt_message


    client.subscribe(args.topic)

    # hack to get retained settings first:
    client.subscribe(retain_hack_topic)
    client.publish(retain_hack_topic, '1')

    while 1:
        rc = client.loop()
        if rc != 0:
            break
