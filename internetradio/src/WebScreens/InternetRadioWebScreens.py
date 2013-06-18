#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Plugins.Extensions.WebInterface.WebScreens import WebScreen

class InternetRadioWebScreens(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Plugins.Extensions.InternetRadio.WebComponents.Sources.InternetRadioWebFavoriteList import InternetRadioWebFavoriteList
		self["InternetRadioFavoriteList"] = InternetRadioWebFavoriteList()

		from Plugins.Extensions.InternetRadio.WebComponents.Sources.InternetRadioWeb import InternetRadioWeb
		self["AddFavorite"] = InternetRadioWeb(session, func=InternetRadioWeb.ADD_FAVORITE)
		self["RemoveFavorite"] = InternetRadioWeb(session, func=InternetRadioWeb.REMOVE_FAVORITE)
		self["RenameFavorite"] = InternetRadioWeb(session, func=InternetRadioWeb.RENAME_FAVORITE)
		self["Play"] = InternetRadioWeb(session, func=InternetRadioWeb.PLAY_STATION)

class InternetRadioStopPlaying(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Plugins.Extensions.InternetRadio.WebComponents.Sources.InternetRadioWeb import InternetRadioWeb
		self["StopPlaying"] = InternetRadioWeb(session, func=InternetRadioWeb.STOP_PLAYING)

class InternetRadioStreamingInfos(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Plugins.Extensions.InternetRadio.WebComponents.Sources.InternetRadioWeb import InternetRadioWeb
		self["StreamingInfos"] = InternetRadioWeb(session, func=InternetRadioWeb.GET_STREAMING_INFOS)

class InternetRadioPlayingStatus(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Plugins.Extensions.InternetRadio.WebComponents.Sources.InternetRadioWeb import InternetRadioWeb
		self["GetPlayingStatus"] = InternetRadioWeb(session, func=InternetRadioWeb.GET_PLAYING_STATUS)
