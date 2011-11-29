include $(top_srcdir)/Rules-cpp.mak

plugindir = $(libdir)/enigma2/python/Plugins/Extensions/PermanentTimeshift

plugin_LTLIBRARIES = eitsave.la

eitsave_la_SOURCES = \
	eitsave.cpp 

eitsave_la_LDFLAGS = \
	-avoid-version -module

install-data-hook:
	rm $(DESTDIR)$(libdir)/enigma2/python/Plugins/Extensions/PermanentTimeshift/eitsave.*a
