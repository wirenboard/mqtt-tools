#!/usr/bin/env python
import argparse
import mosquitto

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 1883


class System(object):
    def __init__(self, name, controls):
        self.name = name
        self.controls = {}
        for order, control in enumerate(controls, 1):
            control.bind(self, order)
            self.controls[control.name] = control

    def topic(self, *tail):
        return "/".join(("/devices", self.name) + tail)

    def publish(self, client):
        client.publish(self.topic("meta/name"), self.name, 2, True)
        # publish metadata first, then values
        for control in self.controls.values():
            control.publish(client)
        for control in self.controls.values():
            control.publish_value()

    def subscribe(self, client):
        for control in self.controls.values():
            control.subscribe(client)

    def post_value(self, target, payload):
        target_control = self.controls[target]
        if target_control.value_str() != payload:
            target_control.post_value(payload)

    def on_message(self, topic, payload):
        for client in self.controls.values():
            client.on_message(topic, payload)


class Control(object):
    type = None

    def __init__(self, name):
        assert isinstance(name, str)
        self.name = name

    def bind(self, system, order):
        self.system = system
        self.order = order

    def topic(self, *tail):
        return self.system.topic("controls", self.name, *tail)

    def publish(self, client):
        assert self.type is not None, "control without a type"
        self.client = client
        self.client.publish(self.topic("meta/type"), self.type, 2, True)
        self.client.publish(self.topic("meta/order"), str(self.order), 2, True)

    def publish_value(self):
        value_str = self.value_str()
        print "publish: %r = %r" % (self.name, value_str)
        if value_str is not None:
            self.client.publish(self.topic(), value_str, 0, True)

    def post_value(self, payload):
        print "%r <-- %r" % (self.name, payload)
        self.update(payload)
        self.publish_value()

    def value_str(self):
        return None

    def subscribe(self, client):
        self.client = client

    def on_message(self, topic, payload):
        pass

    def update(self, payload):
        raise NotImplementedError


class WritableControl(Control):
    def __init__(self, name, target=None, **kwargs):
        super(WritableControl, self).__init__(name, **kwargs)
        print "WritableControl %r: kwargs: %r target: %r" % \
            (self.name, kwargs, target)
        self.target = target

    def subscribe(self, client):
        super(WritableControl, self).subscribe(client)
        client.subscribe(self.topic("on"))

    def on_message(self, topic, payload):
        if topic == self.topic("on"):
            self.post_value(payload)

    def post_value(self, payload):
        super(WritableControl, self).post_value(payload)
        if self.target is not None:
            self.system.post_value(self.target, self.value_str())


class ReadOnlyControl(Control):
    def publish(self, client):
        super(ReadOnlyControl, self).publish(client)
        self.client.publish(self.topic("meta/readonly"), "1", 2, True)


class SwitchControl(WritableControl):
    type = "switch"

    def __init__(self, name, is_on=False, **kwargs):
        super(SwitchControl, self).__init__(name, **kwargs)
        self.is_on = bool(is_on)

    def value_str(self):
        return "1" if self.is_on else "0"

    def update(self, payload):
        self.is_on = (payload == "1")


class NumericControl(Control):
    def __init__(self, name, value=0, **kwargs):
        super(NumericControl, self).__init__(name, **kwargs)
        self.value = value

    def value_str(self):
        return str(self.value) if self.value is not None else 0

    def update(self, payload):
        self.value = float(payload)


class RangeControl(NumericControl, WritableControl):
    type = "range"

    def __init__(self, name, max, value=0, **kwargs):
        super(RangeControl, self).__init__(name, value=value, **kwargs)
        self.max = max

    def publish(self, client):
        super(RangeControl, self).publish(client)
        self.client.publish(self.topic("meta/max"), str(self.max), 2, True)


class TemperatureControl(ReadOnlyControl, NumericControl):
    type = "temperature"


systems = [
    System("Relays", [
        SwitchControl("Relay 1"),
        SwitchControl("Relay 2")
    ]),
    System("Temperature", [
        TemperatureControl("Temp 1"),
        RangeControl("Set Temp 1", max=100, target="Temp 1")
    ])
]


def on_connect(client, userdata, rc):
    if rc != 0:
        return
    for s in systems:
        s.publish(client)
        s.subscribe(client)


def on_message(client, userdata, msg):
    print "message received: %r %r" % (msg.topic, msg.payload)
    for s in systems:
        s.on_message(msg.topic, msg.payload)


def main():
    parser = argparse.ArgumentParser(description="homA device simulator", add_help=False)
    parser.add_argument("-h", "--host", dest="host", type=str,
                        help="MQTT host", default="localhost")
    parser.add_argument("-p", "--port", dest="port", type=int,
                        help="MQTT port", default="1883")
    args = parser.parse_args()

    client = mosquitto.Mosquitto("simulate")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(args.host, args.port)

    while 1:
        rc = client.loop()
        if rc != 0:
            break


if __name__ == "__main__":
    main()
