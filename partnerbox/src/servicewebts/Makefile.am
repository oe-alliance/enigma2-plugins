OBJS := servicewebts.cpp

-include $(OBJS:.cpp=.d)

servicewebts.so:
	$(CXX) $(CPPFLAGS) -MD $(CXXFLAGS) $(ENIGMA2_CFLAGS) $(SIGC_CFLAGS) \
	$(PYTHON_CPPFLAGS) $(DEFS) -I. -Wall -W $(OBJS) -shared -fPIC \
	-Wl,-soname,servicewebts.so -o servicewebts.so $(LDFLAGS)

all: servicewebts.so

CLEANFILES = servicewebts.so servicewebts.d
