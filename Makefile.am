ACLOCAL_AMFLAGS = -I m4

SUBDIRS = \
	advhdmi \
	aihdcontroler \
	antiscrollbar \
	aspectratioswitch \
	audiorestart \
	audiosync \
	automaticcleanup \
	automaticvolumeadjustment \
	autoresolution \
	autotimer \
	babelzapper \
	birthdayreminder \
	bonjour \
	cdinfo \
	curlytx \
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
	eurotictv \
	eventlist \
	filebrowser \
	flashexpander \
	fritzcall \
	fstabeditor \
	ftpbrowser \
	googlemaps \
	growlee \
	imdb \
	infobartunerstate \
	internetradio \
	kiddytimer \
	lastfm \
	letterbox \
	mediadownloader \
	merlinepg \
	merlinepgcenter \
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
	permanentclock \
	pipservicerelation \
	podcast \
	porncenter \
	pushservice \
	quickbutton \
	reconstructapsc \
	remotetimer \
	rsdownloader \
	setpasswd \
	shoutcast \
	showclock \
	simplerss \
	subsdownloader2 \
	svdrp \
	tageditor \
	teletext \
	toolkit \
	tvcharts \
	unwetterinfo \
	valixdcontrol \
	videocolorspace \
	vlcplayer \
	vps \
	weatherplugin \
	webadmin \
	webbouqueteditor \
	webcamviewer \
	werbezapper \
	zaphistorybrowser \
	zapstatistic \
	zdfmediathek \
	oscaminfo \
	esame \
	schiffe \
	sudoku \
	vierg \
	bmediacenter \
	advancedmovieselection

if DREAMBOX
SUBDIRS +=  fancontrol2 letterbox logomanager movielistpreview genuinedreambox
endif

if VUSOLO2
SUBDIRS +=  fancontrol2
endif
if VUDUO2
SUBDIRS +=  fancontrol2
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
