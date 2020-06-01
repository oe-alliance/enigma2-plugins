# -*- coding: iso-8859-1 -*-

#
# Meoteo Italia da
# www.google.it
#
# Author(s): Bacicciosat - Lupomeo
# Graphics: Army
# Package Maintainer: Spaeleus
#

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Label import Label
from Components.Pixmap import Pixmap
from Tools.Directories import fileExists

from urllib2 import Request, urlopen, URLError, HTTPError
from xml.dom import minidom, Node
from enigma import loadPic, eTimer

import six


METEOITALIA_ABOUT_TXT = "Meteo Italia Info Plugin v 0.1\n\nAuthor(s): Bacicciosat - Lupomeo\nGraphics: Army\nPackage Maintainer: Spaeleus\nRss Meteo: www.google.it\n"

class meteoitMain(Screen):
	skin = """
	<screen position="center,center" size="720,576" flags="wfNoBorder">
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeteoItalia/backg.png" position="0,0" size="720,576" alphatest="on" />
		<widget name="lab1" position="10,100" halign="center" size="700,30" zPosition="1" font="Regular;24" valign="top" transparent="1" />
		<widget name="lab2" position="10,130" halign="center" size="700,30" zPosition="1" font="Regular;22" valign="top" transparent="1" />
		<widget name="lab3" position="340,180" size="40,40" zPosition="1" />
		<widget name="lab4" position="10,220" halign="center" size="700,30" zPosition="1" font="Regular;22" valign="top" transparent="1" />
		<widget name="lab5" position="10,260" halign="center" size="700,60" zPosition="1" font="Regular;22" valign="top" transparent="1" />
		<widget name="lab6" position="0,370" halign="center" size="240,30" zPosition="1" font="Regular;20" valign="top" transparent="1" />
		<widget name="lab7" position="100,400" size="40,40" zPosition="1" />
		<widget name="lab8" position="0,450" halign="center" size="240,80" zPosition="1" font="Regular;20" valign="top" transparent="1" />
		<widget name="lab9" position="240,370" halign="center" size="240,30" zPosition="1" font="Regular;20" valign="top" transparent="1" />
		<widget name="lab10" position="340,400" size="40,40" zPosition="1" />
		<widget name="lab11" position="240,450" halign="center" size="240,80" zPosition="1" font="Regular;20" valign="top" transparent="1" />
		<widget name="lab12" position="480,370" halign="center" size="240,30" zPosition="1" font="Regular;20" valign="top" transparent="1" />
		<widget name="lab13" position="580,400" size="40,40" zPosition="1" />
		<widget name="lab14" position="480,450" halign="center" size="240,80" zPosition="1" font="Regular;20" valign="top" transparent="1" />
	</screen>"""


	def __init__(self, session):
		Screen.__init__(self, session)

		self["lab1"] = Label("Attendere prego, connessione al server in corso...")
		self["lab2"] = Label("")
		self["lab3"] = Pixmap()
		self["lab4"] = Label("")
		self["lab5"] = Label("")
		self["lab6"] = Label("")
		self["lab7"] = Pixmap()
		self["lab8"] = Label("")
		self["lab9"] = Label("")
		self["lab10"] = Pixmap()
		self["lab11"] = Label("")
		self["lab12"] = Label("")
		self["lab13"] = Pixmap()
		self["lab14"] = Label("")
		
		
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"red": self.key_red,
			"green": self.key_green,
			"back": self.close,
			"ok": self.close
		})
		
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.startConnection)
		self.onShow.append(self.startShow)
		self.onClose.append(self.delTimer)


#We use a timer to show the Window in the meanwhile we are connecting to google Server
	def startShow(self):
		self["lab1"].setText("Attendere prego, connessione al server in corso...")
		self.activityTimer.start(10)
		
	def startConnection(self):
		self.activityTimer.stop()
		self.updateInfo()

