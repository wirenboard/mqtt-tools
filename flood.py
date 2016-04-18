#!/usr/bin/env python
import time
import argparse
import mosquitto

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1883

DELAY = 0.05

NUM_CONTROLS = 3
DEV_CONTROLS = [
    ("/devices/flood/meta/name", "Flood"),
    ("/devices/flood/controls/ctl1/meta/type", "text"),
    ("/devices/flood/controls/ctl1", "0"),
    ("/devices/flood/controls/ctl2/meta/type", "text"),
    ("/devices/flood/controls/ctl2", "0"),
    ("/devices/flood/controls/ctl3/meta/type", "text"),
    ("/devices/flood/controls/ctl3", "0"),
]


def on_connect(client, userdata, rc):
    if rc != 0:
        return
    for topic, value in DEV_CONTROLS:
        client.publish(topic, value, 2, True)


def main():
    parser = argparse.ArgumentParser(description="homA device simulator", add_help=False)
    parser.add_argument("-h", "--host", dest="host", type=str,
                        help="MQTT host", default="localhost")
    parser.add_argument("-p", "--port", dest="port", type=int,
                        help="MQTT port", default="1883")
    args = parser.parse_args()

    client = mosquitto.Mosquitto("simulate")
    client.on_connect = on_connect
    # client.on_message = on_message
    client.connect(args.host, args.port)

    v = 1

    while True:
        rc = client.loop(DELAY)
        if rc != 0:
            break
        for i in range(1, NUM_CONTROLS + 1):
            client.publish("/devices/flood/controls/ctl%d" % i, v)
            v += 1

if __name__ == "__main__":
    main()
