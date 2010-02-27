OBJS = merlinmp3player.cpp

-include $(OBJS:.cpp=.d)

merlinmp3player.so: merlinmp3player.h


	$(CXX) $(CPPFLAGS) -MD $(CXXFLAGS) $(ENIGMA2_CFLAGS) $(SIGC_CFLAGS) $(GSTREAMER_CFLAGS) $(GSTREAMERPBUTILS_CFLAGS) $(GSTREAMER_LDFLAGS) $(GSTREAMERPBUTILS_LDFLAGS) \
	$(PYTHON_CPPFLAGS) $(DEFS) -I$(top_srcdir)/include -Wall -lgstbase-0.10 -W $(OBJS) -shared -fPIC -Wl,-soname,merlinmp3player.so -o merlinmp3player.so \
	$(LDFLAGS)

all: merlinmp3player.so

CLEANFILES = merlinmp3player.so merlinmp3player.d

