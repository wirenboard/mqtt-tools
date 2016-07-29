#!/usr/bin/env python

import argparse
import mosquitto
import sys
import signal

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1883

DELAY = 0.05

NUM_CONTROLS = 3
DEV_NAME = "flood"

running = True
to_clean_up = 0
to_clean_up_mids = []


def on_connect(client, userdata, rc):
    if rc != 0:
        return

    client.publish("/devices/%s/meta/name" % DEV_NAME, DEV_NAME, retain=True, qos=2)
    for i in range(1, NUM_CONTROLS + 1):
        client.publish("/devices/%s/controls/ctl%d/meta/type" % (DEV_NAME, i), "text", retain=True, qos=2)


def on_publish_cleanup(client, userdata, mid):
    global to_clean_up, running
    if mid in to_clean_up_mids:
        to_clean_up -= 1
    if to_clean_up == 0:
        running = False


def main():
    parser = argparse.ArgumentParser(description="homA device simulator", add_help=False)
    parser.add_argument("-h", "--host", dest="host", type=str,
                        help="MQTT host", default="localhost")
    parser.add_argument("-p", "--port", dest="port", type=int,
                        help="MQTT port", default="1883")
    parser.add_argument("-f", "--fq", help="Flood frequency @ each channel, Hz", type=float, default=20)
    parser.add_argument("-n", "--ncontrols", help="Number of controls", type=int, default=3)
    parser.add_argument("--devname", help="MQTT device name", type=str, default="flood")

    args = parser.parse_args()

    NUM_CONTROLS = args.ncontrols
    DEV_NAME = args.devname

    client = mosquitto.Mosquitto("simulate")
    client.on_connect = on_connect
    # client.on_message = on_message
    client.connect(args.host, args.port)

    if abs(args.fq) < 0.00001:
        args.fq = 0.00001
        print >>sys.stderr, "Warning: limit frequency to 0.00001 (~10s delay)"

    DELAY = 1 / args.fq
    v = 1

    # add signal handler to exit gracefully
    global running

    def sighndlr(signum, frame):
        global running
        running = False

    signal.signal(signal.SIGINT, sighndlr)
    signal.signal(signal.SIGTERM, sighndlr)

    while running:
        try:
            rc = client.loop(DELAY)
        except:
            running = False

        if rc != 0:
            break
        for i in range(1, NUM_CONTROLS + 1):
            client.publish("/devices/%s/controls/ctl%d" % (DEV_NAME, i), str(v))
            v += 1

    # clean up all this flood
    print >>sys.stderr, "Cleaning up..."

    global to_clean_up

    to_clean_up = 2 * NUM_CONTROLS + 1
    client.on_publish = on_publish_cleanup

    running = True

    (_, mid) = client.publish("/devices/%s/meta/name" % DEV_NAME, "", retain=True, qos=2)
    to_clean_up_mids.append(mid)
    for i in range(1, NUM_CONTROLS + 1):
        (_, mid) = client.publish("/devices/%s/controls/ctl%d/meta/type" % (DEV_NAME, i), "", retain=True, qos=2)
        to_clean_up_mids.append(mid)

        (_, mid) = client.publish("/devices/%s/controls/ctl%d" % (DEV_NAME, i), "", retain=True, qos=2)
        to_clean_up_mids.append(mid)

    while running:
        rc = client.loop()
        if rc != 0:
            break

    client.disconnect()

if __name__ == "__main__":
    main()
