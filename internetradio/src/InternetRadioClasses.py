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

class InternetRadioFilter:
	def __init__(self, name = ""):
		self.name = name

class InternetRadioStation:
	def __init__(self, name = "", tags = "", country = "", url = "", language = "", id = "", homepage = ""):
		if name is None:
			name = ""
		self.name = name
		if tags is None:
			self.genre = self.tags = ""
		else:
			self.genre = tags
			self.tags = ",".join(tags.split(" ")).lower().replace(",,",",")
		self.id = id
		if country is None:
			country = ""
		if homepage is None:
			self.homepage = ""
		else:
			self.homepage = homepage
		self.country = country
		self.url = url
