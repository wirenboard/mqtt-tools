#!/usr/bin/env python3
# pylint: disable=invalid-name
# pylint: disable=duplicate-code
import argparse
import logging
import sys

from wb_common.mqtt_client import DEFAULT_BROKER_URL, MQTTClient

logger = logging.getLogger(__name__)


class GetDumpTool:
    def __init__(self, client_id, broker_url, topic):
        self.client = MQTTClient(client_id, broker_url, False)

        self.topic = topic
        self.ret_topic = f"/tmp/{self.client._client_id.decode()}/retain_hack"

    def run(self):
        self.client.start()
        self.client.on_message = self.on_mqtt_message

        self.client.subscribe(self.topic)

        # hack to get retained settings first:
        self.client.subscribe(self.ret_topic)
        self.client.publish(self.ret_topic, "1", qos=2)

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


def main():
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
        "-h", "--host", dest="host", type=str, help="MQTT host (deprecated)", default="localhost"
    )
    parser.add_argument("-p", "--port", dest="port", type=int, help="MQTT port (deprecated)", default="1883")
    parser.add_argument(
        "-u", "--username", dest="username", type=str, help="MQTT username (deprecated)", default=""
    )
    parser.add_argument(
        "-P", "--password", dest="password", type=str, help="MQTT password (deprecated)", default=""
    )
    parser.add_argument(
        "topic",
        type=str,
        help='Topic mask to unpublish retained messages from. For example: "/devices/my-device/#"',
    )

    args = parser.parse_args()

    # For backward compatibility
    if args.host != "localhost" or args.port != 1883 or args.username or args.password:
        userinfo = ""
        if args.username:
            if args.password:
                userinfo = f"{args.username}:{args.password}@"
            else:
                userinfo = f"{args.username}@"
        args.broker_url = f"tcp://{userinfo}{args.host}:{args.port}"

    tool = GetDumpTool(
        "mqtt-get-dump",
        args.broker_url,
        args.topic,
    )
    try:
        tool.run()
    except (ConnectionError, ConnectionRefusedError):
        logger.error("Cannot connect to broker %s", args.broker_url)
        sys.exit(1)
    except ValueError as err:
        logger.error(err)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
