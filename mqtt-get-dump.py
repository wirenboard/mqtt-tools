#!/usr/bin/env python3
import argparse
import sys

from wb_common.mqtt_client import DEFAULT_BROKER_URL, MQTTClient


class GetDumpTool:
    def __init__(self, client_id, broker_url, topic):
        self.client = MQTTClient(client_id, broker_url, False)

        self.topic = topic
        self.ret_topic = "/tmp/%s/retain_hack" % self.client._client_id

    def run(self):
        self.client.start()
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
            self.client.stop()
            sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT get dump", add_help=False)
    parser.add_argument(
        "-b",
        "--broker",
        dest="broker_url",
        type=str,
        help="MQTT broker url",
        default=DEFAULT_BROKER_URL,
    )
    parser.add_argument(
        "topic",
        type=str,
        help='Topic mask to unpublish retained messages from. For example: "/devices/my-device/#"',
    )

    args = parser.parse_args()

    tool = GetDumpTool(
        "mqtt-get-dump",
        args.broker_url,
        args.topic,
    )
    tool.run()
