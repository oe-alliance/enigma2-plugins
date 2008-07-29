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
webinterface/src/WebComponents/Makefile
webinterface/src/WebComponents/Converter/Makefile
webinterface/src/WebComponents/Sources/Makefile

webinterface/src/web-data/Makefile
webinterface/src/web-data/gfx/Makefile

webinterface/src/web-data/lib/Makefile

webinterface/src/web-data/lib/ptwindow/Makefile
webinterface/src/web-data/lib/ptwindow/javascripts/Makefile
webinterface/src/web-data/lib/ptwindow/themes/Makefile
webinterface/src/web-data/lib/ptwindow/themes/alert/Makefile
webinterface/src/web-data/lib/ptwindow/themes/alphacube/Makefile
webinterface/src/web-data/lib/ptwindow/themes/default/Makefile
webinterface/src/web-data/lib/ptwindow/themes/iefix/Makefile

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
fritzcall/po/Makefile

simplerss/Makefile
simplerss/src/Makefile

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

werbezapper/Makefile
werbezapper/src/Makefile

httpproxy/Makefile
httpproxy/src/Makefile

startuptostandby/Makefile
startuptostandby/src/Makefile

imdb/Makefile
imdb/src/Makefile

ofdb/Makefile
ofdb/src/Makefile

networkwizard/Makefile
networkwizard/src/Makefile
networkwizard/po/Makefile

movieretitle/Makefile
movieretitle/src/Makefile

moviecut/Makefile
moviecut/src_cc/Makefile
moviecut/src_py/Makefile

tageditor/Makefile
tageditor/src/Makefile

cdinfo/Makefile
cdinfo/src/Makefile

])
