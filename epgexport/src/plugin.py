##########################################################################
#  EPG Export - Plugin to export your EPG as XMLTV files (c) by gutemine #
#  This program is free software; you can redistribute it and/or         #
#  modify it under the terms of the GNU General Public License           #
#  as published by the Free Software Foundation; either version 3        #
#  of the License, or (at your option) any later version.                #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#  GNU General Public License for more details.                          #
##########################################################################
#  ORIGINAL SOURCE (FORKED FROM):                                        #
#    - https://github.com/leaskovski/EPGExport/blob/master/src/plugin.py #
#  2023-03-29 edit by s3n0:                                              #
#    - source code modified for Python3 support                          #
#    - CONTROL file (inside the IPK file) dependencies changed to:       #
#      python3-requests python3-backports-lzma                           #
##########################################################################

# PYTHON IMPORTS
from backports.lzma import open as lzmaopen
from os import mkdir, symlink, remove, listdir, readlink
from os.path import join, exists, islink, basename
from gzip import open as gzipopen
from time import time, localtime, mktime, strftime
from datetime import datetime, timezone
import xml.etree.ElementTree as etree
from shutil import rmtree
from socket import gethostname, getfqdn
from time import gmtime, strftime
from twisted.internet.threads import deferToThread
from twisted.internet.reactor import listenTCP, run
from twisted.web import http, static
from twisted.web.resource import Resource
from twisted.web.server import Site
from xml.etree.ElementTree import tostring, parse

# ENIGMA IMPORTS
from enigma import getDesktop, eTimer, eEPGCache, eServiceCenter, eServiceReference
from Components.ConfigList import ConfigListScreen
from Components.ActionMap import ActionMap
from Components.config import config, ConfigText, ConfigYesNo, ConfigInteger, ConfigSelection, ConfigSubsection, getConfigListEntry, ConfigIP, ConfigSubList, ConfigClock
from Components.Network import iNetwork
from Components.Pixmap import Pixmap
from Components.Renderer.Picon import getPiconName
from Components.Sources.StaticText import StaticText
from Screens.InfoBar import InfoBar
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from ServiceReference import ServiceReference
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_SYSETC, SCOPE_PLUGINS

# PLUGIN IMPORTS
from . import _  # for localized messages

# GLOBALS
global WebTimer
global WebTimer_conn
global AutoStartTimer
SERVICELIST = None
VERSION = "1.5-r8"
EXPORTPATH = "%s%s" % (resolveFilename(SCOPE_SYSETC), "epgexport")  # /etc/epgexport
CHANNELS = join(EXPORTPATH, "epgexport.channels")
DESTINATION = {"etc": EXPORTPATH, "volatile": "/tmp/epgexport", "data": "/data/epgexport", "hdd": "/media/hdd/epgexport", "usb": "/media/usb/epgexport", "sdcard": "/media/sdcard/epgexport"}

config.plugins.epgexport = ConfigSubsection()
compr_opt = []
compr_opt.append(("none", "%s (xml)" % _("none")))
compr_opt.append(("xz", _("xz")))
compr_opt.append(("gz", _("gz")))
config.plugins.epgexport.compression = ConfigSelection(default="xz", choices=compr_opt)
with open("/proc/mounts", "r") as f:
	mounts = f.read()
save_opt = []
save_opt.append(("etc", DESTINATION.get("etc", None)))
save_opt.append(("volatile", DESTINATION.get("volatile", None)))
for dest in ["/data", "/media/hdd", "/media/usb", "/media/sdcard"]:
	if mounts.find(dest) != -1:
		key = dest[dest.rfind("/") + 1:]
		value = DESTINATION.get(key, None)
		if value:
			save_opt.append((key, value))
print("save_opt: %s" % str(save_opt))
config.plugins.epgexport.epgexport = ConfigSelection(default="volatile", choices=save_opt)
channel_opt = []
channel_opt.append(("name", "%s %s" % (_("Channel"), _("Name"))))
channel_opt.append(("names", "%s%s" % (_("Channel"), _("Name"))))
cname = "%s%s" % (_("Channel"), _("Name"))
channel_opt.append(("nameslow", cname.lower()))
channel_opt.append(("nameslang", "%s.%s" % (cname, _("Language").lower())))
channel_opt.append(("nameslowlang", "%s.%s" % (cname.lower(), _("Language").lower())))
channel_opt.append(("number", "%s %s" % (_("Channel"), _("Number"))))
channel_opt.append(("xml", _("Custom (%s)") % "xml"))
config.plugins.epgexport.channelid = ConfigSelection(default="name", choices=channel_opt)
config.plugins.epgexport.twisted = ConfigYesNo(default=True)
config.plugins.epgexport.server = ConfigSelection(default="none", choices=[("none", _("disabled")), ("ip", _("IP Address")), ("name", _("Server IP").replace("IP", _("Name")))])
config.plugins.epgexport.ip = ConfigIP(default=[192, 168, 0, 100])
config.plugins.epgexport.hostname = ConfigText(default="localhost", fixed_size=False)
config.plugins.epgexport.webinterface = ConfigYesNo(default=False)
config.plugins.epgexport.port = ConfigInteger(default=4444, limits=(4000, 4999))
days_options = []
for days in range(1, 31):
	days_options.append((str(days), str(days)))
config.plugins.epgexport.days = ConfigSelection(default="5", choices=days_options)
reload_options = []
reload_options.append(("0", _("always")))
for hours in range(1, 25):
	reload_options.append((str(hours), str(hours)))
config.plugins.epgexport.reload = ConfigSelection(default="0", choices=reload_options)
config.plugins.epgexport.hours = ConfigSelection(default=0, choices=[("0", _("disabled")), ("1", _("every hour")), ("2", _("every 2 hours")), ("6", _("every 6 hours")), ("12", _("every 12 hours")), ("24", _("daily"))])
config.plugins.epgexport.wakeup = ConfigClock(default=((6 * 60) + 45) * 60)
outdated_options = []
outdated_options.append(("0", _("none")))
for days in range(1, 8):
	outdated_options.append((str(days), str(days)))
