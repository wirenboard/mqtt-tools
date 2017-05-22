.PHONY: all clean

all:
clean :

install: all
	install -m 0755 mqtt-upload-dump.py  $(DESTDIR)/usr/bin/mqtt-upload-dump
	install -m 0755 mqtt-get-dump.py  $(DESTDIR)/usr/bin/mqtt-get-dump
	install -m 0755 mqtt-delete-retained.py  $(DESTDIR)/usr/bin/mqtt-delete-retained




