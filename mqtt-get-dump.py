#!/usr/bin/env python3
import argparse
import random
import sys
import time

import paho.mqtt.client as mqtt


class GetDumpTool:
    def __init__(self, host, port, username, password, topic, ret_topic):
        self.client = mqtt.Client()

        if username:
            self.client.username_pw_set(username, password)

        self.host = host
        self.port = port
        self.topic = topic
        self.ret_topic = ret_topic

    def run(self):
        self.client.connect(self.host, self.port)
        self.client.on_message = self.on_mqtt_message

        self.client.subscribe(self.topic)

        # hack to get retained settings first:
        self.client.subscribe(self.ret_topic)
        self.client.publish(self.ret_topic, "1")

        while 1:
            ret = self.client.loop()
            if ret != 0:
                break

    def on_mqtt_message(self, _, arg1, arg2=None):
        if arg2 is None:
            msg = arg1
        else:
            msg = arg2

        if msg.topic != self.ret_topic:
            print("%s\t%s" % (msg.topic, msg.payload.decode("utf-8").replace("\n", "\\\n")))
        else:
            self.client.disconnect()
            sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT retained message deleter", add_help=False)

    parser.add_argument("-h", "--host", dest="host", type=str, help="MQTT host", default="localhost")

    parser.add_argument("-u", "--username", dest="username", type=str, help="MQTT username", default="")

    parser.add_argument("-P", "--password", dest="password", type=str, help="MQTT password", default="")

    parser.add_argument("-p", "--port", dest="port", type=int, help="MQTT port", default="1883")

    mqtt_device_id = str(time.time()) + str(random.randint(0, 100000))

    parser.add_argument(
        "--ret-topic",
        dest="ret_topic",
        type=str,
        help="Topic to write temporary message to",
        default="/tmp/%s/retain_hack" % (mqtt_device_id),
    )

    parser.add_argument(
        "topic",
        type=str,
        help='Topic mask to unpublish retained messages from. For example: "/devices/my-device/#"',
    )

    args = parser.parse_args()

    tool = GetDumpTool(
        args.host,
        args.port,
        args.username,
        args.password,
        args.topic,
        args.ret_topic,
    )
    tool.run()
