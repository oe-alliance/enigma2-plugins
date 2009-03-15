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
antiscrollbar/etc/Makefile
antiscrollbar/src/Makefile

movietagger/Makefile
movietagger/etc/Makefile
movietagger/src/Makefile

webinterface/Makefile
webinterface/etc/Makefile
webinterface/src/Makefile
webinterface/src/web/Makefile
webinterface/src/web/wap/Makefile
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
webinterface/po/Makefile

wirelesslan/Makefile
wirelesslan/src/Makefile
wirelesslan/po/Makefile

netcaster/Makefile
netcaster/src/Makefile
netcaster/src/etc/Makefile
netcaster/src/bin/Makefile
netcaster/src/bin/interface/Makefile

lastfm/Makefile
lastfm/src/Makefile

logomanager/Makefile
logomanager/src/Makefile
logomanager/logodir_hdd/Makefile

vlcplayer/Makefile
vlcplayer/src/Makefile
vlcplayer/src/servicets/Makefile
vlcplayer/po/Makefile

fritzcall/Makefile
fritzcall/src/Makefile
fritzcall/src/images/Makefile
fritzcall/po/Makefile

simplerss/Makefile
simplerss/src/Makefile
simplerss/po/Makefile

trafficinfo/Makefile
trafficinfo/src/Makefile

webcamviewer/Makefile
webcamviewer/src/Makefile

emailclient/Makefile
emailclient/src/Makefile

autotimer/Makefile
autotimer/src/Makefile
autotimer/po/Makefile

epgrefresh/Makefile
epgrefresh/src/Makefile
epgrefresh/src/webinterface/Makefile
epgrefresh/po/Makefile

werbezapper/Makefile
werbezapper/po/Makefile
werbezapper/src/Makefile

httpproxy/Makefile
httpproxy/src/Makefile

startuptostandby/Makefile
startuptostandby/src/Makefile

imdb/Makefile
imdb/src/Makefile
imdb/po/Makefile

ofdb/Makefile
ofdb/src/Makefile
ofdb/po/Makefile

networkwizard/Makefile
networkwizard/src/Makefile
networkwizard/po/Makefile

movieretitle/Makefile
movieretitle/src/Makefile
movieretitle/po/Makefile

moviecut/Makefile
moviecut/src_cc/Makefile
moviecut/src_py/Makefile

tageditor/Makefile
tageditor/src/Makefile
tageditor/po/Makefile

cdinfo/Makefile
cdinfo/src/Makefile

unwetterzentrale/Makefile
unwetterzentrale/src/Makefile

youtubeplayer/Makefile
youtubeplayer/src/Makefile
youtubeplayer/src/Nemesis.GlassLine_Mod/Makefile

zaphistorybrowser/Makefile
zaphistorybrowser/po/Makefile
zaphistorybrowser/src/Makefile

passwordchanger/Makefile
passwordchanger/po/Makefile
passwordchanger/src/Makefile

autoresolution/Makefile
autoresolution/src/Makefile

mosaic/Makefile
mosaic/po/Makefile
mosaic/src/Makefile

googlemaps/Makefile
googlemaps/src/Makefile

rsdownloader/Makefile
rsdownloader/po/Makefile
rsdownloader/src/Makefile

permanentclock/Makefile
permanentclock/po/Makefile
permanentclock/src/Makefile

mediadownloader/Makefile
mediadownloader/po/Makefile
mediadownloader/src/Makefile

epgsearch/Makefile
epgsearch/po/Makefile
epgsearch/src/Makefile

networkbrowser/Makefile
networkbrowser/src/Makefile
networkbrowser/src/icons/Makefile
networkbrowser/src/lib/Makefile
networkbrowser/po/Makefile

ac3lipsync/Makefile
ac3lipsync/po/Makefile
ac3lipsync/img/Makefile
ac3lipsync/src/Makefile
])
