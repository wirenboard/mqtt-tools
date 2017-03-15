mqtt\_stats
==========

Collects some useful stats about MQTT topic:

* Number of messages published;
* Average message rate;
* Peak message rate (approx.).

Usage
-----

```
./mqtt_stats [-H host] [-p port] [-t topic]
```

To print stats, use SIGINT (Ctrl-C) or SIGUSR1 (this will not halt the application, just print stats message).
