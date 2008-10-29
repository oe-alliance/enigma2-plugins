OBJS := servicets.cpp

-include $(OBJS:.cpp=.d)

servicets.so:
	$(CXX) $(CPPFLAGS) -MD $(CXXFLAGS) $(ENIGMA2_CFLAGS) $(SIGC_CFLAGS) \
	$(PYTHON_CPPFLAGS) $(DEFS) -I. -Wall -W $(OBJS) -shared -fPIC \
	-Wl,-soname,servicets.so -o servicets.so $(LDFLAGS)

all: servicets.so

CLEANFILES = servicets.so servicets.d
