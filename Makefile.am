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
	ecasa \
	eibox \
	emailclient \
	epgrefresh \
	epgsearch \
	filebrowser \
	fritzcall \
	fstabeditor \
	ftpbrowser \
	googlemaps \
	growlee \
	httpproxy \
	imdb \
	kiddytimer \
	lastfm \
	mediadownloader \
	merlinepg \
	merlinmusicplayer \
	meteoitalia \
	mosaic \
	moviecut \
	movieretitle \
	moviesearch \
	movietagger \
	mphelp \
	multirc \
	ncidclient \
	netcaster \
	networkbrowser \
	ofdb \
	orfat \
	orfteletext \
	partnerbox \
	passwordchanger \
	permanentclock \
	podcast \
	porncenter \
	quickbutton \
	reconstructapsc \
	remotetimer \
	rsdownloader \
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
	werbezapper \
	youtubeplayer \
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

if TPM
SUBDIRS += \
	mytube \
	yttrailer \
	webinterface
endif

metadir = $(datadir)/meta
meta_DATA = index-enigma2-plugins.xml
CLEANFILES = index-enigma2-plugins.xml

index-enigma2-plugins.xml: $(top_srcdir)/genmetaindex.py $(top_srcdir)/*/meta/plugin_*.xml
	$(AM_V_GEN)$(PYTHON) $^ > $@