#We will use this for callbacks too
	def updateInfo(self):
		myurl = self.get_Url()
		req = Request(myurl)
		try:
			handler = urlopen(req)
		except HTTPError as e:
			maintext = "Error: connection failed !"
		except URLError as e:
			maintext = "Error: Page not available !"
		else:
			xml_response = handler.read()
			#xml_response = handler.read().decode('iso-8859-1').encode('utf-8')
			xml_response = self.checkXmlSanity(xml_response)
			dom = minidom.parseString(xml_response)
			handler.close()

			maintext = ""
			tmptext = ""
			if (dom):
				weather_data = {}
				weather_dom = dom.getElementsByTagName('weather')[0]
				data_structure = { 
					'forecast_information': ('postal_code', 'current_date_time'),
					'current_conditions': ('condition', 'temp_c', 'humidity', 'wind_condition', 'icon')
					}
				for (tag, list_of_tags2) in six.iteritems(data_structure):
					tmp_conditions = {}
					for tag2 in list_of_tags2:
						try: 
							tmp_conditions[tag2] =  weather_dom.getElementsByTagName(tag)[0].getElementsByTagName(tag2)[0].getAttribute('data')
						except IndexError:
							pass
						weather_data[tag] = tmp_conditions

					forecast_conditions = ('day_of_week', 'low', 'high', 'icon', 'condition')
					forecasts = []

				for forecast in dom.getElementsByTagName('forecast_conditions'):
					tmp_forecast = {}
					for tag in forecast_conditions:
						tmp_forecast[tag] = forecast.getElementsByTagName(tag)[0].getAttribute('data')
						forecasts.append(tmp_forecast)

					weather_data['forecasts'] = forecasts
					dom.unlink()

				maintext = "Il tempo di oggi a " + str(weather_data['forecast_information']['postal_code'])
				mytime =  str(weather_data['forecast_information']['current_date_time'])
				parts = mytime.strip().split(" ")
				mytime = parts[1]
				self["lab2"].setText("Condizioni del tempo aggiornate alle ore " + mytime)
				
				myicon = self.checkIcon(str(weather_data['current_conditions']['icon']))
# Damn'ed Google gifs .... (we cannot use loadPixmap)			
				png = loadPic(myicon, 40, 40, 0, 0, 0, 1)
				self["lab3"].instance.setPixmap(png)
				
				self["lab4"].setText(self.fixSlang(str(weather_data['current_conditions']['condition'])))
				
				tmptext = "Temperatura: " + str(weather_data['current_conditions']['temp_c']) + " gradi Celsius\n" + str(weather_data['current_conditions']['humidity']) + "   " + str(weather_data['current_conditions']['wind_condition'])
				self["lab5"].setText(tmptext)
				
				tmptext = "Previsioni " + self.eXtendedDay(str(weather_data['forecasts'][1]['day_of_week']))
				self["lab6"].setText(tmptext)
				
				myicon = self.checkIcon(str(weather_data['forecasts'][1]['icon']))
				png = loadPic(myicon, 40, 40, 0, 0, 0, 1)
				self["lab7"].instance.setPixmap(png)
				
				tmptext = self.fixSlang(str(weather_data['forecasts'][1]['condition'])) + "\nTemp. minima: " + str(weather_data['forecasts'][1]['low']) + "\nTemp. massima: " + str(weather_data['forecasts'][1]['high'])
				self["lab8"].setText(tmptext)
				
				tmptext = "Previsioni " + self.eXtendedDay(str(weather_data['forecasts'][2]['day_of_week']))
				self["lab9"].setText(tmptext)
				
				myicon = self.checkIcon(str(weather_data['forecasts'][2]['icon']))
				png = loadPic(myicon, 40, 40, 0, 0, 0, 1)
				self["lab10"].instance.setPixmap(png)
				
				tmptext = self.fixSlang(str(weather_data['forecasts'][2]['condition'])) + "\nTemp. minima: " + str(weather_data['forecasts'][2]['low']) + "\nTemp. massima: " + str(weather_data['forecasts'][2]['high'])
				self["lab11"].setText(tmptext)
				
				tmptext = "Previsioni " + self.eXtendedDay(str(weather_data['forecasts'][3]['day_of_week']))
				self["lab12"].setText(tmptext)
				
				myicon = self.checkIcon(str(weather_data['forecasts'][3]['icon']))
				png = loadPic(myicon, 40, 40, 0, 0, 0, 1)
				self["lab13"].instance.setPixmap(png)
				
				tmptext = self.fixSlang(str(weather_data['forecasts'][3]['condition'])) + "\nTemp. minima: " + str(weather_data['forecasts'][3]['low']) + "\nTemp. massima: " + str(weather_data['forecasts'][3]['high'])
				self["lab14"].setText(tmptext)

			else:
				maintext = "Error getting XML document!"
		
		
		self["lab1"].setText(maintext)
			



# Download icon from Google if we have not yet.
	def checkIcon(self, filename):
		parts = filename.split("/")
		totsp = (len(parts) -1)
		localfile = pluginpath + "/" + parts[totsp]
		if fileExists(localfile):
			pass
		else:
			url = "http://www.google.it" + filename
			handler = urlopen(url)
			if (handler):
				content = handler.read()
				fileout = open(localfile, "wb")
				fileout.write(content)
				handler.close()
				fileout.close()
		
		return localfile

# Bad Google translations (uff.....)
	def fixSlang(self, word):
		if word.find('Chiaro') != -1:
			word = "Sereno"
		return word
		
