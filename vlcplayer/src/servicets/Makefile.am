servicets.so: servicets.cpp servicets.h
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(ENIGMA2_CFLAGS) $(SIGC_CFLAGS) \
	$(PYTHON_CPPFLAGS) $(DEFS) -I. -Wall -W servicets.cpp -shared -fPIC \
	-Wl,-soname,servicets.so -o servicets.so $(LDFLAGS)

all: servicets.so

CLEANFILES = servicets.so
