#!/usr/bin/env python3
import argparse
import sys

import tqdm
from wb_common.mqtt_client import DEFAULT_BROKER_URL, MQTTClient


class UploadDumpTool:
    def __init__(self, client_id, broker_url, filename, verbose=False):
        self.client = MQTTClient(client_id, broker_url, False)

        self.filename = filename
        self.verbose = verbose

        self.pbar = None
        self.last_mid = None

    @staticmethod
    def parse_dump(filename):
        topic = None
        full_msg = None
        with open(filename, encoding="utf-8") as f:
            for line in f:
                line = line[:-1]

                next_line = False
                if len(line) > 0 and line[-1] == "\\":
                    next_line = True
                    line = line[:-1]

                if topic is None:
                    chunks = line.split("\t", 1)
                    if len(chunks) < 2:
                        continue

                    topic, msg = line.split("\t", 1)

                    if next_line:
                        msg = msg + "\n"
                    full_msg = msg
                else:
                    if next_line:
                        line = line + "\n"
                    full_msg += line

                # check if line end contains backslash
                if next_line:
                    continue

                yield (topic, full_msg)

                topic = None
                full_msg = None

    def run(self):
        self.client.start()
        self.client.on_publish = self.on_mqtt_publish

        mid = None

        for topic, full_msg in self.parse_dump(self.filename):
            _, mid = self.client.publish(topic, full_msg, retain=True, qos=2)
            if self.verbose:
                print(topic)

        self.last_mid = mid

        if args.verbose:
            print("last: %d" % self.last_mid)

        self.pbar = tqdm.tqdm(total=self.last_mid)

        while 1:
            ret = self.client.loop()
            if ret != 0:
                break

    def on_mqtt_publish(self, _, arg1, arg2=None):
        # global last_mid
        mid = arg1 or arg2
        # update progressbar
        if self.pbar:
            self.pbar.update(1)
        # print mid, last_mid
        if self.last_mid and (self.last_mid == mid):
            self.client.stop()
            self.pbar.close()
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="publish mqtt messages to broker", add_help=False)
    parser.add_argument(
        "-b",
        "--broker",
        dest="broker_url",
        type=str,
        help="MQTT broker url",
        default=DEFAULT_BROKER_URL,
    )
    parser.add_argument("-h", "--host", dest="host", type=str, help="MQTT host (deprecated)", default="localhost")
    parser.add_argument("-p", "--port", dest="port", type=int, help="MQTT port (deprecated)", default="1883")
    parser.add_argument("-u", "--username", dest="username", type=str, help="MQTT username (deprecated)", default="")
    parser.add_argument("-P", "--password", dest="password", type=str, help="MQTT password (deprecated)", default="")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "filename", type=str, help="File containing MQTT dump.  Topic and message are separated by tab"
    )

    args = parser.parse_args()

    # For backward compatibility
    if args.host != "localhost" or args.port != 1883 or args.username or args.password:
        if args.username:
            if args.password:
                userinfo = "%s:%s@" % (args.username, args.password)
            else:
                userinfo = "%s@" % args.username
        args.broker_url = "tcp://%s%s:%s" % (userinfo, args.host, args.port)

    tool = UploadDumpTool(
        "mqtt-upload-dump",
        args.broker_url,
        args.filename,
        verbose=args.verbose,
    )
    tool.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