config.plugins.epgexport.outdated = ConfigSelection(default="0", choices=outdated_options)
bouquet_options = []
enigma2 = resolveFilename(SCOPE_SYSETC, "enigma2")  # /etc/enigma2
for bouquet in listdir(enigma2):
	if bouquet.startswith("userbouquet.") and bouquet.endswith(".tv"):
		with open(join(enigma2, bouquet), encoding="utf8", errors='ignore') as f:
			name = f.readline()
		name = name.replace("#NAME ", "").replace(" (TV)", "").rstrip()
		bouquet_options.append((name.lower(), name))
fav = False
for bouquet in bouquet_options:
	if bouquet[0].startswith("fav"):
		fav = True
		break
if not fav:  # prevent crashes if default not found...
	bouquet_options.append(("favorites", _("Favorites")))
bouquet_options.sort()
config.plugins.epgexport.bouquets = ConfigSubList()
bouquet_length = len(bouquet_options)
for x in range(bouquet_length):
	config.plugins.epgexport.bouquets.append(ConfigSubsection())
	config.plugins.epgexport.bouquets[x].export = ConfigYesNo(default=False)
	config.plugins.epgexport.bouquets[x].name = ConfigText(default="")
	config.plugins.epgexport.bouquets[x].name.value = bouquet_options[x][0]
	config.plugins.epgexport.bouquets[x].name.save()


def cprint(text):
	with open("/tmp/epgexport.log", "a") as f:
		f.write("%s: %s\n" % (strftime("%x %X", gmtime()), text))


def checkLastUpdate():
	update_file_name = join(EXPORTPATH, "LastUpdate.txt")
	update = True
	if not exists("%s.%s" % (CHANNELS, "xml.xz")):
		return update
	if not exists(join(EXPORTPATH, "epgexport.xml.xz")):
		return update
	if exists(update_file_name):  # Used to check server validity
		date_format = "%Y-%m-%d %H:%M:%S"
		allowed_delta = 3600 * int(config.plugins.epgexport.reload.value)
		now = int(time())
		cprint("now %d" % now)
		with open(update_file_name, "r") as x:
			Last = x.readline()
		LastTime = Last.strip("\n")
		FileDate = datetime.strptime(LastTime, date_format)
		file_date = int(FileDate.strftime("%s"))
		cprint("File Date %d" % file_date)
		delta = (now - file_date)
		cprint("delta seconds %d" % delta)
		if delta <= allowed_delta:
			update = False
	return update


def exportLastUpdate():
	now = datetime.now()  # always use current date and time
	date = now.strftime("%Y-%m-%d %H:%M:%S")
	cprint("date: %s" % date)
	update_file_name = join(EXPORTPATH, "LastUpdate.txt")
	with open(update_file_name, "w") as f:
		f.write(date)
		f.write("\n")


def startEPGExport(session, **kwargs):
	global SERVICELIST
	slist = kwargs.get("SERVICELIST", None)
	if slist is None and InfoBar is not None:
		InfoBarInstance = InfoBar.instance
		if InfoBarInstance is not None:
			slist = InfoBarInstance.servicelist
	SERVICELIST = slist
	session.open(EPGExportConfiguration)


def cleanepgexport(keep=False):
	if keep:
		for file in [join(EXPORTPATH, "LastUpdate.txt"), "%s.%s" % (CHANNELS, "xml"), "%s.%s" % (CHANNELS, "xml.gz"), "%s.%s" % (CHANNELS, "xml.xz"), join(EXPORTPATH, "epgexport.xml"), join(EXPORTPATH, "epgexport.xml.gz"), join(EXPORTPATH, "epgexport.xml.xz"), join(EXPORTPATH, "custom.channels.xml")]:
			if exists(file):
				remove(file)
	elif exists(EXPORTPATH):
		rmtree(EXPORTPATH)


def fixepgexport():
	save_path = config.plugins.epgexport.epgexport.value
	if save_path == "etc":
		if islink(EXPORTPATH):
			remove(EXPORTPATH)
			mkdir(EXPORTPATH, mode=0o777)
			cprint("old link '%s' removed, new directory '%s' created" % (EXPORTPATH, EXPORTPATH))
		cprint("Exportpath is %s" % EXPORTPATH)
	else:
		dest = DESTINATION.get(save_path, None)
		if dest:
			if not exists(dest):
				mkdir(dest, mode=0o777)
			if exists(EXPORTPATH):  # it could be a directory or a link
				if islink(EXPORTPATH):
					if dest != readlink(EXPORTPATH):  # no longer valid?
						remove(EXPORTPATH)
						symlink(dest, EXPORTPATH)
						cprint("old Link '%s' removed, new link '%s' for '%s' created" % (EXPORTPATH, EXPORTPATH, dest))
				else:  # it's a directory
					cleanepgexport()
					symlink(dest, EXPORTPATH)
					cprint("old directory '%s' removed, new link '%s' created" % (EXPORTPATH, EXPORTPATH))
			else:
				symlink(dest, EXPORTPATH)
				cprint("nothing to remove, new link '%s' created" % EXPORTPATH)
			cprint("Exportpath is %s" % dest)
		else:
			if islink(EXPORTPATH):
				remove(EXPORTPATH)
			else:
				cleanepgexport()
			cprint("Exportpath is none")


