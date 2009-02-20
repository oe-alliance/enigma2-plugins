CFLAGS_append = " -DDEBUG"
CXXFLAGS_append = " -DDEBUG"

netscan.so: src
	$(CC) -Wall -W -shared -O2 -fPIC -o netscan.so -lc main.o list.o range.o statusq.o nbtscan.o smbinfo.o showmount.o
	$(STRIP) netscan.so
	
src: list.c range.c statusq.c nbtscan.c main.c smbinfo.c
	$(CC) -DDEBUG -O2 -fPIC -c list.c
	$(CC) -DDEBUG -O2 -fPIC -c range.c
	$(CC) -DDEBUG -O2 -fPIC -c statusq.c
	$(CC) -DDEBUG -O2 -fPIC -c nbtscan.c
	$(CC) -DDEBUG -O2 -fPIC -c smbinfo.c
	$(CC) -DDEBUG -O2 -fPIC -c showmount.c
	$(CC) -DDEBUG -O2 -fPIC -c $(PYTHON_CPPFLAGS) -c main.c

all: netscan.so

CLEANFILES = netscan.so

install: all
	$(INSTALL) netscan.so $(DESTDIR)/usr/lib/enigma2/python/Plugins/SystemPlugins/NetworkBrowser

