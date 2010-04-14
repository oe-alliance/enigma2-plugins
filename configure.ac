AC_INIT(enigma2-plugins, 1.0)
AM_INIT_AUTOMAKE(enigma2-plugins, 1.0)

AM_PATH_PYTHON()
AC_PROG_CC
AC_PROG_CXX
AC_PROG_RANLIB
AC_PYTHON_DEVEL

AC_CHECK_HEADER(enigma2/lib/base/i18n.h,have_e2_includes="yes",have_e2_includes="no")
if test x"${have_e2_includes}" = "xyes"; then
	TUXBOX_APPS
	TUXBOX_APPS_DIRECTORY
	TUXBOX_APPS_DVB
	TUXBOX_APPS_LIB_PKGCONFIG(ENIGMA2,enigma2)
	TUXBOX_APPS_LIB_PKGCONFIG(SIGC,sigc++-1.2)
	_TUXBOX_APPS_LIB_PKGCONFIG_OPTIONAL(GSTREAMER,gstreamer,HAVE_GSTREAMER)
	_TUXBOX_APPS_LIB_PKGCONFIG_OPTIONAL(GSTREAMERPBUTILS,gstreamer-pbutils,HAVE_GSTSTREAMERPBUTILS)
	AC_DEFINE(HAVE_E2_INCLUDES, 1,[Define if enigm2 includes are available])
	CXXFLAGS="$CXXFLAGS -fno-rtti -fno-exceptions"
	LDFLAGS="$LDFLAGS -pthread $PYTHON_LDFLAGS"
else
	AC_MSG_NOTICE([enigma2 headers not found.. dont build servicets.so])
fi
AM_CONDITIONAL(HAVE_E2_INCLUDES, test "$have_e2_includes" = "yes")