def readSkin(skin):
	skintext = ""
	skinfile = join(resolveFilename(SCOPE_PLUGINS, "Extensions/EPGExport"), "skin_%s.xml" % ("fHD" if getDesktop(0).size().width() > 1300 else "HD"))
	try:
		with open(skinfile, "r") as file:
			try:
				domskin = parse(file).getroot()
				for element in domskin:
					if element.tag == "screen" and element.attrib["name"] == skin:
						skintext = tostring(element).decode()
						break
			except Exception as error:
				print("[Skin] Error: Unable to parse skin data in '%s' - '%s'!" % (skinfile, error))
	except OSError as error:
		print("[Skin] Error: Unexpected error opening skin file '%s'! (%s)" % (skinfile, error))
	return skintext


class EPGExportAutoStartTimer:  # class for Autostart of EPG Export
	def __init__(self, session):
		self.session = session
		self.EPGExportTimer = eTimer()
		self.EPGExportTimer.callback.append(self.onEPGExportTimer)
		self.update()

	def getWakeTime(self):
		if int(config.plugins.epgexport.hours.value):
			clock = config.plugins.epgexport.wakeup.value
			nowt = time()
			now = localtime(nowt)
			return int(mktime((now.tm_year, now.tm_mon, now.tm_mday, clock[0], clock[1], 0, 0, now.tm_yday, now.tm_isdst)))
		else:
			cprint("automatic epg exporting is disabled")
			return -1

	def update(self, atLeast=0):
		self.EPGExportTimer.stop()
		wake = self.getWakeTime()
		now = int(time())
		if wake > 0:
			if wake < now + atLeast:
				wake += int(config.plugins.epgexport.hours.value) * 3600  # next in x hours
			tnext = wake - now
			self.EPGExportTimer.startLongTimer(tnext)
			cprint("WakeUpTime now set to %d seconds (now=%d)" % (tnext, now))
		else:
			wake = -1

	def onEPGExportTimer(self):
		self.EPGExportTimer.stop()
		now = int(time())
		cprint("onTimer occured at %d" % now)
		wake = self.getWakeTime()
		atLeast = 0
		if wake - now < 60:  # If we're close enough, we're okay...
			self.autoEPGExport()
			atLeast = 60
		self.update(atLeast)  # restart timer for next day...

	def autoEPGExport(self):
		cprint("automatic epg export starts")
		EPGExport(None, config.plugins.epgexport.compression.value, True, True)


def sessionstart(reason, **kwargs):
		if reason == 0 and "session" in kwargs:
			global AutoStartTimer  # Autostart of EPG Export
			session = kwargs.get("session", None)
			fixepgexport()
			if config.plugins.epgexport.webinterface.value:  # run plugin's own webinterface
				if config.plugins.epgexport.twisted.value:
					cprint("CUSTOM WEBIF TWISTED")
					deferToThread(startingCustomEPGExternal).addCallback(lambda ignore: finishedCustomEPGExternal())
				else:
					cprint("CUSTOM WEBIF THREAD")
					global WebTimer
					global WebTimer_conn
					WebTimer = eTimer()
					WebTimer_conn = WebTimer.timeout.connect(startingCustomEPGExternal)
					WebTimer.start(5000, True)
			else:
				cprint("NO Webinterface at all")
			cprint("AUTOSTART TIMER")
			AutoStartTimer = EPGExportAutoStartTimer(session)


def startingCustomEPGExternal():
	resourceSource = EPGExportSource()
	resourceLast = EPGExportLastUpdate()
	resourceChannels = EPGExportChannels()
	resourcePrograms = EPGExportPrograms()
	root = Resource()
	root.putChild(b"epgexport.sources.xml", resourceSource)
	root.putChild(b"LastUpdate.txt", resourceLast)
	root.putChild(b"epgexport.channels.xml", resourceChannels)
	root.putChild(b"epgexport.channels.xml.gz", resourceChannels)
	root.putChild(b"epgexport.channels.xml.xz", resourceChannels)
	root.putChild(b"epgexport.xml", resourcePrograms)
	root.putChild(b"epgexport.gz", resourcePrograms)
	root.putChild(b"epgexport.xz", resourcePrograms)
	root.putChild(b"picon", static.File("/picon"))
	factory = Site(root)
	port = int(config.plugins.epgexport.port.value)
	listenTCP(port, factory)
	try:
		run()
	except Exception as err:
		cprint(str(err))


def finishedCustomEPGExternal():
	cprint("Custom Webinterface Finished!!!")


def Plugins(**kwargs):
	return [
		PluginDescriptor(name="EPG Export", description=_("Export EPG as XML"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="epgexport.png", fnc=startEPGExport),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False)
		]


