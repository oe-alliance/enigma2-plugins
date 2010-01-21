AUTOMAKE_OPTIONS = gnu
SUBDIRS = \
	ac3lipsync \
	antiscrollbar \
	ardmediathek \
	autoresolution \
	autotimer \
	cdinfo \
	dreamirc \
	elektro \
	emailclient \
	epgrefresh \
	epgsearch \
	filebrowser \
	fritzcall \
	ftpbrowser \
	genuinedreambox \
	googlemaps \
	growlee \
	httpproxy \
	imdb \
	kiddytimer \
	lastfm \
	logomanager \
	mediadownloader \
	meteoitalia \
	mosaic \
	moviecut \
	movielistpreview \
	movieretitle \
	movieselectionquickbutton \
	movietagger \
	multirc \
	mytube \
	netcaster \
	networkbrowser \
	ofdb \
	orfat \
	partnerbox \
	passwordchanger \
	permanentclock \
	podcast \
	porncenter \
	quickbutton \
	reconstructapsc \
	remotetimer \
	rsdownloader \
	simplerss \
	setpasswd \
	shoutcast \
	startupservice \
	startuptostandby \
	tageditor \
	trafficinfo \
	unwetterzentrale \
	vlcplayer \
	weatherplugin \
	webcamviewer \
	webinterface \
	werbezapper \
	youtubeplayer \
	zaphistorybrowser


LANGS := $(shell cat $(srcdir)/LINGUAS)

install-exec-hook:
	for lang in $(LANGS); do \
		$(PYTHON) $(srcdir)/genmetaindex.py $$lang $(DESTDIR)$(datadir)/meta/plugin_*.xml > $(DESTDIR)$(datadir)/meta/index-enigma2-plugins_$$lang.xml; \
	done

uninstall-hook:
	$(RM) $(DESTDIR)$(datadir)/meta/index-enigma2-plugins_*.xml
