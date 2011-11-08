include $(top_srcdir)/Rules-cpp.mak

plugindir = $(libdir)/enigma2/python/Plugins/Extensions/MerlinMusicPlayer

plugin_LTLIBRARIES = merlinmp3player.la

merlinmp3player_la_SOURCES = \
	merlinmp3player.cpp \
	merlinmp3player.h

merlinmp3player_la_LDFLAGS = \
	-avoid-version -module

merlinmp3player_la_LIBADD = \
	@GSTREAMER_LIBS@
