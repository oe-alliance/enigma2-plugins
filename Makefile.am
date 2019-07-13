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
	channelselectionshorttitle \
	curlytx \
	dreamexplorer \
	dreamirc \
	dreammediathek \
	dvdbackup \
	easyinfo \
	easymedia \
	ecasa \
	eibox \
	emailclient \
	emission \
	eparted \
	epgrefresh \
	eurotictv \
	eventlist \
	eventposition \
	filebrowser \
	flashexpander \
	fritzcall \
	fstabeditor \
	ftpbrowser \
	googlemaps \
	growlee \
	imdb \
	infobartunerstate \
	kiddytimer \
	letterbox \
	mediadownloader \
	merlinepg \
	merlinepgcenter \
	merlinmusicplayer \
	mosaic \
	moviecut \
	movieretitle \
	moviesearch \
	movietagger \
	mphelp \
	multirc \
	ncidclient \
	netcaster \
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
	reftopiconname \
	remotetimer \
	rsdownloader \
	seriesplugin \
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
	weathercomponent \
	weathercomponenthandler \
	webadmin \
	webbouqueteditor \
	webcamviewer \
	werbezapper \
	zaphistorybrowser \
	zapstatistic \
	zdfmediathek \
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

if XC7346
SUBDIRS +=  fancontrol2
endif

if TPM
SUBDIRS += \
	mytube \
	yttrailer \
	webinterface \
	menusort \
	pluginhider \
	pluginsort 
endif

if PLI
SUBDIRS += networkbrowserpli epgsearchpli
else
SUBDIRS += networkbrowser epgsearch
endif

metadir = $(datadir)/meta
meta_DATA = index-enigma2-plugins.xml
CLEANFILES = index-enigma2-plugins.xml

index-enigma2-plugins.xml: $(top_srcdir)/genmetaindex.py $(top_srcdir)/*/meta/plugin_*.xml
	$(AM_V_GEN)$(PYTHON) $^ > $@
