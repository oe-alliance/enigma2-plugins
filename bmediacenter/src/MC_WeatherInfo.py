from Screens.Screen import Screen
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Button import Button
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import *
try:
	from twisted.web.client import getPage
except Exception, e:
	print "Media Center Weather Info: Import twisted.web.client failed"
import os
from __init__ import _
stations = []
names = open("/usr/lib/enigma2/python/Plugins/Extensions/BMediaCenter/weather.config").read().split('\r\n')
for x in names:
	stations.append((x, _(x)))
config.plugins.mc_wi = ConfigSubsection()
config.plugins.mc_wi.city = ConfigSelection(default="Berlin-Deutschland", choices = stations )
config.plugins.mc_wi.cityo = ConfigSelection(default="Frankfurt-Deutschland", choices = stations )
config.plugins.mc_wi.cityt = ConfigSelection(default="Hamburg-Deutschland", choices = stations )
config.plugins.mc_wi.cityth = ConfigSelection(default="Koeln-Deutschland", choices = stations )
config.plugins.mc_wi.cityf = ConfigSelection(default="Muenchen-Deutschland", choices = stations )
config.plugins.mc_wi.citystart = ConfigSelection(default="City", choices = [("City", _("City")),("City2", _("City2")),("City3", _("City3")),("City4", _("City4")),("City5", _("City5"))])
config.plugins.mc_wi.metric = ConfigSelection(default="C", choices = [("C", _("Celsius")),("F", _("Farenheit"))])
config.plugins.mc_wi.language = ConfigSelection(default="de", choices = [("de", _("German")),("en", _("English"))])
url = "http://mipsel-ipk-update.aaf-board.com/Ampel/test.php"
#-------------------------------------------------------#
class MC_WeatherInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self["key_blue"] = Button(_("Settings"))
		self["actions"] = NumberActionMap(["SetupActions", "ColorActions"],
		{
			"cancel": self.close,
			"blue": self.WeatherSetup,
			"left": self.left,
			"right": self.right
		}, -1)
		self["CatTemp"] = Label(_("Humidity :\nWind :"))
		self["CatMinMax"] = Label("Max. :\n\nMin.  :")
		self["CatMinMax1"] = Label("Max. :\n\nMin.  :")
		self["CatMinMax2"] = Label("Max. :\n\nMin.  :")
		self["CatMinMax3"] = Label("Max. :\n\nMin.  :")
		self["TodayPicture"] = Pixmap()
		self["TmrwPicture"] = Pixmap()
		self["TdatPicture"] = Pixmap()
		self["NTdatPicture"] = Pixmap()
		self["NNTdatPicture"] = Pixmap()
		self["CurrentCity"] = Label(_("Updating Weather Info ..."))
		self["TodayTemp"] = Label("")
		self["TodayPrecip"] = Label("")
		self["TodayHumidityWind"] = Label("")
		self["TmrwDay"] = Label("")
		self["TmrwMinMax"] = Label("")
		self["TmrwPrecip"] = Label("")
		self["TdatDay"] = Label("")
		self["TdatMinMax"] = Label("")
		self["TdatPrecip"] = Label("")
		self["NTdatDay"] = Label("")
		self["NTdatMinMax"] = Label("")
		self["NTdatPrecip"] = Label("")
		self["NNTdatDay"] = Label("")
		self["NNTdatMinMax"] = Label("")
		self["NNTdatPrecip"] = Label("")
		self.onFirstExecBegin.append(self.GetWeatherInfo)
	def error(self, error):
		self.session.open(MessageBox,("UNEXPECTED ERROR:\n%s") % (error),  MessageBox.TYPE_INFO)
	def left(self):
		if config.plugins.mc_wi.citystart.value == "City":
			config.plugins.mc_wi.citystart.value = "City5"
		elif config.plugins.mc_wi.citystart.value == "City2":
			config.plugins.mc_wi.citystart.value = "City"
		elif config.plugins.mc_wi.citystart.value == "City3":
			config.plugins.mc_wi.citystart.value = "City2"
		elif config.plugins.mc_wi.citystart.value == "City4":
			config.plugins.mc_wi.citystart.value = "City3"
		elif config.plugins.mc_wi.citystart.value == "City5":
			config.plugins.mc_wi.citystart.value = "City4"
		config.plugins.mc_wi.save()
		self.GetWeatherInfo()
	def right(self):
		if config.plugins.mc_wi.citystart.value == "City":
			config.plugins.mc_wi.citystart.value = "City2"
		elif config.plugins.mc_wi.citystart.value == "City2":
			config.plugins.mc_wi.citystart.value = "City3"
		elif config.plugins.mc_wi.citystart.value == "City3":
			config.plugins.mc_wi.citystart.value = "City4"
		elif config.plugins.mc_wi.citystart.value == "City4":
			config.plugins.mc_wi.citystart.value = "City5"
		elif config.plugins.mc_wi.citystart.value == "City5":
			config.plugins.mc_wi.citystart.value = "City"
		config.plugins.mc_wi.save()
		self.GetWeatherInfo()
	def WeatherSetup(self):
		self.session.openWithCallback(self.GetWeatherInfo, WeatherSetup)
	def GetWeatherInfo(self):
		if config.plugins.mc_wi.citystart.value == "City":
			self.url = "%s?s=%s&l=%s&met=%s" % (url, config.plugins.mc_wi.city.value, config.plugins.mc_wi.language.value, config.plugins.mc_wi.metric.value)
		elif config.plugins.mc_wi.citystart.value == "City2":
			self.url = "%s?s=%s&l=%s&met=%s" % (url, config.plugins.mc_wi.cityo.value, config.plugins.mc_wi.language.value, config.plugins.mc_wi.metric.value)
		elif config.plugins.mc_wi.citystart.value == "City3":
			self.url = "%s?s=%s&l=%s&met=%s" % (url, config.plugins.mc_wi.cityt.value, config.plugins.mc_wi.language.value, config.plugins.mc_wi.metric.value)
		elif config.plugins.mc_wi.citystart.value == "City4":
			self.url = "%s?s=%s&l=%s&met=%s" % (url, config.plugins.mc_wi.cityth.value, config.plugins.mc_wi.language.value, config.plugins.mc_wi.metric.value)
		elif config.plugins.mc_wi.citystart.value == "City5":
			self.url = "%s?s=%s&l=%s&met=%s" % (url, config.plugins.mc_wi.cityf.value, config.plugins.mc_wi.language.value, config.plugins.mc_wi.metric.value)
		try:
			getPage(self.url).addCallback(self.UpdateWeatherInfo).addErrback(self.error)
			self["CurrentCity"].setText(_("Updating Weather Info ..."))
		except Exception, e:
			self["CurrentCity"].setText(_("Updating Weather Info failed (Twisted Web not installed)"))
	def UpdateWeatherInfo(self, html):
		wi_iline = html.splitlines()
		self["TodayTemp"].setText(wi_iline[1])
		self["TodayPrecip"].setText(wi_iline[2])
		self["TodayHumidityWind"].setText(wi_iline[4] +"\n"+ wi_iline[3])
		self["TodayPicture"].instance.setPixmapFromFile(wi_iline[5])
		self["TmrwDay"].setText(wi_iline[7])
		self["TmrwMinMax"].setText(wi_iline[10] +"\n\n"+ wi_iline[9])
		self["TmrwPrecip"].setText(wi_iline[8])
		self["TmrwPicture"].instance.setPixmapFromFile(wi_iline[11])
		self["TdatDay"].setText(wi_iline[13])
		self["TdatMinMax"].setText(wi_iline[16] +"\n\n"+ wi_iline[15])
		self["TdatPrecip"].setText(wi_iline[14])
		self["TdatPicture"].instance.setPixmapFromFile(wi_iline[17])
		self["NTdatDay"].setText(wi_iline[18])
		self["NTdatMinMax"].setText(wi_iline[21] +"\n\n"+ wi_iline[20])
		self["NTdatPrecip"].setText(wi_iline[19])
		self["NTdatPicture"].instance.setPixmapFromFile(wi_iline[22])
		self["NNTdatDay"].setText(wi_iline[23])
		self["NNTdatMinMax"].setText(wi_iline[26] +"\n\n"+ wi_iline[25])
		self["NNTdatPrecip"].setText(wi_iline[24])
		self["NNTdatPicture"].instance.setPixmapFromFile(wi_iline[27])
		if config.plugins.mc_wi.citystart.value == "City":
			self["CurrentCity"].setText(config.plugins.mc_wi.city.getText())
		elif config.plugins.mc_wi.citystart.value == "City2":
			self["CurrentCity"].setText(config.plugins.mc_wi.cityo.getText())
		elif config.plugins.mc_wi.citystart.value == "City3":
			self["CurrentCity"].setText(config.plugins.mc_wi.cityt.getText())
		elif config.plugins.mc_wi.citystart.value == "City4":
			self["CurrentCity"].setText(config.plugins.mc_wi.cityth.getText())
		elif config.plugins.mc_wi.citystart.value == "City5":
			self["CurrentCity"].setText(config.plugins.mc_wi.cityf.getText())
#-------------------------------------------------------#
class WeatherSetup(Screen, ConfigListScreen):
	skin = """
		<screen name="WeatherSetup" position="80,140" size="560,330" title="Edit Weather Info Settings">
			<widget name="config" position="10,10" size="540,250" scrollbarMode="showOnDemand" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = NumberActionMap(["SetupActions","OkCancelActions"],
		{
			"ok": self.keyOK,
			"cancel": self.close
		}, -1)
		self.list = []
		self.list.append(getConfigListEntry(_("City"), config.plugins.mc_wi.city))
		self.list.append(getConfigListEntry(_("City 2"), config.plugins.mc_wi.cityo))
		self.list.append(getConfigListEntry(_("City 3"), config.plugins.mc_wi.cityt))
		self.list.append(getConfigListEntry(_("City 4"), config.plugins.mc_wi.cityth))
		self.list.append(getConfigListEntry(_("City 5"), config.plugins.mc_wi.cityf))
		self.list.append(getConfigListEntry(_("Metric"), config.plugins.mc_wi.metric))
		self.list.append(getConfigListEntry(_("Language"), config.plugins.mc_wi.language))
		ConfigListScreen.__init__(self, self.list, session)
	def keyOK(self):
		config.plugins.mc_wi.save()
		self.close()