class EPGExportConfiguration(ConfigListScreen, Screen):
	def __init__(self, session):
		skin = readSkin("EPGExportConfiguration")
		self.skin = skin
		self.onChangedEntry = []  # explicit check on every entry
		Screen.__init__(self, session, skin)
		ConfigListScreen.__init__(self, [])
		self["config"].onSelectionChanged.append(self.selectionChanged)
		self["headline"] = StaticText()
		self["statustext"] = StaticText()
		self["logo"] = Pixmap()
		self["buttonred"] = StaticText(_("Exit"))
		self["buttongreen"] = StaticText(_("Save"))
		ftypes = {"xz": "xz", "gz": "gz", "none": "xml"}
		ftype = ftypes.get(config.plugins.epgexport.compression.value, "{Error}")
		self["buttonyellow"] = StaticText("%s (%s)" % (_("Downloading"), ftype))
		self["buttonblue"] = StaticText("%s %s" % (_("Select"), _("Bouquets")))
		self["actions"] = ActionMap(["ChannelSelectEPGActions", "InfobarTeletextActions", "SetupActions", "ColorActions"], {
			"exit": self.cancel,
			"cancel": self.cancel,
			"red": self.cancel,
			"green": self.save,
			"yellow": self.yellow_key,
			"blue": self.blue_key,
			"showEPGList": self.about,
			"startTeletext": self.getText
		})
		self.refreshLayout()
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self["headline"].setText(_("%s - ver. %s") % ("EPG Export", VERSION))
		self["logo"].instance.setPixmapFromFile("%s/epgexport.png" % resolveFilename(SCOPE_PLUGINS, "Extensions/EPGExport"))
		self.refreshLayout()

	def refreshLayout(self):
		clist = []
		clist.append(getConfigListEntry(_("Destination directory"), config.plugins.epgexport.epgexport))
		clist.append(getConfigListEntry(_("EPG Download (Days)"), config.plugins.epgexport.days))
		clist.append(getConfigListEntry(_("EPG Update (Hours)"), config.plugins.epgexport.reload))
		clist.append(getConfigListEntry(_("Keep outdated EPG (Days)"), config.plugins.epgexport.outdated))
		clist.append(getConfigListEntry(_("Recurring EPG Download"), config.plugins.epgexport.hours))
		if int(config.plugins.epgexport.hours.value):
			clist.append(getConfigListEntry(_("StartTime"), config.plugins.epgexport.wakeup))
		clist.append(getConfigListEntry(_("Compression"), config.plugins.epgexport.compression))
		clist.append(getConfigListEntry(_("Channel ID"), config.plugins.epgexport.channelid))
		clist.append(getConfigListEntry(_("OpenWebIf Picon Location (XML-Source)"), config.plugins.epgexport.server))
		if config.plugins.epgexport.server.value == "ip":
			clist.append(getConfigListEntry(_("Server IP Address"), config.plugins.epgexport.ip))
		if config.plugins.epgexport.server.value == "name":
			clist.append(getConfigListEntry(_("Server Name"), config.plugins.epgexport.hostname))
		clist.append(getConfigListEntry(_("Enable Plugin's own WebInterface (GUI restart required)"), config.plugins.epgexport.webinterface))
		if config.plugins.epgexport.webinterface.value:
			clist.append(getConfigListEntry(_("Server Port (4000-4999)"), config.plugins.epgexport.port))
			clist.append(getConfigListEntry(_("Enable 'twisted'-mode for WebInterface (recommended)"), config.plugins.epgexport.twisted))
			clist.append(("\n",))
			clist.append((_("HINT: >>> Test Plugin's own WebInterface with 'BoxIP:Port/LastUpdate.txt' <<<"),))
		self["config"].setList(clist)

	def save(self):
		epgexport_string = """<?xml version="1.0" encoding="latin-1"?>
								<sources><mappings>
									<channel name="epgexport.channels.xml.xz">
										<url>http://localhost/epgexport.channels.xml.xz</url>
									</channel>
									</mappings>
									<sourcecat sourcecatname="EPG Export XMLTV">
										<source type="gen_xmltv" nocheck="1" channels="epgexport.channels.xml.xz">
											<description>EPG Export Channels (xz) (c) gutemine 2019</description>
											<url>http://localhost/epgexport.xz</url>
										</source>
									</sourcecat>
								</sources>"""
		self["statustext"].setText("%s %s %s" % (_("Saving"), _("Configuration"), _("...")))
		if config.plugins.epgexport.channelid.value == "xml" and not exists(join(EXPORTPATH, "custom.channels.xml")):
			config.plugins.epgexport.channelid.value = "name"
		for x in self["config"].list:
			if len(x) > 1:
				x[1].save()
		if config.plugins.epgexport.server.value != "none":
			host = "%d.%d.%d.%d" % tuple(config.plugins.epgexport.ip.value) if config.plugins.epgexport.server.value == "ip" else config.plugins.epgexport.hostname.value
			if config.plugins.epgexport.compression.value == "xz":
				epg_string = epgexport_string.replace("localhost", host)
			elif config.plugins.epgexport.compression.value == "gz":
				epg_string = epgexport_string.replace("localhost", host).replace("xz", "gz")
			else:
				epg_string = epgexport_string.replace("localhost", host).replace(".xz", "").replace("(xz) ", "")
			if config.plugins.epgexport.webinterface.value:  # add port for plugin's own webinterface
				port = config.plugins.epgexport.port.value
				epg_string = epg_string.replace("/epgexport", ":%s/epgexport" % port)
			epgimport = join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgimport")
			if not exists(epgimport):
				mkdir(epgimport, mode=0o777)
			with open(join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgimport/epgexport.sources.xml"), "w+") as f:
				f.write(epg_string)
			epgload = join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgload")
			if not exists(epgload):
				mkdir(epgload, mode=0o777)
			with open(join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgload/epgexport.sources.xml"), "w+") as f:
				f.write(epg_string)
		else:
			file = join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgimport/epgexport.sources.xml")
			if exists(file):
				remove(file)
			file = join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgload/epgexport.sources.xml")
			if exists(file):
				remove(file)
		fixepgexport()
		self.close(True)

	def cancel(self):
		self["statustext"].setText("%s %s %s" % (_("Leaving"), _("Configuration"), _("...")))
		for x in self["config"].list:
			if len(x) > 1:
				x[1].cancel()
		self.close(False)

	def selectionChanged(self):
		choice = self["config"].getCurrent()
		current = choice[1]
		hostname = config.plugins.epgexport.hostname
		ip = config.plugins.epgexport.ip
		if current == ip:
			self["buttonyellow"].setText(_("Server IP"))
		elif current == hostname:
			self["buttonyellow"].setText(_("Hostname"))
		else:
			ftypes = {"xz": "xz", "gz": "gz", "none": "xml"}
			ftype = ftypes.get(config.plugins.epgexport.compression.value, "{Error}")
			self["buttonyellow"].setText("%s (%s)" % (_("Downloading"), ftype))

	def changedEntry(self):
		choice = self["config"].getCurrent()
		current = choice[1]
		hostname = config.plugins.epgexport.hostname
		if config.plugins.epgexport.channelid.value == "xml" and not exists(join(EXPORTPATH, "custom.channels.xml")):
			config.plugins.epgexport.channelid.value = "name"
		if choice is not None and current != hostname:
			self.refreshLayout()

	def yellow_key(self):
		choice = self["config"].getCurrent()
		current = choice[1]
		hostname = config.plugins.epgexport.hostname
		ip = config.plugins.epgexport.ip
		if current == ip:
			ip = self.getIP()
			lip = ip.split(".")
			localip = [int(lip[0]), int(lip[1]), int(lip[2]), int(lip[3])]  # make tuple by hand...
			config.plugins.epgexport.ip.value = localip
			self.refreshLayout()
		elif current == hostname:
			hostname = gethostname()
			fullname = getfqdn(hostname)
			config.plugins.epgexport.hostname.value = fullname
			self.refreshLayout()
		else:
			selected = 0
			for x in range(bouquet_length):
				if config.plugins.epgexport.bouquets[x].export.value:
					selected += 1
			if selected < 1:
				for x in range(bouquet_length):
					if config.plugins.epgexport.bouquets[x].name.value == "favorites":
						config.plugins.epgexport.bouquets[x].export.value = True
						config.plugins.epgexport.bouquets[x].export.save()
						cprint("nothing selected, means Favorites")
			fixepgexport()
			self["statustext"].setText("%s %s" % (_("EPG"), _("Downloading")))
			self.startingEPGExport()
			self.finishedEPGExport()

	def startingEPGExport(self):
		self["statustext"].setText("%s %s..." % (_("EPG"), _("Downloading")))
		EPGExport(self, config.plugins.epgexport.compression.value, True, True)

	def finishedEPGExport(self):
		loaded = ""
		for x in range(bouquet_length):
			if config.plugins.epgexport.bouquets[x].export.value:
				loaded += "%s\n" % config.plugins.epgexport.bouquets[x].name.value
		compression = config.plugins.epgexport.compression.value
		ctype = "(%s)" % compression if compression in ["xz", "gz"] else "(raw)"
		self.session.open(MessageBox, "%s %s %s:\n\n %s\n%s" % (_("EPG"), _("Downloading"), ctype, loaded.upper(), _("Execution finished!!")), MessageBox.TYPE_INFO, timeout=3)

	def about(self):
		self.session.open(MessageBox, _("%s plugin ver. %s\n\n(c) gutemine 2019\n\nSpecial Thanks to Rytec for the XMLTV Format !") % ("EPG Export", VERSION), MessageBox.TYPE_INFO)

	def getText(self):
		cprint("CLEANING EXPORT")
		cleanepgexport(True)
		self.session.open(MessageBox, "%s %s %s %s" % (_("EPG"), _("Download"), _("Cache"), _("Reset")), MessageBox.TYPE_INFO)

	def getIP(self):
		ip = None
		lip = "localhost"
		ifaces = iNetwork.getConfiguredAdapters()
		for iface in ifaces:
			ip = iNetwork.getAdapterAttribute(iface, "ip")
			if not ip or len(ip) != 4:
				continue
		if ip is not None:
			lip = '.'.join(str(x) for x in ip)
		cprint("local ip %s" % (lip))
		return lip

	def blue_key(self):
		self.session.open(EPGExportSelection)


class EPGExport(Screen):
	def __init__(self, main, compressed="xz", channels=True, programs=True):
		self.main = main
		self.compressed = compressed
		self.channels = channels
		self.programs = programs
		self.cur_event = None
		self.cur_service = None
		self.offs = 0
		self.epgcache = eEPGCache.getInstance()
		self.time_base = int(time()) - int(config.plugins.epgexport.outdated.value) * 60 * 24
		self.time_epoch = int(config.plugins.epgexport.days.value) * 60 * 24
		self.slist = None
		self.tree = None
		global SERVICELIST
		if SERVICELIST is None:
			InfoBarInstance = InfoBar.instance
			if InfoBarInstance is not None:
				SERVICELIST = InfoBarInstance.servicelist
		cprint("SERVICELIST: %s" % SERVICELIST)
		new = checkLastUpdate()
		if new:
			if config.plugins.epgexport.channelid.value == "xml":
				if exists(join(EXPORTPATH, "custom.channels.xml")):
					cprint("loading custom.channels.xml")
					if self.main is not None:
						self.main["statustext"].setText(_("Custom (xml %s %s...)") % (_("Channels"), _("Downloading")))
					epgtree = etree.parse(join(EXPORTPATH, "custom.channels.xml"))
					self.tree = epgtree.getroot()
				else:
					cprint("custom.channels.xml not found")
					if self.main is not None:
						self.main["statustext"].setText(_("Custom (%s)") % ("xml %s" % _("not found")))
					return
			cprint("extracting...")
			self.startingEPGExport()
		else:
			cprint("still valid...")
			if self.main is not None:
				self.main["statustext"].setText("%s %s %s %s" % (_("EPG"), _("Download"), _("Reload"), _("Finished")))

	def startingEPGExport(self):
		cprint("starting EPG export...")
		global SERVICELIST
		lang = config.osd.language.value
		sp = []
		sp = lang.split("_")
		self.language = sp[0].lower()
		if SERVICELIST:  # use current bouquet if none is found...
			bouquet = SERVICELIST.getRoot()
			if bouquet:
				serviceHandler = eServiceCenter.getInstance()
				info = serviceHandler.info(bouquet)
				bouquet_name = info.getName(bouquet)
				cprint("DEFAULT bouquet %s" % bouquet_name)
				all_bouquets = SERVICELIST.getBouquetList()
				self.services = []
				for bouquets in all_bouquets:
					bt = tuple(bouquets)
					bouquet_name = bt[0].replace(" (TV)", "").replace(" (Radio)", "").lower()
					cprint("CHECKS bouquet %s" % bouquet_name)
					for x in range(bouquet_length):
						if bouquet_name == config.plugins.epgexport.bouquets[x].name.value and config.plugins.epgexport.bouquets[x].export.value:
							bouquet = bouquets[1]
							cprint("FOUND bouquet %s" % bouquet_name)
							self.services += self.getBouquetServices(bouquet)
			if self.channels:
				self.exportChannels()
			if self.programs:
				cprint("extracting...")
				exportLastUpdate()
				self.extractEPG()
				self.exportEPG()

	def getBouquetServices(self, bouquet):
		services = []
		SERVICELIST = eServiceCenter.getInstance().list(bouquet)
		if SERVICELIST is not None:
			while True:
				service = SERVICELIST.getNext()
				if not service.valid():  # check if end of list
					break
				if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):  # ignore non playable services
					continue
				services.append(ServiceReference(service))
		return services

	def extractEPG(self):
		self.cur_event = None
		self.cur_service = None
		test = [(service.ref.toString(), 0, self.time_base, self.time_epoch) for service in self.services]
		test.insert(0, "XRnITBDSE")
#		test.insert(0, ("XRnITBDSE", 0, self.time_base, self.time_epoch))  # N = ServiceName, n = short ServiceName
		epg_data = self.queryEPG(test)
		self.program = []
		tmp_list = []
		service = None
		for x in epg_data:
			if service is None or service.ref != ServiceReference(x[0]).ref:
				if tmp_list:
					self.program.append((service, tmp_list[0][0] is not None and tmp_list or None))
				try:  # Dont use the service return from the EPG query because it wont have a number so search it from the services list that we used to build the query
					service = next(s for s in self.services if s.ref == ServiceReference(x[0]).ref)
					cprint("extractEPG found: %s" % service)
				except Exception as e:
					cprint("extractEPG exception: %s" % e)
				tmp_list = []
			if len(x) > 7:
				tmp_list.append((x[2], x[3], x[4], x[5], x[6], x[7]))
		if tmp_list and len(tmp_list):
			self.program.append((service, tmp_list[0][0] is not None and tmp_list or None))

	def queryEPG(self, list, buildFunc=None):
		if self.epgcache is not None:
			if buildFunc is not None:
				return self.epgcache.lookupEvent(list, buildFunc)
			else:
				return self.epgcache.lookupEvent(list)
		return []

	def exportChannels(self):
		xmltv_string = self.generateChannels()
		xml_file_name = "%s.%s" % (CHANNELS, "xml")
		if self.compressed == "xz":
			with lzmaopen("%s.xz" % xml_file_name, "wb") as f:
				f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
				f.write(xmltv_string)
		elif self.compressed == "gz":
			with gzipopen("%s.gz" % xml_file_name, "wb") as f:
				f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
				f.write(xmltv_string)
		else:
			with open(xml_file_name, "wb") as f:
				f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
				f.write(xmltv_string)

	def exportEPG(self):
		xmltv_string = self.generateEPG()
		xml_file_name = join(EXPORTPATH, "epgexport.xml")
		if self.compressed == "xz":
			with lzmaopen("%s.xz" % xml_file_name, "wb") as f:
				f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
				f.write(xmltv_string)
		elif self.compressed == "gz":
			with gzipopen("%s.gz" % xml_file_name, "wb") as f:
				f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
				f.write(xmltv_string)
		else:
			with open(xml_file_name, "wb") as f:
				f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
				f.write(xmltv_string)

	def indent(self, elem, level=0):
		i = "\n%s" % ("  " * level)
		if len(elem):
			if not elem.text or not elem.text.strip():
				elem.text = "%s  " % i
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
			for elem in elem:
				self.indent(elem, level + 1)
			if not elem.tail or not elem.tail.strip():
				elem.tail = i
		else:
			if level and (not elem.tail or not elem.tail.strip()):
				elem.tail = i

	def channelNumber(self, service):
		if hasattr(service, "ref") and service.ref and "0:0:0:0:0:0:0:0:0" not in service.ref.toString():
			numservice = service.ref
			num = numservice and numservice.getChannelNum() or None
			if num is not None:
				return num
		return None

	def channelID(self, service):
		service_name = service.getServiceName().encode("ascii", "ignore")
		service_id = service_name.decode().replace(" ", "").replace("(", "").replace(")", "").replace("-", "").replace(".", "").replace("+", "").replace("_", "").replace("/", "").replace("Â", "").replace("�", "")
		service_id = self.b2s(service_id)
		service_ref = service.ref.toString()
		service_num = self.channelNumber(service)
		if self.tree is not None:  # fallback is nameslang
			channel_id = "%s.%s" % (service_id, self.language)
			for child in self.tree:
				if child.text == service_ref and len(child.attrib["id"]) > 0:  # first find will win because good custom file has only one find
					channel_id = child.attrib["id"]
					break
		elif config.plugins.epgexport.channelid.value == "names":
			channel_id = service_id
		elif config.plugins.epgexport.channelid.value == "nameslang":
			channel_id = "%s.%s" % (service_id, self.language)
		elif config.plugins.epgexport.channelid.value == "nameslow":
			channel_id = service_id.lower()
		elif config.plugins.epgexport.channelid.value == "nameslowlang":
			channel_id = "%s.%s" % (service_id.lower(), self.language)
		elif config.plugins.epgexport.channelid.value == "number" and service_num:
			channel_id = str(service_num)
		else:  # default = channel name
			channel_id = service_name
		return self.b2s(channel_id)

	def piconURL(self, service):
		picon_url = None
		if config.plugins.epgexport.server.value != "none":
			picon_file = getPiconName(service)
			if picon_file:
				host = "%d.%d.%d.%d" % tuple(config.plugins.epgexport.ip.value) if config.plugins.epgexport.server.value == "ip" else config.plugins.epgexport.hostname.value
				picon_url = "http://%s/picon/%s" % (host, basename(picon_file))
		return picon_url

	def generateChannels(self):
		cprint("Building XMLTV channel list file")
		sp = []
		root = etree.Element('channels')
		for service in self.services:  # write all channel id's and service references at beginning of file
			service_name = service.getServiceName().replace('Â', '').replace('�', '')
			service_ref = service.ref.toString()
			sp = service_ref.split("::")
			service_ref = sp[0]
			if len(service_name) > 0 and service_ref.find("//") == -1 and service_ref.find("BOUQUET") == -1:
				service_id = self.channelID(service)
				xmltv_channel = etree.SubElement(root, "channel")
				xmltv_channel.set('id', service_id)
				xmltv_channel.text = service_ref
		self.indent(root)  # etree.tostring has no pretty print to make indent in xml
		cprint("Building XMLTV channel list file, completed")
		return etree.tostring(root, encoding='utf-8')

	def getTimezoneOffset(self):
		ts = time()  # utc time
		tl = localtime()  # local time == (utc time + utc offset)
#       td = timedelta(minutes=int(tl.tm_isdst)*60) # summertime is not needed...
#       cprint("summer time delta %s" % td)
#       offset = datetime.fromtimestamp(ts) - datetime.utcfromtimestamp(ts) - td
		offset = datetime.fromtimestamp(ts, tz=timezone.utc) - datetime.fromtimestamp(ts, tz=timezone.utc)
		delta = str(offset).rstrip("0").replace(":", "")  # make nice string form XMLTV local time offset...
		if abs(int(delta)) < 1000:
			local_offset = '+0%s' % delta if int(delta) > 0 else '-0%s' % delta
		else:
			local_offset = '+%s' % delta if int(delta) > 0 else '-%s' % delta
		cprint("local offset: %s" % local_offset)
		return local_offset

	def generateEPG(self):
		cprint("Building XMLTV electronic program guide file")
		root = etree.Element('tv')
		generator_info_name = 'EPG Export Plugin (c) gutemine 2019'
		generator_info_url = 'https://sourceforge.net/projects/gutemine/'
		root.set('generator-info-name', generator_info_name)
		root.set('generator-info-url', generator_info_url)
		cn = 0
		for service in self.services:
			service_name = service.getServiceName().replace('Â', '').replace('�', '')
			service_ref = service.ref.toString()
			if len(service_name) > 0 and service_ref.find("//") == -1:
				service_id = self.channelID(service)
				xmltv_channel = etree.SubElement(root, 'channel')
				xmltv_channel.set('id', service_id)
				xmltv_cname = etree.SubElement(xmltv_channel, 'display-name', lang=self.language)
				xmltv_cname.text = service_name
				service_picon = self.piconURL(service_ref)
				if service_picon:
					xmltv_cicon = etree.SubElement(xmltv_channel, 'icon')
					xmltv_cicon.set('src', service_picon)
				cn += 1
		cprint("channel number: %d" % cn)
		local_time_offset = self.getTimezoneOffset()
		en = 0
		for program in self.program:
			if program[1] is not None:
				service = program[0]
				service_name = service.getServiceName().replace('Â', '').replace('�', '')
				service_ref = service.ref.toString()
				if len(service_name) > 0 and service_ref.find("//") == -1:
					service_id = self.channelID(service)
					for event in program[1]:
						prog = dict()
						title = self.b2s(event[1]).strip()
						start = int(event[2])
						duration = int(event[3])
						subtitletext = self.b2s(event[4]).strip()
						description = self.b2s(event[5]).strip()
						stop = start + duration
						start_time = strftime('%Y%m%d%H%M00', localtime(start))
						stop_time = strftime('%Y%m%d%H%M00', localtime(stop))
						xmltv_program = etree.SubElement(root, 'programme')
						xmltv_program.set('start', "%s %s" % (start_time, local_time_offset))
						xmltv_program.set('stop', "%s %s" % (stop_time, local_time_offset))
						xmltv_program.set('channel', service_id)
						en += 1
						if title is not None:
							title_text = self.b2s(title).split('. ')
							title = etree.SubElement(xmltv_program, 'title', lang=self.language)
							title.text = self.b2s(title_text[0]).strip()
							if len(subtitletext) > 1:
								subtitle = etree.SubElement(xmltv_program, 'sub-title', lang=self.language)
								subtitle.text = self.b2s(subtitletext)
							else:
								if len(title_text) > 1:
									subtitle = etree.SubElement(xmltv_program, 'sub-title', lang=self.language)
									subtitle.text = self.b2s(title_text[1]).strip()
						if description is not None and len(description) > 1:
							desc = etree.SubElement(xmltv_program, 'desc', lang=self.language)
							desc.text = self.b2s(description)
		cprint("event number: %d" % en)
		self.indent(root)
		if self.main is not None:  # etree.tostring has no pretty print to make indent in xml
			self.main["statustext"].setText("%s %s %s: %d %s %s %s: %d" % (_("EPG"), _("Download"), _("Channels"), cn, _("EPG"), _("Info"), _("Details"), en))
		return etree.tostring(root, encoding='utf-8')

	def b2s(self, s):  # converting data type 'bytes' to 'string'
		return s.decode('utf-8') if isinstance(s, bytes) else s


class EPGExportSource(Resource):
	def render_GET(self, req):
		cprint("SOURCE REQUEST...")
		if exists(join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgload/epgexport.sources.xml")):
			with open(join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgload/epgexport.sources.xml"), "r") as f:
				sources = f.read()
		elif exists(join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgimport/epgexport.sources.xml")):
			with open(join(resolveFilename(SCOPE_SYSETC, "epgexport"), "epgimport/epgexport.sources.xml"), "r") as f:
				sources = f.read()
		else:
			sources = ""
		cprint("sources: %s" % sources)
		req.setResponseCode(http.OK)
		req.setHeader("Content-type", "text/html")
		req.setHeader("charset", "UTF-8")
		return sources.encode()


class EPGExportLastUpdate(Resource):
	def render_GET(self, req):  # always return current date for a web request
		cprint("last update request...")
		now = datetime.now()
		date = now.strftime('%Y-%m-%d')
		cprint("last update: %s" % date)
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')
		return date.encode()


class EPGExportChannels(Resource):
	def render_GET(self, req):
		cprint("CHANNELS REQUEST: %s" % req.uri)
		new = checkLastUpdate()
		if req.uri.find(b"epgexport.channels.xml.xz") != -1:
			if new or not exists("%s.%s" % (CHANNELS, "xml.xz")):  # web request for xz file
				cprint("EXPORTING CHANNELS xz")
				EPGExport(None, "xz", True, False)
			with open("%s.%s" % (CHANNELS, "xml.xz"), "rb") as f:
				channels = f.read()
		elif req.uri.find(b"epgexport.channels.xml.gz") != -1:
			if new or not exists("%s.%s" % (CHANNELS, "xml.gz")):  # web request for gz file
				cprint("EXPORTING CHANNELS gz")
				EPGExport(None, "gz", True, False)
			with open("%s.%s" % (CHANNELS, "xml.gz"), "rb") as f:
				channels = f.read()
		else:
			if new or not exists("%s.%s" % (CHANNELS, "xml")):  # web request for uncompressed file
				cprint("EXPORTING CHANNELS")
				EPGExport(None, "none", True, False)
			with open("%s.%s" % (CHANNELS, "xml"), "rb") as f:
				channels = f.read()
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')
		return channels


class EPGExportPrograms(Resource):
	def render_GET(self, req):
		cprint("PROGRAMS REQUEST: %s" % req.uri)
		new = checkLastUpdate()
		if req.uri.find(b"epgexport.xz") != -1:
			if new or not exists(join(EXPORTPATH, "epgexport.xml.xz")):  # web request for xz file
				cprint("EXPORTING PROGRAMS xz")
				EPGExport(None, "xz", False, True)
			with open(join(EXPORTPATH, "epgexport.xml.xz"), "rb") as f:
				programs = f.read()
		elif req.uri.find(b"epgexport.gz") != -1:
			if new or not exists(join(EXPORTPATH, "epgexport.xml.gz")):  # web request for gz file
				cprint("EXPORTING PROGRAMS gz")
				EPGExport(None, "gz", False, True)
			with open(join(EXPORTPATH, "epgexport.xml.gz"), "rb") as f:
				programs = f.read()
		else:
			if new or not exists(join(EXPORTPATH, "epgexport.xml")):  # web request for uncompressed file
				cprint("EXPORTING PROGRAMS")
				EPGExport(None, "none", False, True)
			with open(join(EXPORTPATH, "epgexport.xml"), "rb") as f:
				programs = f.read()
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')
		return programs


class EPGExportSelection(ConfigListScreen, Screen):
	def __init__(self, session):
		self.session = session
		skin = readSkin("EPGExportSelection")
		self.skin = skin
		Screen.__init__(self, session, skin)
		self.onChangedEntry = []  # explicit check on every entry
		ConfigListScreen.__init__(self, [])
		self["headline"] = StaticText()
		self["logo"] = Pixmap()
		self["buttonred"] = StaticText(_("Exit"))
		self["buttongreen"] = StaticText(_("Save"))
		self["buttonyellow"] = StaticText(_("Reset"))
		self["buttonblue"] = StaticText(_("About"))
		self["actions"] = ActionMap(["SetupActions",
									"ColorActions"], {"ok": self.save,
													"exit": self.cancel,
													"cancel": self.cancel,
													"red": self.cancel,
													"green": self.save,
													"yellow": self.resetting,
													"blue": self.about})
		selected = 0
		for x in range(bouquet_length):
			if config.plugins.epgexport.bouquets[x].export.value:
				selected += 1
		if selected < 1:
			self.resetting()
		self.createSetup()
		self.onLayoutFinish.append(self.onLayoutFinished)
#		self.onShown.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		self["headline"].setText("%s %s" % (_("EPG Selection"), _("Bouquet")))
		self["logo"].instance.setPixmapFromFile("%s/epgexport.png" % resolveFilename(SCOPE_PLUGINS, "Extensions/EPGExport"))

	def save(self):
		selected = 0
		for x in range(bouquet_length):
			if config.plugins.epgexport.bouquets[x].export.value:
				selected += 1
		if selected < 1:
			self.resetting()
		for x in range(bouquet_length):
			config.plugins.epgexport.bouquets[x].export.save()
			config.plugins.epgexport.bouquets[x].name.save()
		self.close(True)

	def cancel(self):
		for x in range(bouquet_length):
			config.plugins.epgexport.bouquets[x].export.cancel()
			config.plugins.epgexport.bouquets[x].name.cancel()
		self.close(False)

	def createSetup(self):
		clist = []
		for x in range(bouquet_length):
			clist.append(getConfigListEntry(bouquet_options[x][1], config.plugins.epgexport.bouquets[x].export))
		self["config"].setList(clist)

	def changedEntry(self):
		choice = self["config"].getCurrent()
		current = choice[1]
		if choice is not None:
			self.createSetup()

	def resetting(self):
		for x in range(bouquet_length):
			config.plugins.epgexport.bouquets[x].export.value = False
			if config.plugins.epgexport.bouquets[x].name.value == "favorites":
				config.plugins.epgexport.bouquets[x].export.value = True
				cprint("nothing selected, means Favorites")
			config.plugins.epgexport.bouquets[x].export.save()
			config.plugins.epgexport.bouquets[x].name.save()
		self.createSetup()

	def about(self):
			self.session.open(MessageBox, _("%s plugin ver. %s\n\n(c) gutemine 2019\n\nSpecial Thanks to Rytec for the XMLTV Format !") % ("EPG Export", VERSION), MessageBox.TYPE_INFO)
