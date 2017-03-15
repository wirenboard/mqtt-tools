/* mqtt_stats - lightweight MQTT broker activity registrator
 * 
 * See README.md for futher information
 *
 * Author: Nikita webconn Maslov
 * Copyright 2017 Contactless Devices LLC
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include <signal.h>
#include <sys/time.h>
#include <errno.h>
#include <string.h>

#include <mosquitto.h>

#define CLIENT_ID       "mqtt_stats"
#define DEFAULT_BROKER  "localhost"
#define DEFAULT_TOPIC   "/#"
#define DEFAULT_PORT    1883
#define KEEPALIVE       60
#define PERIOD          3

void print_help(const char *name)
{
    fprintf(stderr, "Usage: %s [-H hostname] [-p port] [-t topic] [-h]\n", name);
}

/* Active flag */
sig_atomic_t active = 1;

/* SIGINT/SIGTERM handler */
void on_signal(int sig)
{
    active = 0;
}

/* Number of messages registered */
long num_messages = 0;

/* Number of messages per period of time */
long num_messages_rate = 0;

/* Maximum message rate */
float max_rate = 0.0;

/* Start time */
struct timeval start_time = { 0 };

/* Period start time */
struct timeval period_start_time = { 0 };
    
/* Default topic */
char *topic = DEFAULT_TOPIC;

/* Mosquitto message callback */
void on_message(struct mosquitto *mosq, void *userdata, const struct mosquitto_message *msg)
{
    if (!msg->retain) {
        /* increase number of messages received */
        num_messages++;
        num_messages_rate++;
    }
}

/* Mosquitto connect callback */
void on_connect(struct mosquitto *mosq, void *userdata, int rc)
{
    printf("Connected to MQTT\n");
}

/* Mosquitto log callback */
void log_callback(struct mosquitto *mosq, void *userdata, int level, const char *str)
{
    fprintf(stderr, " [mqtt] %s\n", str);
}

int main(int argc, char *argv[])
{
    /* arguments:
     * -h: show help
     * -H: broker hostname (default: 'localhost')
     * -p: broker port (default: 1883)
     * -v: verbose
     */
    char *broker_host = DEFAULT_BROKER;
    int port = DEFAULT_PORT;
    int opt;
    int verbose = 0;

    while ((opt = getopt(argc, argv, "hvH:p:t:")) != -1) {
        switch (opt) {
        case 'H':
            /* broker_host = (char *) malloc(strlen(optarg) + 1); */
            /* strncpy(broker_host, optarg, strlen(optarg)); */
            broker_host = optarg;
            break;
        case 'p':
            port = atoi(optarg);
            break;
        case 't':
            topic = optarg;
            break;
        case 'v':
            verbose = 1;
            break;
        case 'h':
        default:
            print_help(argv[0]);
            return 1;
        }
    }

    /* register signal handler */
    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);


    /* init mosquitto */
    mosquitto_lib_init();

    struct mosquitto *mqtt = mosquitto_new(CLIENT_ID, 1, NULL);

    if (!mqtt) {
        fprintf(stderr, "Error init mqtt\n");
        return -1;
    }

    mosquitto_message_callback_set(mqtt, on_message);
    mosquitto_connect_callback_set(mqtt, on_connect);

    if (verbose == 1) {
        mosquitto_log_callback_set(mqtt, log_callback);
    }

    if (mosquitto_connect(mqtt, broker_host, port, KEEPALIVE)) {
        fprintf(stderr, "Unable to connect\n");
        return -1;
    }

    mosquitto_subscribe(mqtt, NULL, topic, 0);
    
    /* init timers */
    gettimeofday(&start_time, NULL);
    gettimeofday(&period_start_time, NULL);
    
    fprintf(stderr, "mqtt_stats from host %s, port %d, topic %s\n", broker_host, port, topic);
    fprintf(stderr, "Type Ctrl-C to see stats.\n\n");

    /* start loop till we are active (no Ctrl-C received) */
    while (active) {
        mosquitto_loop(mqtt, PERIOD, 1);

        /* try to measure rate */
        struct timeval t;
        gettimeofday(&t, NULL);

        int interval = t.tv_sec - period_start_time.tv_sec;

        if (interval >= PERIOD) {
            /* calculate rate */
            float rate = (float) num_messages_rate / interval;

            if (rate > max_rate) {
                max_rate = rate;
            }

            /* clear counters */
            num_messages_rate = 0;
            period_start_time = t;
        }
    }

    /* print stats */
    struct timeval t;
    gettimeofday(&t, NULL);

    int full_interval = t.tv_sec - start_time.tv_sec;
    float avg_rate = (float) num_messages / full_interval;

    fprintf(stderr, "MQTT stats:\n\tTotal number of messages: %ld\n\tAverage rate: %f msg/s\n\tMax rate: %f msg/s\n\n", 
            num_messages, avg_rate, max_rate);

    mosquitto_destroy(mqtt);
    mosquitto_lib_cleanup();

    return 0;
}
