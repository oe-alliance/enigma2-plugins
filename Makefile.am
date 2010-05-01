AUTOMAKE_OPTIONS = gnu
SUBDIRS = \
	ac3lipsync \
	aihdcontrol \
	antiscrollbar \
	automatictimerlistcleanup \
	autoresolution \
	autotimer \
	cdinfo \
	dreamirc \
	dvdbackup \
	dyndns \
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
	letterbox \
	logomanager \
	mediadownloader \
	merlinmusicplayer \
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
	seekbar \
	setpasswd \
	shoutcast \
	simplerss \
	startupservice \
	startuptostandby \
	tageditor \
	trafficinfo \
	unwetterzentrale \
	virtualzap \
	vlcplayer \
	vxdcontrol \
	weatherplugin \
	webcamviewer \
	webinterface \
	werbezapper \
	youtubeplayer \
	zaphistorybrowser \
	zapstatistic \
	zdfmediathek


LANGS := $(shell cat $(srcdir)/LINGUAS)

install-exec-hook:
	for lang in $(LANGS); do \
		$(PYTHON) $(srcdir)/genmetaindex.py $$lang $(DESTDIR)$(datadir)/meta/plugin_*.xml > $(DESTDIR)$(datadir)/meta/index-enigma2-plugins_$$lang.xml; \
	done

uninstall-hook:
	$(RM) $(DESTDIR)$(datadir)/meta/index-enigma2-plugins_*.xml