# Google don't show expanded days
	def eXtendedDay(self, day):
		if day.find('lun') != -1:
			day = "Lunedi'"
		elif day.find('mar') != -1:
			day = "Martedi'"
		elif day.find('mer') != -1:
			day = "Mercoledi'"
		elif day.find('gio') != -1:
			day = "Giovedi'"
		elif day.find('ven') != -1:
			day = "Venerdi'"
		elif day.find('sab') != -1:
			day = "Sabato"
		elif day.find('dom') != -1:
			day = "Domenica"
		return day
			
# Make text safe for xml parser (Google old xml format without the character set declaration)
	def checkXmlSanity(self, content):
		content = content.replace('à', 'a')
		content = content.replace('è', 'e')
		content = content.replace('é', 'e')
		content = content.replace('ì', 'i')
		content = content.replace('ò', 'o')
		content = content.replace('ù', 'u')
		return content

	def get_Url(self):
		url = 'http://www.google.it/ig/api?weather='
		url2 = "Roma"
		cfgfile = pluginpath + "/" + "meteoitalia.cfg"
		if fileExists(cfgfile):
			f = open(cfgfile, 'r')
			line = f.readline()
			url2 = line.strip()
			f.close()
		url = url + url2
		url = url.replace(' ', '%20')
		return url
		
	def delTimer(self):
		del self.activityTimer

	def key_green(self):
		box = self.session.open(MessageBox, METEOITALIA_ABOUT_TXT, MessageBox.TYPE_INFO)
		box.setTitle(_("Informazioni"))
		
	def key_red(self):
		self.session.openWithCallback(self.updateInfo, MeteoitSelectCity)

class MeteoitSelectCity(Screen):
	skin = """
	<screen position="center,center" size="720,576" flags="wfNoBorder">
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeteoItalia/backg.png" position="0,0" size="720,576" alphatest="on" />
		<widget source="list" render="Listbox" position="40,110" zPosition="1" size="640,380" scrollbarMode="showOnDemand" transparent="1" >
			<convert type="StringList" />
		</widget>
		<widget name="lab1" position="10,520" halign="center" size="700,30" zPosition="1" font="Regular;24" valign="top" foregroundColor="#639ACB" transparent="1" />
	</screen>"""


	def __init__(self, session):
		Screen.__init__(self, session)

		self.list = ["Agrigento", "Alessandria", "Ancona", "Andria", "Aosta", "Arezzo", "Ascoli Piceno", "Asti", "Avellino", "Bari",
				"Barletta", "Belluno", "Benevento", "Bergamo", "Biella", "Bologna", "Bolzano", "Brescia", "Brindisi", "Cagliari",
				"Caltanissetta", "Campobasso", "Carbonia", "Caserta", "Catania", "Catanzaro", "Chieti", "Como", "Cosenza",
				"Cremona", "Crotone", "Cuneo", "Enna", "Fermo", "Ferrara", "Firenze", "Foggia", "Forli", "Frosinone", "Genova",
				"Gorizia", "Grosseto", "Iglesias", "Imperia", "Isernia", "La Spezia", "L'Aquila", "Lanusei", "Latina", "Lecce",
				"Lecco", "Livorno", "Lodi", "Lucca", "Macerata", "Mantova", "Massa", "Matera", "Messina", "Milano", "Modena",
				"Monza", "Napoli", "Novara", "Nuoro", "Ogliastra", "Olbia", "Oristano", "Padova", "Palermo", "Parma", "Pavia",
				"Perugia", "Pesaro", "Pescara", "Piacenza", "Pisa", "Pistoia", "Pordenone", "Potenza", "Prato", "Ragusa", "Ravenna",
				"Reggio Calabria", "Reggio Emilia", "Rieti", "Rimini", "Roma", "Rovigo", "Salerno", "Sanluri", "Sassari", "Savona",
				"Siena", "Siracusa", "Sondrio", "Taranto", "Tempio Pausania", "Teramo", "Terni", "Torino", "Trani", "Trapani",
				"Trento", "Treviso", "Trieste", "Udine", "Urbino", "Varese", "Venezia", "Verbania", "Vercelli", "Verona",
				"Vibo Valenzia", "Villacidro", "Vicenza", "Viterbo"]
				
		self["list"] = List(self.list)
		self["lab1"] = Label("Ok per confermare")
		
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"back": self.close,
			"ok": self.saveCfg,
			"green": self.key_green
		})

	def key_green(self):
		box = self.session.open(MessageBox, METEOITALIA_ABOUT_TXT, MessageBox.TYPE_INFO)
		box.setTitle(_("Informazioni"))

	def saveCfg(self):
		city = self["list"].getCurrent()
		if city:
			cfgfile = pluginpath + "/" + "meteoitalia.cfg"
			out = open(cfgfile, "w")
			out.write(city)
		self.close()



def main(session, **kwargs):
	session.open(meteoitMain)	


def Plugins(path,**kwargs):
	global pluginpath
	pluginpath = path
	return PluginDescriptor(name="MeteoItalia", description="Previsioni Meteo", icon="meteoitalia.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
