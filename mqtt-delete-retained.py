#!/usr/bin/env python3
import argparse
import sys

import tqdm
from wb_common.mqtt_client import DEFAULT_BROKER_URL, MQTTClient


class DeleteRetainedTool:
    def __init__(self, client_id, broker_url, topic, verbose=False):
        self.pbar = None
        self.total = 0

        self.verbose = verbose

        self.topics_to_unpublish = set()
        self.unpublished_topics = set()

        self.client = MQTTClient(client_id, broker_url, False)
        self.topic = topic
        self.retain_hack_topic = "/tmp/%s/retain_hack" % self.client._client_id.decode()

    def run(self):
        self.client.start()
        self.client.on_message = self.on_mqtt_message

        self.client.subscribe(self.topic)

        # hack to get retained settings first:
        self.client.subscribe(self.retain_hack_topic)
        self.client.publish(self.retain_hack_topic, "1")

        while 1:
            ret = self.client.loop()
            if ret != 0:
                break

    def on_mqtt_message(self, _, arg1, arg2=None):
        if arg2 is None:
            msg = arg1
        else:
            msg = arg2

        if self.verbose:
            print(msg.topic)

        if msg.topic != self.retain_hack_topic:
            self.topics_to_unpublish.add(msg.topic)
            self.total += 1
        else:
            self.client.on_publish = self.on_mqtt_publish
            self.client.unsubscribe(args.topic)
            if self.topics_to_unpublish:
                self.pbar = tqdm.tqdm(total=self.total)
                for topic in self.topics_to_unpublish:
                    if self.verbose:
                        print(topic)
                    ret = self.client.publish(topic, "", retain=True, qos=2)

                    mid = ret[1]
                    self.unpublished_topics.add(mid)
            else:
                if self.pbar:
                    self.pbar.close()
                else:
                    print("warning: no messages for this topic")
                self.client.stop()
                sys.exit(0)

    def on_mqtt_publish(self, _, arg1, arg2=None):
        mid = arg1 or arg2
        if self.pbar and mid in self.unpublished_topics:
            self.pbar.update(1)
        self.unpublished_topics.discard(mid)
        if not self.unpublished_topics:
            if self.verbose:
                print("topics published")
            if self.pbar:
                self.pbar.close()
            self.client.stop()
            sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT retained message deleter", add_help=False)
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose output")
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

    tool = DeleteRetainedTool(
        "mqtt-delete-retained",
        args.broker_url,
        args.topic,
        verbose=args.verbose,
    )

    tool.run()
