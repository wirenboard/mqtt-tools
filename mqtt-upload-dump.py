#!/usr/bin/python
import argparse

try:
    import mosquitto
except ImportError:
    import paho.mqtt.client as mosquitto


import sys
import progressbar


last_mid = None
pb = None
pb_widgets=[progressbar.Percentage(), progressbar.Bar(left="[", right="]")]


def on_mqtt_publish(arg0, arg1, arg2=None):
    # global last_mid
    mid = arg1 or arg2
    # update progressbar
    if pb:
        pb.update(mid)
    # print mid, last_mid
    if last_mid and (last_mid == mid):
        client.disconnect()
        pb.finish()
        sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='publish mqtt messages to broker', add_help=False)

    parser.add_argument('-h', '--host', dest='host', type=str,
                        help='MQTT host', default='localhost')

    parser.add_argument('-p', '--port', dest='port', type=int,
                        help='MQTT port', default='1883')

    parser.add_argument('-u', '--username', dest='username', type=str,
                        help='MQTT username', default='')

    parser.add_argument('-P', '--password', dest='password', type=str,
                        help='MQTT password', default='')

    parser.add_argument('-v', '--verbose', dest='verbose', action="store_true",
                        help="Verbose output")

    parser.add_argument('filename', type=str,
                        help='File containing MQTT dump.  Topic and message are separated by tab')

    args = parser.parse_args()

    client = mosquitto.Mosquitto()
    if args.username:
        client.username_pw_set(args.username, args.password)

    client.connect(args.host, args.port)
    client.on_publish = on_mqtt_publish

    mid = None
    topic = None
    full_msg = None
    for line in open(args.filename):
        line = line.decode('utf8')[:-1]

        next_line = False
        if len(line) > 0 and line[-1] == "\\":
            next_line = True
            line = line[:-1]

        if topic is None:
            chunks = line.split('\t', 1)
            if len(chunks) < 2:
                continue

            topic, msg = line.split('\t', 1)
            topic = bytearray(topic, "utf8")

            if next_line:
                msg = msg + '\n'
            msg = bytearray(msg, "utf8")
            full_msg = msg
        else:
            if next_line:
                line = line + '\n'
            full_msg += bytearray(line, "utf8")

        # check if line end contains backslash
        if next_line:
            continue

        status, mid = client.publish(topic, full_msg, retain=True, qos=2)

        if args.verbose:
            print(topic)

        topic = None
        full_msg = None

    last_mid = mid

    if args.verbose:
        print("last: %d" % last_mid)

    pb = progressbar.ProgressBar(widgets=pb_widgets,
                                 maxval=last_mid).start()

    while 1:
        rc = client.loop()
        if rc != 0:
            break
