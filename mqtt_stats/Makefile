TARGET=mqtt_stats

OBJS=main.o

#DEB_TARGET_ARCH ?= armel

ifeq ($(DEB_TARGET_ARCH), armel)
CROSS_COMPILE = arm-linux-gnueabi-
endif
ifeq ($(DEB_TARGET_ARCH), armhf)
CROSS_COMPILE = arm-linux-gnueabihf-
endif

CC=$(CROSS_COMPILE)gcc

LDFLAGS=-lmosquitto -g
CFLAGS=-std=c99 -g -Wall -Werror

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) -c -o $@ $^ $(CFLAGS)

clean:
	rm -rf $(TARGET) $(OBJS)

.PHONY: clean
