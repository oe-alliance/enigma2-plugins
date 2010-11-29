AM_CXXFLAGS = @LIBCRYPTO_CFLAGS@

plugindir = $(libdir)/enigma2/python/Plugins/Extensions/BitrateViewer

plugin_LTLIBRARIES = bitratecalc.la

bitratecalc_la_SOURCES = \
	bitratecalc.cpp \
	bitratecalc.h

bitratecalc_la_LDFLAGS = \
	-avoid-version -module

bitratecalc_la_LIBADD = \
	@LIBCRYPTO_LIBS@
