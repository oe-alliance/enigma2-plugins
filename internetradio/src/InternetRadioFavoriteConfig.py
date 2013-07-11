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

import os
from Components.config import config, ConfigSubsection, Config, ConfigInteger, ConfigSubList, ConfigText
from enigma import eEnv

class Favorite:
	def __init__(self, configItem = None):
		self.configItem = configItem

class InternetRadioFavoriteConfig(object):
	FAVORITE_FILE_DEFAULT =  eEnv.resolve('${libdir}/enigma2/python/Plugins/Extensions/InternetRadio/internetradio_favorites') #'/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/internetradio_favorites'
	FAVORITE_FILE = eEnv.resolve("${sysconfdir}/enigma2/internetradio_favorites.user") #'/etc/enigma2/internetradio_favorites.user'
	def __init__(self):
		self.loadFavoriteConfig()

	def loadFavoriteConfig(self):
		self.favoriteConfig = Config()
		if os.path.exists(self.FAVORITE_FILE):
			self.favoriteConfig.loadFromFile(self.FAVORITE_FILE)
		else:
			self.favoriteConfig.loadFromFile(self.FAVORITE_FILE_DEFAULT)
		self.favoriteConfig.entriescount =  ConfigInteger(0)
		self.favoriteConfig.Entries = ConfigSubList()
		self.initFavouriteConfig()

	def initFavouriteEntryConfig(self):
		self.favoriteConfig.Entries.append(ConfigSubsection())
		i = len(self.favoriteConfig.Entries) -1
		self.favoriteConfig.Entries[i].name = ConfigText(default = "")
		self.favoriteConfig.Entries[i].text = ConfigText(default = "")
		self.favoriteConfig.Entries[i].type = ConfigInteger(0)
		self.favoriteConfig.Entries[i].tags = ConfigText(default = "")
		self.favoriteConfig.Entries[i].country = ConfigText(default = "")
		self.favoriteConfig.Entries[i].homepage = ConfigText(default = "")
		return self.favoriteConfig.Entries[i]

	def initFavouriteConfig(self):
		count = self.favoriteConfig.entriescount.value
		if count != 0:
			i = 0
			while i < count:
				self.initFavouriteEntryConfig()
				i += 1

	def addFavorite(self, name = "", text = "", favoritetype = "", tags = "", country = "", homepage = ""):
		self.favoriteConfig.entriescount.value = self.favoriteConfig.entriescount.value + 1
		self.favoriteConfig.entriescount.save()
		newFavorite = self.initFavouriteEntryConfig()
		newFavorite.name.value = name
		newFavorite.text.value = text
		newFavorite.type.value = favoritetype
		newFavorite.tags.value = tags
		newFavorite.country.value = country
		newFavorite.homepage.value = homepage
		newFavorite.save()
		self.favoriteConfig.saveToFile(self.FAVORITE_FILE)

	def renameFavorite(self, configItem, name, text=None):
			configItem.name.value = name
			if text is not None:
				configItem.text.value = text
			configItem.save()
			self.favoriteConfig.saveToFile(self.FAVORITE_FILE)

	def removeFavorite(self, configItem):
		if configItem is not None:
			self.favoriteConfig.entriescount.value = self.favoriteConfig.entriescount.value - 1
			self.favoriteConfig.entriescount.save()
			self.favoriteConfig.Entries.remove(configItem)
			self.favoriteConfig.Entries.save()
			self.favoriteConfig.saveToFile(self.FAVORITE_FILE)

	def removeFavoriteHTML(self, name, text, favoritetype):
		result = 0
		for item in self.favoriteConfig.Entries:
			if item.name.value == name and item.text.value == text and item.type.value == favoritetype:
				result = 1
				self.removeFavorite(item)
				break
		return result

	def renameFavoriteHTML(self, name, text, favoritetype, newname, newtext=None):
		result = 0
		for item in self.favoriteConfig.Entries:
			if item.name.value == name and item.text.value == text and item.type.value == favoritetype:
				result = 1
				self.renameFavorite(item, newname, newtext)
				break
		return result

	def getFavoriteList(self, html = False):
		favoriteList = []
		for item in self.favoriteConfig.Entries:
			if html == True:
				favoriteList.append((item.name.value, item.text.value, item.type.value, item.tags.value, item.country.value, item.homepage.value))
			else:
				favoriteList.append(((Favorite(item)),))
		return favoriteList
