OBJS := bitratecalc.cpp

-include $(OBJS:.cpp=.d)

bitratecalc.so:
	$(CXX) $(CPPFLAGS) -MD $(CXXFLAGS) $(ENIGMA2_CFLAGS) $(SIGC_CFLAGS) \
	$(PYTHON_CPPFLAGS) $(DEFS) -I. -Wall -W $(OBJS) -shared -fPIC  -lcrypto \
	-Wl,-soname,bitratecalc.so -o bitratecalc.so $(LDFLAGS)

all: bitratecalc.so

CLEANFILES = bitratecalc.so bitratecalc.d

