# -*- coding: utf-8 -*-
from Converter import Converter
from time import localtime, strftime
from Components.Element import cached
from Components.config import config


class vConvClockToText(Converter, object):
	DEFAULT = 0
	WITH_SECONDS = 1
	IN_MINUTES = 2
	DATE = 3
	FORMAT = 4
	AS_LENGTH = 5
	TIMESTAMP = 6
	STUNDEN = 7
	LOCDE = 8
	LOCFULL = 9

	def __init__(self, type):
		Converter.__init__(self, type)
		if type == "WithSeconds":
			self.type = self.WITH_SECONDS
		elif type == "InMinutes":
			self.type = self.IN_MINUTES
		elif type == "InStunden":
			self.type = self.STUNDEN
		elif type == "Date":
			self.type = self.DATE
		elif type == "AsLength":
			self.type = self.AS_LENGTH
		elif type == "Timestamp":
			self.type = self.TIMESTAMP
		elif str(type).find("Format") != -1:
			self.type = self.FORMAT
			self.fmt_string = type[7:]
		elif str(type).find("LocaleKurz") != -1:
			self.type = self.LOCDE
			self.fmt_string = type[11:]
		elif str(type).find("LocaleLang") != -1:
			self.type = self.LOCFULL
			self.fmt_string = type[11:]
		else:
			self.type = self.DEFAULT
		if config.osd.language.value == "de_DE":
			self.Tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
			self.Monate = ["Jan", "Feb", u"M\xe4r", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
		elif (config.osd.language.value == "it_IT") or (config.osd.language.value == "es_ES"):
			self.Tage = ["Lu", "Ma", "Me", "Gi", "Ve", "Sa", "Do"]
			self.Monate = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
		else:
			self.Tage = ["Mo", "Tu", "We", "Th", "Fr", "Say", "Su"]
			self.Monate = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

	@cached
	def getText(self):
		time = self.source.time
		if time is None:
			return ""
		if self.type == self.IN_MINUTES:
			return "%d min" % (time / 60)
		elif self.type == self.AS_LENGTH:
			return "%d:%02d" % (time / 60, time % 60)
		elif self.type == self.TIMESTAMP:
			return str(time)
		elif self.type == self.STUNDEN:
			return "%d:%02d" % (time / 3600, (time / 60) - ((time / 3600) * 60))
		t = localtime(time)
		if self.type == self.WITH_SECONDS:
			return "%2d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec)
		elif self.type == self.DEFAULT:
			return "%02d:%02d" % (t.tm_hour, t.tm_min)
		elif self.type == self.DATE:
			return strftime("%A %B %d, %Y", t)
		elif self.type == self.FORMAT:
			spos = self.fmt_string.find('%')
			if spos > 0:
				s1 = self.fmt_string[:spos]
				s2 = strftime(self.fmt_string[spos:], t)
				return str(s1 + s2)
			else:
				return strftime(self.fmt_string, t)
		elif self.type == self.LOCDE:
			spos = self.fmt_string.find('%')
			if not(spos < 0):
				s1 = (strftime(self.fmt_string[spos:], t))
				iAll = s1.split(" ")
				iTag = iAll[0]
				iMonat = iAll[2]
				sOut = self.Tage[int(iTag) - 1] + " " + iAll[1] + ". " + self.Monate[int(iMonat) - 1]
				return str(sOut)
			else:
				return strftime(self.fmt_string, t)
		elif self.type == self.LOCFULL:
			spos = self.fmt_string.find('%')
			if not(spos < 0):
				s1 = (strftime(self.fmt_string[spos:], t))
				iAll = s1.split(" ")
				iTag = iAll[0]
				iMonat = iAll[2]
				sOut = self.Tage[int(iTag) - 1] + " " + iAll[1] + ". " + self.Monate[int(iMonat) - 1]
				zeit = "%02d:%02d" % (t.tm_hour, t.tm_min)
				return str(sOut + "     " + zeit)
			else:
				return strftime(self.fmt_string, t)
		else:
			return "???"

	text = property(getText)
