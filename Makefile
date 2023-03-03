.PHONY: all clean

PREFIX = /usr

all:
clean:

install: all
	install -Dm0755 mqtt-upload-dump.py $(DESTDIR)$(PREFIX)/bin/mqtt-upload-dump
	install -Dm0755 mqtt-get-dump.py $(DESTDIR)$(PREFIX)/bin/mqtt-get-dump
	install -Dm0755 mqtt-delete-retained.py $(DESTDIR)$(PREFIX)/bin/mqtt-delete-retained