AC_OUTPUT([
Makefile

ac3lipsync/Makefile
ac3lipsync/img/Makefile
ac3lipsync/meta/Makefile
ac3lipsync/po/Makefile
ac3lipsync/src/Makefile

antiscrollbar/Makefile
antiscrollbar/meta/Makefile
antiscrollbar/src/Makefile

automatictimerlistcleanup/Makefile
automatictimerlistcleanup/meta/Makefile
automatictimerlistcleanup/po/Makefile
automatictimerlistcleanup/src/Makefile

autoresolution/Makefile
autoresolution/meta/Makefile
autoresolution/src/Makefile

autotimer/Makefile
autotimer/meta/Makefile
autotimer/po/Makefile
autotimer/src/Makefile
autotimer/src/webinterface/Makefile

cdinfo/Makefile
cdinfo/meta/Makefile
cdinfo/src/Makefile

dreamirc/Makefile
dreamirc/meta/Makefile
dreamirc/src/Makefile
dreamirc/src/protocols/Makefile

dvdbackup/Makefile
dvdbackup/meta/Makefile
dvdbackup/po/Makefile
dvdbackup/src/Makefile

dyndns/Makefile
dyndns/src/Makefile
dyndns/meta/Makefile

elektro/Makefile
elektro/meta/Makefile
elektro/po/Makefile
elektro/src/Makefile

emailclient/Makefile
emailclient/meta/Makefile
emailclient/po/Makefile
emailclient/src/Makefile

epgrefresh/Makefile
epgrefresh/meta/Makefile
epgrefresh/po/Makefile
epgrefresh/src/Makefile
epgrefresh/src/webinterface/Makefile

epgsearch/Makefile
epgsearch/meta/Makefile
epgsearch/po/Makefile
epgsearch/src/Makefile

filebrowser/Makefile
filebrowser/meta/Makefile
filebrowser/src/Makefile

fritzcall/Makefile
fritzcall/meta/Makefile
fritzcall/po/Makefile
fritzcall/src/Makefile
fritzcall/src/images/Makefile

ftpbrowser/Makefile
ftpbrowser/meta/Makefile
ftpbrowser/po/Makefile
ftpbrowser/src/Makefile
ftpbrowser/src/images/Makefile

genuinedreambox/Makefile
genuinedreambox/meta/Makefile
genuinedreambox/src/Makefile

googlemaps/Makefile
googlemaps/meta/Makefile
googlemaps/src/Makefile

growlee/Makefile
growlee/meta/Makefile
growlee/src/Makefile

httpproxy/Makefile
httpproxy/meta/Makefile
httpproxy/src/Makefile

imdb/Makefile
imdb/meta/Makefile
imdb/po/Makefile
imdb/src/Makefile

kiddytimer/Makefile
kiddytimer/img/Makefile
kiddytimer/meta/Makefile
kiddytimer/po/Makefile
kiddytimer/src/Makefile

lastfm/Makefile
lastfm/meta/Makefile
lastfm/src/Makefile

letterbox/Makefile
letterbox/src/Makefile
letterbox/meta/Makefile

logomanager/Makefile
logomanager/logodir_hdd/Makefile
logomanager/meta/Makefile
logomanager/src/Makefile

mediadownloader/Makefile
mediadownloader/meta/Makefile
mediadownloader/po/Makefile
mediadownloader/src/Makefile

merlinmusicplayer/Makefile
merlinmusicplayer/meta/Makefile
merlinmusicplayer/src/Makefile
merlinmusicplayer/src/images/Makefile
merlinmusicplayer/src/merlinmp3player/Makefile


meteoitalia/Makefile
meteoitalia/meta/Makefile
meteoitalia/src/Makefile

mosaic/Makefile
mosaic/meta/Makefile
mosaic/po/Makefile
mosaic/src/Makefile

moviecut/Makefile
moviecut/meta/Makefile
moviecut/src_cc/Makefile
moviecut/src_py/Makefile

movielistpreview/Makefile
movielistpreview/meta/Makefile
movielistpreview/po/Makefile
movielistpreview/src/Makefile

movieretitle/Makefile
movieretitle/meta/Makefile
movieretitle/po/Makefile
movieretitle/src/Makefile

movieselectionquickbutton/Makefile
movieselectionquickbutton/po/Makefile
movieselectionquickbutton/src/Makefile

movietagger/Makefile
movietagger/etc/Makefile
movietagger/meta/Makefile
movietagger/src/Makefile

multirc/Makefile
multirc/src/Makefile
multirc/meta/Makefile

mytube/Makefile
mytube/meta/Makefile
mytube/po/Makefile
mytube/src/Makefile

netcaster/Makefile
netcaster/meta/Makefile
netcaster/src/Makefile
netcaster/src/bin/Makefile
netcaster/src/bin/interface/Makefile
netcaster/src/etc/Makefile

networkbrowser/Makefile
networkbrowser/meta/Makefile
networkbrowser/po/Makefile
networkbrowser/src/Makefile
networkbrowser/src/icons/Makefile
networkbrowser/src/lib/Makefile

ofdb/Makefile
ofdb/meta/Makefile
ofdb/po/Makefile
ofdb/src/Makefile

orfat/Makefile
orfat/meta/Makefile
orfat/src/Makefile

partnerbox/Makefile
partnerbox/meta/Makefile
partnerbox/po/Makefile
partnerbox/src/Makefile
partnerbox/src/icons/Makefile
partnerbox/src/servicewebts/Makefile

passwordchanger/Makefile
passwordchanger/meta/Makefile
passwordchanger/po/Makefile
passwordchanger/src/Makefile

permanentclock/Makefile
permanentclock/meta/Makefile
permanentclock/po/Makefile
permanentclock/src/Makefile

podcast/Makefile
podcast/etc/Makefile
podcast/meta/Makefile
podcast/po/Makefile
podcast/src/Makefile

porncenter/Makefile
porncenter/meta/Makefile
porncenter/po/Makefile
porncenter/src/Makefile
porncenter/src/Additions/Makefile

quickbutton/Makefile
quickbutton/meta/Makefile
quickbutton/po/Makefile
quickbutton/src/Makefile

reconstructapsc/Makefile
reconstructapsc/meta/Makefile
reconstructapsc/src_cc/Makefile
reconstructapsc/src_py/Makefile

remotetimer/Makefile
remotetimer/meta/Makefile
remotetimer/src/Makefile

rsdownloader/Makefile
rsdownloader/meta/Makefile
rsdownloader/po/Makefile
rsdownloader/src/Makefile
rsdownloader/src/container/Makefile

seekbar/Makefile
seekbar/meta/Makefile
seekbar/po/Makefile
seekbar/src/Makefile

setpasswd/Makefile
setpasswd/meta/Makefile
setpasswd/po/Makefile
setpasswd/src/Makefile

shoutcast/Makefile
shoutcast/meta/Makefile
shoutcast/po/Makefile
shoutcast/src/Makefile

simplerss/Makefile
simplerss/meta/Makefile
simplerss/po/Makefile
simplerss/src/Makefile

startupservice/Makefile
startupservice/meta/Makefile
startupservice/po/Makefile
startupservice/src/Makefile

startuptostandby/Makefile
startuptostandby/meta/Makefile
startuptostandby/src/Makefile

tageditor/Makefile
tageditor/meta/Makefile
tageditor/po/Makefile
tageditor/src/Makefile

trafficinfo/Makefile
trafficinfo/meta/Makefile
trafficinfo/src/Makefile

unwetterzentrale/Makefile
unwetterzentrale/meta/Makefile
unwetterzentrale/src/Makefile

virtualzap/Makefile
virtualzap/meta/Makefile
virtualzap/po/Makefile
virtualzap/src/Makefile

vlcplayer/Makefile
vlcplayer/meta/Makefile
vlcplayer/po/Makefile
vlcplayer/src/Makefile
vlcplayer/src/servicets/Makefile

vxdcontrol/Makefile
vxdcontrol/meta/Makefile
vxdcontrol/src/Makefile
vxdcontrol/src/comp/Makefile
vxdcontrol/src/data/Makefile

weatherplugin/Makefile
weatherplugin/meta/Makefile
weatherplugin/src/Makefile

webcamviewer/Makefile
webcamviewer/meta/Makefile
webcamviewer/src/Makefile

webinterface/Makefile
webinterface/meta/Makefile
webinterface/po/Makefile
webinterface/src/Makefile
webinterface/src/etc/Makefile
webinterface/src/mobile/Makefile
webinterface/src/web/Makefile
webinterface/src/web-data/Makefile
webinterface/src/web-data/gfx/Makefile
webinterface/src/web-data/img/Makefile
webinterface/src/web-data/lib/Makefile
webinterface/src/web-data/tpl/Makefile
webinterface/src/web-data/tpl/default/Makefile
webinterface/src/web-data/tpl/default/streaminterface/Makefile
webinterface/src/web-data/tpl/default/streaminterface/img/Makefile
webinterface/src/WebChilds/Makefile
webinterface/src/WebChilds/External/Makefile
webinterface/src/WebComponents/Makefile
webinterface/src/WebComponents/Converter/Makefile
webinterface/src/WebComponents/Sources/Makefile

werbezapper/Makefile
werbezapper/meta/Makefile
werbezapper/po/Makefile
werbezapper/src/Makefile

youtubeplayer/Makefile
youtubeplayer/meta/Makefile
youtubeplayer/src/Makefile
youtubeplayer/src/Nemesis.GlassLine_Mod/Makefile

zaphistorybrowser/Makefile
zaphistorybrowser/meta/Makefile
zaphistorybrowser/po/Makefile
zaphistorybrowser/src/Makefile

zapstatistic/Makefile
zapstatistic/meta/Makefile
zapstatistic/po/Makefile
zapstatistic/src/Makefile

zdfmediathek/Makefile
zdfmediathek/meta/Makefile
zdfmediathek/src/Makefile

])
