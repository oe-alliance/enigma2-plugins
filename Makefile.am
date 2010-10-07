AUTOMAKE_OPTIONS = gnu
SUBDIRS = \
	ac3lipsync \
	aihdcontrol \
	antiscrollbar \
	automatictimerlistcleanup \
	automaticvolumeadjustment \
	autoresolution \
	autotimer \
	babelzapper \
	bonjour \
	cdinfo \
	dreamirc \
	dvdbackup \
	dyndns \
	eibox \
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
	merlinepg \
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


install-exec-hook:
	$(PYTHON) $(srcdir)/genmetaindex.py $(DESTDIR)$(datadir)/meta/plugin_*.xml > $(DESTDIR)$(datadir)/meta/index-enigma2-plugins.xml

uninstall-hook:
	$(RM) $(DESTDIR)$(datadir)/meta/index-enigma2-plugins.xml

