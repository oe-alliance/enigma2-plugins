include $(top_srcdir)/Rules-cpp.mak

plugindir = $(libdir)/enigma2/python/Plugins/Extensions/BitrateViewer

plugin_LTLIBRARIES = bitratecalc.la

bitratecalc_la_SOURCES = \
	bitratecalc.cpp \
	bitratecalc.h

bitratecalc_la_LDFLAGS = \
	$(PLUGIN_LIBTOOL_FLAGS)

bitratecalc_la_LIBADD = \
	@LIBCRYPTO_LIBS@
