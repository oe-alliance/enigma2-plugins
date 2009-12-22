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
	AC_DEFINE(HAVE_E2_INCLUDES, 1,[Define if enigm2 includes are available])
	CXXFLAGS="$CXXFLAGS -fno-rtti -fno-exceptions"
	LDFLAGS="$LDFLAGS -pthread $PYTHON_LDFLAGS"
else
	AC_MSG_NOTICE([enigma2 headers not found.. dont build servicets.so])
fi
AM_CONDITIONAL(HAVE_E2_INCLUDES, test "$have_e2_includes" = "yes")

AC_OUTPUT([
Makefile
antiscrollbar/Makefile
antiscrollbar/src/Makefile
antiscrollbar/meta/Makefile

movietagger/Makefile
movietagger/etc/Makefile
movietagger/src/Makefile
movietagger/meta/Makefile

webinterface/Makefile
webinterface/src/etc/Makefile
webinterface/src/Makefile
webinterface/src/web/Makefile
webinterface/src/mobile/Makefile
webinterface/src/WebChilds/Makefile
webinterface/src/WebChilds/External/Makefile
webinterface/src/WebComponents/Makefile
webinterface/src/WebComponents/Converter/Makefile
webinterface/src/WebComponents/Sources/Makefile

webinterface/src/web-data/Makefile
webinterface/src/web-data/gfx/Makefile
webinterface/src/web-data/img/Makefile
webinterface/src/web-data/lib/Makefile
webinterface/src/web-data/tpl/Makefile
webinterface/src/web-data/tpl/default/Makefile
webinterface/src/web-data/tpl/default/streaminterface/Makefile
webinterface/src/web-data/tpl/default/streaminterface/img/Makefile
webinterface/po/Makefile
webinterface/meta/Makefile

netcaster/Makefile
netcaster/src/Makefile
netcaster/src/etc/Makefile
netcaster/src/bin/Makefile
netcaster/src/bin/interface/Makefile
netcaster/meta/Makefile

lastfm/Makefile
lastfm/src/Makefile
lastfm/meta/Makefile

logomanager/Makefile
logomanager/src/Makefile
logomanager/logodir_hdd/Makefile
logomanager/meta/Makefile

vlcplayer/Makefile
vlcplayer/src/Makefile
vlcplayer/src/servicets/Makefile
vlcplayer/po/Makefile
vlcplayer/meta/Makefile

fritzcall/Makefile
fritzcall/src/Makefile
fritzcall/src/images/Makefile
fritzcall/po/Makefile
fritzcall/meta/Makefile

simplerss/Makefile
simplerss/src/Makefile
simplerss/po/Makefile
simplerss/meta/Makefile

trafficinfo/Makefile
trafficinfo/src/Makefile
trafficinfo/meta/Makefile

webcamviewer/Makefile
webcamviewer/src/Makefile
webcamviewer/meta/Makefile

emailclient/Makefile
emailclient/src/Makefile
emailclient/po/Makefile
emailclient/meta/Makefile

autotimer/Makefile
autotimer/src/Makefile
autotimer/src/webinterface/Makefile
autotimer/po/Makefile
autotimer/meta/Makefile

epgrefresh/Makefile
epgrefresh/src/Makefile
epgrefresh/src/webinterface/Makefile
epgrefresh/po/Makefile
epgrefresh/meta/Makefile

werbezapper/Makefile
werbezapper/po/Makefile
werbezapper/src/Makefile
werbezapper/meta/Makefile

httpproxy/Makefile
httpproxy/src/Makefile
httpproxy/meta/Makefile

startuptostandby/Makefile
startuptostandby/src/Makefile
startuptostandby/meta/Makefile

imdb/Makefile
imdb/src/Makefile
imdb/po/Makefile
imdb/meta/Makefile

ofdb/Makefile
ofdb/src/Makefile
ofdb/po/Makefile
ofdb/meta/Makefile

movieretitle/Makefile
movieretitle/src/Makefile
movieretitle/po/Makefile
movieretitle/meta/Makefile

moviecut/Makefile
moviecut/src_cc/Makefile
moviecut/src_py/Makefile
moviecut/meta/Makefile

tageditor/Makefile
tageditor/src/Makefile
tageditor/po/Makefile
tageditor/meta/Makefile

cdinfo/Makefile
cdinfo/src/Makefile
cdinfo/meta/Makefile

unwetterzentrale/Makefile
unwetterzentrale/src/Makefile
unwetterzentrale/meta/Makefile

youtubeplayer/Makefile
youtubeplayer/src/Makefile
youtubeplayer/src/Nemesis.GlassLine_Mod/Makefile
youtubeplayer/meta/Makefile

zaphistorybrowser/Makefile
zaphistorybrowser/po/Makefile
zaphistorybrowser/src/Makefile
zaphistorybrowser/meta/Makefile

passwordchanger/Makefile
passwordchanger/po/Makefile
passwordchanger/src/Makefile
passwordchanger/meta/Makefile

autoresolution/Makefile
autoresolution/src/Makefile
autoresolution/meta/Makefile

mosaic/Makefile
mosaic/po/Makefile
mosaic/src/Makefile
mosaic/meta/Makefile

googlemaps/Makefile
googlemaps/src/Makefile
googlemaps/meta/Makefile

rsdownloader/Makefile
rsdownloader/po/Makefile
rsdownloader/src/Makefile
rsdownloader/src/container/Makefile
rsdownloader/meta/Makefile

permanentclock/Makefile
permanentclock/po/Makefile
permanentclock/src/Makefile
permanentclock/meta/Makefile

mediadownloader/Makefile
mediadownloader/po/Makefile
mediadownloader/src/Makefile
mediadownloader/meta/Makefile

epgsearch/Makefile
epgsearch/po/Makefile
epgsearch/src/Makefile
epgsearch/meta/Makefile

networkbrowser/Makefile
networkbrowser/src/Makefile
networkbrowser/src/icons/Makefile
networkbrowser/src/lib/Makefile
networkbrowser/po/Makefile
networkbrowser/meta/Makefile

ac3lipsync/Makefile
ac3lipsync/po/Makefile
ac3lipsync/img/Makefile
ac3lipsync/src/Makefile
ac3lipsync/meta/Makefile

dreamirc/Makefile
dreamirc/src/Makefile
dreamirc/src/protocols/Makefile
dreamirc/meta/Makefile

remotetimer/Makefile
remotetimer/src/Makefile
remotetimer/meta/Makefile

partnerbox/Makefile
partnerbox/src/Makefile
partnerbox/src/servicewebts/Makefile
partnerbox/src/icons/Makefile
partnerbox/po/Makefile
partnerbox/meta/Makefile

quickbutton/Makefile
quickbutton/po/Makefile
quickbutton/src/Makefile
quickbutton/meta/Makefile

setpasswd/Makefile
setpasswd/po/Makefile
setpasswd/src/Makefile
setpasswd/meta/Makefile

mytube/Makefile
mytube/po/Makefile
mytube/src/Makefile
mytube/meta/Makefile

orfat/Makefile
orfat/src/Makefile
orfat/meta/Makefile

filebrowser/Makefile
filebrowser/src/Makefile
filebrowser/meta/Makefile

podcast/Makefile
podcast/etc/Makefile
podcast/po/Makefile
podcast/src/Makefile
podcast/meta/Makefile

genuinedreambox/Makefile
genuinedreambox/src/Makefile
genuinedreambox/meta/Makefile

kiddytimer/Makefile
kiddytimer/img/Makefile
kiddytimer/po/Makefile
kiddytimer/src/Makefile
kiddytimer/meta/Makefile

elektro/Makefile
elektro/po/Makefile
elektro/src/Makefile
elektro/meta/Makefile

ftpbrowser/Makefile
ftpbrowser/po/Makefile
ftpbrowser/src/Makefile
ftpbrowser/src/images/Makefile
ftpbrowser/meta/Makefile

growlee/Makefile
growlee/src/Makefile
growlee/meta/Makefile

meteoitalia/Makefile
meteoitalia/src/Makefile

weatherplugin/Makefile
weatherplugin/src/Makefile
weatherplugin/meta/Makefile

startupservice/Makefile
startupservice/po/Makefile
startupservice/src/Makefile
startupservice/meta/Makefile

movieselectionquickbutton/Makefile
movieselectionquickbutton/po/Makefile
movieselectionquickbutton/src/Makefile

])
