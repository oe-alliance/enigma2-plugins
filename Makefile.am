ACLOCAL_AMFLAGS = -I m4

SUBDIRS = \
	aihdcontroler \
	antiscrollbar \
	audiosync \
	automaticcleanup \
	automaticvolumeadjustment \
	autoresolution \
	autotimer \
	babelzapper \
	bonjour \
	cdinfo \
	dreamirc \
	dreammediathek \
	dvdbackup \
	easyinfo \
	easymedia \
	eibox \
	emailclient \
	epgrefresh \
	epgsearch \
	filebrowser \
	fritzcall \
	ftpbrowser \
	googlemaps \
	growlee \
	httpproxy \
	imdb \
	kiddytimer \
	lastfm \
	mediadownloader \
	menusort \
	merlinepg \
	merlinmusicplayer \
	meteoitalia \
	mosaic \
	moviecut \
	movieretitle \
	moviesearch \
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
	shoutcast \
	showclock \
	simplerss \
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

if DREAMBOX
SUBDIRS +=  fancontrol2 letterbox logomanager movielistpreview
endif

if VUUNO
SUBDIRS +=  fancontrol2
endif
if VUULTIMO
SUBDIRS +=  fancontrol2
endif

metadir = $(datadir)/meta
meta_DATA = index-enigma2-plugins.xml
CLEANFILES = index-enigma2-plugins.xml

index-enigma2-plugins.xml: $(top_srcdir)/genmetaindex.py $(top_srcdir)/*/meta/plugin_*.xml
	$(AM_V_GEN)$(PYTHON) $^ > $@
