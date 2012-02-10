ACLOCAL_AMFLAGS = -I m4

SUBDIRS = \
	3dsettings \
	aihdcontroler \
	antiscrollbar \
	audiosync \
	automaticcleanup \
	automatictimerlistcleanup \
	automaticvolumeadjustment \
	autoresolution \
	autotimer \
	babelzapper \
	bitrateviewer \
	bonjour \
	cdinfo \
	curlytx \
	dreamirc \
	dreammediathek \
	dvdbackup \
	dyndns \
	easyinfo \
	easymedia \
	ecasa \
	eibox \
	elektro \
	emailclient \
	emission \
	epgrefresh \
	epgsearch \
	eurotictv \
	fancontrol2 \
	filebrowser \
	fritzcall \
	fstabeditor \
	ftpbrowser \
	genuinedreambox \
	googlemaps \
	growlee \
	httpproxy \
	imdb \
	infobartunerstate \
	kiddytimer \
	lastfm \
	letterbox \
	logomanager \
	mediadownloader \
	menusort \
	merlinepg \
	merlinepgcenter \
	merlinmusicplayer \
	meteoitalia \
	mosaic \
	moviecut \
	movielistpreview \
	movieretitle \
	moviesearch \
	movieselectionquickbutton \
	movietagger \
	movieepg \
	mphelp \
	multirc \
	mytube \
	namezap \
	ncidclient \
	netcaster \
	networkbrowser \
	ofdb \
	orfat \
	orfteletext \
	partnerbox \
	passwordchanger \
	permanentclock \
	permanenttimeshift \
	pipservicerelation \
	pipzap \
	pluginhider \
	pluginsort \
	podcast \
	porncenter \
	quickbutton \
	reconstructapsc \
	remotetimer \
	rsdownloader \
	seekbar \
	serienfilm \
	setpasswd \
	showclock \
	simplerss \
	startupservice \
	startuptostandby \
	subsdownloader2 \
	svdrp \
	tageditor \
	trafficinfo \
	tvcharts \
	unwetterinfo \
	valixdcontrol \
	virtualzap \
	vlcplayer \
	vps \
	weatherplugin \
	webcamviewer \
	webbouqueteditor \
	webinterface \
	werbezapper \
	youtubeplayer \
	yttrailer \
	zaphistorybrowser \
	zapstatistic \
	zdfmediathek

metadir = $(datadir)/meta
meta_DATA = index-enigma2-plugins.xml
CLEANFILES = index-enigma2-plugins.xml

index-enigma2-plugins.xml: $(top_srcdir)/genmetaindex.py $(top_srcdir)/*/meta/plugin_*.xml
	$(AM_V_GEN)$(PYTHON) $^ > $@
