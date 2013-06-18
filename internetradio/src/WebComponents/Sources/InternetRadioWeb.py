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

from Components.Sources.Source import Source
from Screens.InfoBar import InfoBar
from Plugins.Extensions.InternetRadio.InternetRadioFavoriteConfig import InternetRadioFavoriteConfig
from Plugins.Extensions.InternetRadio.InternetRadioScreen import InternetRadioScreen
from Plugins.Extensions.InternetRadio.InternetRadioClasses import InternetRadioStation

class InternetRadioWeb(Source):

	ADD_FAVORITE = 0
	REMOVE_FAVORITE = 1
	RENAME_FAVORITE = 3
	PLAY_STATION = 4
	GET_PLAYING_STATUS = 5
	GET_STREAMING_INFOS = 6
	STOP_PLAYING = 7

	def __init__(self, session, func=ADD_FAVORITE):
		Source.__init__(self)
		self.func = func
		self.session = session
		self.command = None
		if self.func is self.GET_PLAYING_STATUS:
			self.result = self.getPlayingStatus()
		elif self.func is self.GET_STREAMING_INFOS:
			self.result = self.getStreamingInfos()
		elif self.func is self.STOP_PLAYING:
			self.result = self.stopPlaying()
		else:
			self.result = ( False, "one two three four unknown command" )

	def handleCommand(self, cmd):
		print "[WebComponents.InternetRadioWeb] handleCommand with cmd = ", cmd
		if self.func is self.ADD_FAVORITE:
			self.result = self.addFavorite(cmd)
		elif self.func is self.REMOVE_FAVORITE:
			self.result = self.removeFavorite(cmd)
		elif self.func is self.RENAME_FAVORITE:
			self.result = self.renameFavorite(cmd)
		elif self.func is self.PLAY_STATION:
				self.result = self.playStation(cmd)
		else:
			self.result = ( False, "one two three four unknown command" )

	def addFavorite(self, param):
		print "[WebComponents.InternetRadioWeb] addFavorite with param = ", param
		name = param["name"]
		if name is None:
			return (False, "No favorite name given!")
		text = param["text"]
		if text is None:
			text = name
		favoritetype = param["favoritetype"]
		if favoritetype is None:
			return (False, "No favorite type given!")
		elif favoritetype.isdigit() == False:
			return (False, "favorite type has to be a number between 0 and 2!")
		tags = param["tags"]
		if tags is None:
			tags = ""
		country = param["country"]
		if country is None:
			country = ""
		homepage = param["homepage"]
		if homepage is None:
			homepage = ""
		favoriteConfig = InternetRadioFavoriteConfig()
		favoriteConfig.addFavorite(name = name, text = text, favoritetype = int(favoritetype), tags = tags, country = country, homepage = homepage)
		player = self.getPlayerInstance()
		if player is not None:
			player.updateFavoriteList()
		return (True, "favorite %s added." % name)

	def removeFavorite(self, param):
		print "[WebComponents.InternetRadioWeb] removeFavorite with param = ", param
		name = param["name"]
		if name is None:
			return (False, "No favorite name given!")
		text = param["text"]
		if text is None:
			text = name
		favoritetype = param["favoritetype"]
		if favoritetype is None:
			return (False, "No favorite type given!")
		elif favoritetype.isdigit() == False:
			return (False, "favorite type has to be a number between 0 and 2!")
		found = 0
		favoriteConfig = InternetRadioFavoriteConfig()
		if favoriteConfig.removeFavoriteHTML(name = name, text = text, favoritetype = int(favoritetype)) == 1:
			player = self.getPlayerInstance()
			if player is not None:
				player.updateFavoriteList()
			return (True, "favorite %s removed." % name)
		else:
			return (False, "Could not find favorite %s!" % name)

	def renameFavorite(self, param):
		print "[WebComponents.InternetRadioWeb] renameFavorite with param = ", param
		name = param["name"]
		if name is None:
			return (False, "No favorite name given!")

		text = param.get("text", name)
		newtext = param.get("newtext", None)

		favoritetype = param["favoritetype"]
		if favoritetype is None:
			return (False, "No favorite type given!")
		elif favoritetype.isdigit() == False:
			return (False, "favorite type has to be a number between 0 and 2!")
		newname = param["newname"]
		if newname is None:
			return (False, "No favorite newname given!")
		found = 0
		favoriteConfig = InternetRadioFavoriteConfig()
		if favoriteConfig.renameFavoriteHTML(name = name, text = text, favoritetype = int(favoritetype), newname = newname, newtext = newtext) == 1:
			player = self.getPlayerInstance()
			if player is not None:
				player.updateFavoriteList()
			return (True, "favorite %s renamed." % name)
		else:
			return (False, "Could not find favorite %s!" % name)


	def playStation(self, param):
		print "[WebComponents.InternetRadioWeb] playStation with param = ", param
		name = param["name"]
		if name is None:
			name = ""
		url = param["url"]
		if url is None:
			return (False, "No url given!")
		radioStation = InternetRadioStation(name = name)
		player = self.getPlayerInstance()
		if player is not None:
			player.playRadioStation(url, radioStation)
			player.updateFullscreenStationName(radioStation.name)
			return (True, "%s opend." % url)
		else:
			# start plugin only when no other screen is open...
			if isinstance(self.session.current_dialog, InfoBar):
				player = self.session.open(InternetRadioScreen, url, radioStation)
				return (True, "%s opend." % url)
			else:
				return (False, "Player can not start because there is another screen already open.")

	def getPlayingStatus(self):
		player = self.getPlayerInstance()
		if player is not None:
			return player.getCurrentPlayingStation()
		else:
			return (False, "InternetRadio plugin is not running...")

	def getStreamingInfos(self):
		player = self.getPlayerInstance()
		if player is not None:
			return (True, player.getStreamingInfos())
		else:
			return (False, "InternetRadio plugin is not running...")

	def stopPlaying(self):
		player = self.getPlayerInstance()
		if player is not None:
			player.closePlayer()
		return (True, "Done...")

	def getPlayerInstance(self):
		if isinstance(self.session.current_dialog, InternetRadioScreen):
			return self.session.current_dialog
		else:
			return None
