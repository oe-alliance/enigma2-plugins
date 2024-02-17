# -*- coding: UTF-8 -*-
import json
import re
import xml.etree.ElementTree as Et
from datetime import datetime, timedelta
from os import mkdir, path, unlink
import requests
from skin import AttributeParser
from Components.ActionMap import ActionMap
from Components.config import ConfigDirectory, ConfigSelection, ConfigSubsection, ConfigYesNo, config, configfile
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from enigma import addFont, eConsoleAppContainer, ePicLoad, eServiceReference, getDesktop, gPixmapPtr
from Screens import InfoBarGenerics
from Screens.ChoiceBox import ChoiceBox
from Screens.Console import Console
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from six import ensure_str

try:
	from twisted.internet.reactor import callInThread
except ImportError:
	import threading

	def callInThread(func, *args, **kwargs):
		thread = threading.Thread(target=func, args=args, kwargs=kwargs)
		thread.start()


config.plugins.MVW = ConfigSubsection()
config.plugins.MVW.savetopath = ConfigDirectory(default="/media/hdd/movie/")
config.plugins.MVW.SaveResumePoint = ConfigYesNo(default=False)
config.plugins.MVW.UT_DL = ConfigYesNo(default=False)
config.plugins.MVW.COVER_DL = ConfigYesNo(default=False)
config.plugins.MVW.DESC = ConfigYesNo(default=False)
config.plugins.MVW.AUTOPLAY = ConfigYesNo(default=False)
config.plugins.MVW.FUTURE = ConfigYesNo(default=False)
config.plugins.MVW.INTSKIN = ConfigYesNo(default=False)

PLUGINPATH = "/usr/lib/enigma2/python/Plugins/Extensions/Mediathekviewweb/"
FHD = getDesktop(0).size().height() > 720
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
TMPIC = "/tmp/cover/bild.jpg"
SKINFILE = PLUGINPATH + "skin_FHD.xml" if FHD else PLUGINPATH + "skin_HD.xml"
FONT = "/usr/share/fonts/LiberationSans-Regular.ttf"
if not path.exists(FONT):
	FONT = "/usr/share/fonts/nmsbd.ttf"
addFont(FONT, "SRegular", 100, False)
ColorList = [("glass,#40000000,#5a000000,#37cccccc", "Black Glass"), ("glass,#5a082567,#5a000000,#37cccccc", "SapphireBlue Glass"), ("glass,#5a080828,#5a000000,#37cccccc", "MagentaBlue Glass"), ("glass,#e615d7b6,#5a000000,#37cccccc", "PaleGreen Glass"), ("glass,#5aa0785a,#5a000000,#37cccccc", "Chamoisee Glass"), ("transparent,#050a1232,#1502050e,#05192d7c", "DarkBlue Transparent"), ("transparent,#05000000,#15000000,#606060", "BlackGrey Transparent"), ("transparent,#05000000,#15000000,#ffff00", "BlackYellow Transparent"), ("transparent,#1a104485,#3D104485,#1aC0C0C0", "BrightBlue Transparent"), ("transparent,#1a746962,#1502050e,#1a746962", "BrownBlue Transparent"), ("MiniTV,#104485,#0c366a,#C0C0C0", "BrightBlue MiniTV"), ("MiniTV,#0a1232,#02050e,#192d7c", "DarkBlue MiniTV"), ("MiniTV,#000000,#080808,#606060", "BlackGrey MiniTV"), ("MiniTV,#000000,#080808,#ffff00", "BlackYellow MiniTV"), ("MiniTV,#746962,#02050e,#746962", "BrownBlue MiniTV")]
config.plugins.MVW.SkinColor = ConfigSelection(default="glass,#40000000,#5a000000,#37cccccc", choices=ColorList)


def readskin(eskin=None):
	cf = config.plugins.MVW.SkinColor.value.split(",")
	sn = eskin if eskin else cf[0]
	s = ""
	try:
		with open(SKINFILE, "r") as f:
			root = Et.parse(f).getroot()
		for element in root:
			if element.tag == "screen" and element.attrib["name"] == sn:
				s = ensure_str(Et.tostring(element))
		if hasattr(AttributeParser, "scrollbarForegroundColor"):
			s = s.replace("scrollbarSliderForegroundColor", "scrollbarForegroundColor")
	except (OSError, IOError, Et.ParseError):
		return ""
	return s.strip().replace("{col1}", cf[1]).replace("{col2}", cf[2]).replace("{col3}", cf[3]).replace("{picpath}", PLUGINPATH + "img/")


def vttxmltosrt(data):
	def convert_time(time):
		time = float(time[:-1])
		h = int(time / 3600)
		m = int((time % 3600) / 60)
		s = int(time % 60)
		ms = int((time % 1) * 1000)
		return "{:02d}:{:02d}:{:02d},{:03d}".format(h, m, s, ms)

	if "WEBVTT" in data:
		data = re.sub(re.compile("<.*?>| align:middle"), "", data)
	elif "<?xml version" in data:
		data = Et.fromstring(data)
		elm = data.find("{http://www.w3.org/ns/ttml}body").find("{http://www.w3.org/ns/ttml}div")
		if elm is not None:
			count = 0
			tt = "WEBVTT\n\n"

			for el in elm:
				b = el.attrib.get("begin", "")
				if "s" in b and "." in b:
					b = convert_time(b)
				e = el.attrib.get("end", "")
				if "s" in e and "." in e:
					e = convert_time(e)
				span = el.findall("{http://www.w3.org/ns/ttml}span")
				if span:
					for span in span:
						txt = span.text
				else:
					txt = el.text
				if txt and b and e:
					txt = txt.replace("<br/>", "")
					count += 1
					tt += str(count) + "\n"
					tt += str(b.replace(".", ",") + " --> " + e.replace(".", ",")) + "\n"
					tt += (txt) + "\n\n"
			return ensure_str(tt)
	return ensure_str(data)


def geturl(url, headers=None, data=None, timeout=10, verify=True):
	try:
		if not headers:
			headers = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", "Accept-Language": "de,en-US;q=0.7,en;q=0.3", "Accept-Encoding": "gzip, deflate"}
		r = requests.post(url, headers=headers, data=data, timeout=timeout, verify=verify) if data else requests.get(url, headers=headers, timeout=timeout, verify=verify)
	except requests.RequestException:
		return ""
	return r.content


class Mediathekviewweb(Screen):
	def __init__(self, session):
		s = readskin()
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "ChannelSelectBaseActions", "MenuActions"], {"menu": self.MVWSetup, "green": self.mvw_cdn, "red": self.close, "blue": self.HauptMenu, "up": self.up, "down": self.down, "left": self.left, "right": self.right, "nextBouquet": self.p_up, "prevBouquet": self.p_down, "ok": self.ok, "cancel": self.back}, -1)
		self["movielist"] = List()
		self["cover"] = Pixmap()
		self.skin = s
		self.skinName = "Mediathekviewweb_org" if config.plugins.MVW.INTSKIN.value else "Mediathekviewweb"
		self["handlung"] = ScrollLabel()
		self.HISTORY = [("MENU", "", "")]
		self["DownloadLabel"] = ScrollLabel()
		self["PluginName"] = ScrollLabel("MediathekViewWeb v1.1")
		self["progress"] = ProgressBar()
		self["progress"].hide()
		self.dl_file = None
		self.totalDuration = 0
		if not path.exists("/tmp/cover/"):
			mkdir("/tmp/cover/")
		self.onLayoutFinish.append(self.HauptMenu)

	def reload_skin(self):
		self.session.open(Mediathekviewweb)
		self.close()

	def MVWSetup(self):
		self.session.openWithCallback(self.reload_skin, ConfigScreen)

	def mvw_api(self, query="", channel="", page=1, size=100, index="0"):
		liste = []
		offset = size * (page - 1)
		data = {"sortBy": "timestamp", "sortOrder": "desc", "future": config.plugins.MVW.FUTURE.value, "offset": offset, "size": size}
		if query or channel:
			data["queries"] = []
		if query:
			data["queries"].append({"fields": ["title", "topic"], "query": query})
		if channel:
			data["queries"].append({"fields": ["channel"], "query": channel})
		headers = {"User-Agent": UA, "content-type": "text/plain"}
		data = geturl("https://mediathekviewweb.de/api/query", headers=headers, data=json.dumps(data))
		if data and 'result":null' not in str(data):
			data = json.loads(data)
			data = data.get("result", {})
			totalResults = data.get("queryInfo", {}).get("totalResults", "")
			for js in data.get("results", {}):
				if not js.get("title"):
					continue
				duration = str(timedelta(seconds=int(js.get("duration")))) if str(js.get("duration")).isdigit() else ""
				timestamp = datetime.fromtimestamp(int(js.get("timestamp"))).strftime("%d-%m-%Y %H:%M:%S") if str(js.get("timestamp")).isdigit() else ""
				sub = js.get("url_subtitle", "")
				urls = []
				if js.get("url_video_hd"):
					urls.append(("Hoch", js.get("url_video_hd") + "##" + sub))
				if js.get("url_video"):
					urls.append(("Mittel", js.get("url_video") + "##" + sub))
				if js.get("url_video_low"):
					urls.append(("Niedrig", js.get("url_video_low") + "##" + sub))
				img = js.get("url_website", "")
				liste.append(("MVW_PLAY", ensure_str("[%s] %s - %s" % (js.get("channel", ""), js.get("topic", ""), js.get("title", ""))), urls, ensure_str("%s%s\n%s" % ("UT\n" if sub else "", timestamp, js.get("description", ""))), img, duration, ""))
			if totalResults > (page * size):
				liste.append(("MVW_API", "Nextpage", (ensure_str(query), ensure_str(channel), (page + 1), size), "", PLUGINPATH + "/img/" + "nextpage.png", "", ""))
		if liste:
			self["movielist"].setList(liste)
			self["movielist"].setIndex(int(index))
			self.infos()
		else:
			self.HISTORY.pop()
			self.session.open(MessageBox, "Kein Eintrag vorhanden", MessageBox.TYPE_INFO, timeout=5)

	def HauptMenu(self, index="0"):
		menu = [("MVW_SUCHE", "Überall Suchen", ("", "", 1, 100, False), "", PLUGINPATH + "/img/" + "suche.png", "", ""), ("MVW_API", "Überall Stöbern", ("", "", 1, 100, False), "", PLUGINPATH + "img/" + "home.png", "", ""), ("MVW_SENDER_SUCHE", "Sender Suche", ("", "", 1, 100, False), "", PLUGINPATH + "/img/" + "suche.png", "", ""), ("MVW_SENDER", "Sender Stöbern", ("", "", 1, 100, False), "", PLUGINPATH + "/img/" + "sender.png", "", "")]
		self["movielist"].setList(menu)
		self["movielist"].setIndex(int(index))
		self.infos()

	def Sender(self, index="0", action="MVW_CHANNEL"):
		URL = "https://api.ardmediathek.de/image-service/images/urn:ard:image:"
		sender = [(action, "ARD", "", "", URL + "cddcfbc2887edfac?ch=bb94ade5984b3b54&w=360", "", ""), (action, "ZDF", "", "", "https://www.zdf.de/static/0.104.2262/img/appicons/zdf-152.png", "", ""), (action, "ZDF-tivi", "", "", "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/ZDFtivi_logo.svg/320px-ZDFtivi_logo.svg.png", "", ""), (action, "ARTE.DE", "", "", URL + "f9195b8bcbeaecc9?ch=fa42703f1b4c20bc&w=360", "", ""), (action, "SWR", "", "", URL + "aa24d7b7a46ac51c?ch=d6485202286d7033&w=360", "", ""), (action, "NDR", "", "", URL + "8d587d540cd01169?w=360", "", ""), (action, "3Sat", "", "", URL + "bdced2e15aab3c69?w=360&ch=b92f2ae35c4a1309", "", ""), (action, "KiKA", "", "", URL + "34a231a870f22c6d?w=360&ch=865612894cbd4d56", "", ""), (action, "BR", "", "", URL + "e73b862eee3232c4?ch=7560abc4cc794ac5&w=360", "", ""), (action, "SR", "", "", URL + "ff434ca6a62db52e?ch=542282531695b516&w=360", "", ""), (action, "Radio Bremen TV", "", "", URL + "7b4c72c6e85a6620?ch=468f72b78a0ed537&w=360", "", ""), (action, "DW", "", "", URL + "8d853ccf548a874f?ch=a285b4113c76fea4&w=360", "", ""), (action, "HR", "", "", URL + "10f8968f47d2528e?w=360&ch=393ec00d9f489f74", "", ""), (action, "MDR", "", "", URL + "68c2d007353ffcea?ch=dfd3a69469855178&w=360", "", ""), (action, "WDR", "", "", URL + "7a4016b5348d0a80?ch=a04121766f1f3d82&w=360", "", ""), (action, "Funk.net", "", "", "https://www.funk.net/img/favicons/favicon-192x192.png", "", ""), (action, "RBB", "", "", URL + "0ed44c2fbb444e41?ch=a7ba657f549573d2&w=360", "", ""), (action, "PHOENIX", "", "", URL + "0740d8e76701b87c?ch=ac815bf512ad7d9b&w=360", "", ""), (action, "RBTV", "", "", "https://upload.wikimedia.org/wikipedia/commons/8/86/Rocket_Beans_RBTV_Logo.png", "", ""), (action, "ORF", "", "", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/ORF_logo.svg/320px-ORF_logo.svg.png", "", ""), (action, "SRF", "", "", "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/Schweizer_Radio_und_Fernsehen_Logo.svg/320px-Schweizer_Radio_und_Fernsehen_Logo.svg.png", "", ""), (action, "ARTE.FR", "", "", URL + "f9195b8bcbeaecc9?ch=fa42703f1b4c20bc&w=360", "", ""), (action, "ARTE.EN", "", "", URL + "f9195b8bcbeaecc9?ch=fa42703f1b4c20bc&w=360", "", ""), (action, "ARTE.ES", "", "", URL + "f9195b8bcbeaecc9?ch=fa42703f1b4c20bc&w=360", "", ""), (action, "ARTE.PL", "", "", URL + "f9195b8bcbeaecc9?ch=fa42703f1b4c20bc&w=360", "", ""), (action, "ARTE.IT", "", "", URL + "f9195b8bcbeaecc9?ch=fa42703f1b4c20bc&w=360", "", "")]
		self["movielist"].setList(sender)
		self["movielist"].setIndex(int(index))
		self.infos()

	def mvw_Suche(self, text, sender=""):
		if text:
			if self["movielist"].getCurrent()[0] == "MVW_CHANNEL_SEARCH":
				sender = self["movielist"].getCurrent()[1]
			self.HISTORY.append(("MVW_API", (text, sender, 1, 100, False), self["movielist"].getIndex()))
			self.mvw_api(query=text, channel=sender)

	def ok(self):
		current_item = self["movielist"].getCurrent()
		action = current_item[0]
		url = current_item[2]
		index = self["movielist"].getIndex()
		if action in ("MVW_SUCHE", "MVW_CHANNEL_SEARCH"):
			self.session.openWithCallback(self.mvw_Suche, VirtualKeyBoard, title="Mediathek Suche")
		elif action == "MVW_PLAY":
			self.mvw_cdn(True)
		else:
			if action == "MVW_API":
				self.mvw_api(url[0], url[1], url[2], url[3])
			elif action == "MVW_SENDER_SUCHE":
				self.Sender(action="MVW_CHANNEL_SEARCH")
			elif action == "MVW_SENDER":
				self.Sender()
			elif action == "MVW_CHANNEL":
				self.mvw_api("", current_item[1])
			self.HISTORY.append((action, url, index))

	def back(self):
		if len(self.HISTORY) > 1:
			index = self.HISTORY[-1][2]
			self.HISTORY.pop()
			action, url = self.HISTORY[-1][:2]
			if action == "MVW_API":
				self.mvw_api(url[0], url[1], url[2], url[3], index)
			elif action == "MVW_SENDER_SUCHE":
				self.Sender(index, "MVW_CHANNEL_SEARCH")
			elif action == "MVW_SENDER":
				self.Sender(index)
			elif action == "MVW_CHANNEL":
				self.mvw_api(url)
			elif action == "MENU":
				self.HauptMenu(index)
		else:
			self.close()

	def mvw_image(self, url, play=True):
		if url:
			data = ensure_str(geturl(url))
			url = re.findall(r'src":"([^"]+)', data, re.DOTALL)
			if not url:
				url = re.findall(r'image" content="([^"]+)', data, re.DOTALL)
			if url:
				url = url[0]
				url = url.replace("{width}", "360" if play else "1080")
				if "kika.de" in url or "arte.tv" in url:
					url = url.split("?")[0]
					if "arte.tv" in url:
						url = url + ".jpg"
				if play:
					return callInThread(self.getimage, url, self["movielist"].getIndex())
				return url
		return ""

	def ffmpegsetup(self, answer):
		if answer:
			self.session.open(Console, cmdlist=["opkg update && opkg install ffmpeg"])

	def mvw_cdn(self, play=False):
		if self.dl_file:
			self.session.openWithCallback(self.dl_Stop, MessageBox, "möchten Sie den Download abbrechen?", default=True, type=MessageBox.TYPE_YESNO)
			return
		if isinstance(self["movielist"].getCurrent()[2], list):
			url = self["movielist"].getCurrent()[2]
			if play:
				if config.plugins.MVW.AUTOPLAY.value and url:
					self.Play(url[0])
				else:
					self.session.openWithCallback(self.Play, Choicebox, title="Wiedergabe starten?", list=url)
			else:
				if not path.exists("/usr/bin/ffmpeg"):
					self.session.openWithCallback(self.ffmpegsetup, MessageBox, "Zum Download benötigen Sie ffmpeg installieren?")
					return
				self.session.openWithCallback(self.dl_start, Choicebox, title="Download starten?", list=url)

	def fileClean(self):
		filename = self.dl_file.rsplit(".", 1)[0]
		for ext in [".srt", ".jpg", ".txt"]:
			fileext = filename + ext
			if path.exists(fileext):
				unlink(fileext)
		self.dl_file = None

	def dl_Stop(self, answer):
		if answer:
			self.console.sendCtrlC()
			if path.exists(self.dl_file):
				unlink(self.dl_file)
			self.fileClean()
			self.dl_file = None
			self.totalDuration = 0
			self["progress"].hide()

	def dl_start(self, answer):
		if answer:
			url = answer[1].split("##")
			filename = "".join(i for i in ensure_str(self["movielist"].getCurrent()[1]) if i not in r'\/":*?<>|')
			self.dl_file = str(config.plugins.MVW.savetopath.value) + "/" + str(filename) + ".mp4"
			if path.exists(self.dl_file):
				n = self.dl_file
				root, ext = path.splitext(self.dl_file)
				i = 0
				while path.exists(n):
					i += 1
					n = "%s_(%i)%s" % (root, i, ext)
				self.dl_file = n
			if config.plugins.MVW.COVER_DL.value:
				img = self.mvw_image(self["movielist"].getCurrent()[4], False)
				if img:
					img = geturl(img)
					if img:
						with open(self.dl_file[:-3] + "jpg", "wb") as f:
							f.write(img)
			if config.plugins.MVW.UT_DL.value and url[1]:
				txt = ensure_str(geturl(url[1]))
				if txt:
					txt = vttxmltosrt(txt)
					if txt:
						with open(self.dl_file[:-3] + "srt", "w") as f:
							f.write(txt)
			if config.plugins.MVW.DESC.value:
				desc = ensure_str(self["movielist"].getCurrent()[3])
				if desc:
					with open(self.dl_file[:-3] + "txt", "w") as f:
						f.write(desc)
			if ".m3u8" in url[0] or ".mp4" in url[0] or ".mp3" in url[0]:
				self.console = eConsoleAppContainer()
				self.console.dataAvail.append(self.avail)
				self.console.appClosed.append(self.finished)
				cmd = 'ffmpeg -y -i %s -headers "User-Agent: %s" -acodec copy -vcodec copy "%s"' % (url[0], UA, self.dl_file)
				self.console.execute(cmd)
				self["progress"].show()
				self["progress"].setValue(0)
				self["DownloadLabel"].setText("")
				self["DownloadLabel"].show()
			else:
				self.session.open(MessageBox, "Das Herunterladen der Datei wird nicht unterstützt.", MessageBox.TYPE_INFO, timeout=5)
				self.dl_file = None

	def avail(self, txt):
		try:
			if txt:
				txt = ensure_str(txt)
				if "Duration" in txt:
					duration = txt.split("Duration: ")[1].split(",")[0].split(":")
					if len(duration) == 3 and all(duration):
						self.totalDuration = float(duration[0]) * 3600 + float(duration[1]) * 60 + float(duration[2])
					else:
						self.totalDuration = 7200.00
				if "time=" in txt and self.totalDuration > 0:
					duration = txt.split("time=")[1].split(" ")[0].split(":")
					if len(duration) == 3 and duration[0].isdigit() and duration[1].isdigit():
						duration = float(duration[0]) * 3600 + float(duration[1]) * 60 + float(duration[2])
						if duration and self.totalDuration:
							progress = (duration / self.totalDuration) * 100
							self["progress"].setValue(int(progress))
							self["DownloadLabel"].setText(str(round(progress, 2)) + " %")
		except (KeyError, ValueError, IndexError):
			pass

	def finished(self, string):
		if self.dl_file:
			if string == 0:
				self.session.open(MessageBox, "Download erfolgreich", MessageBox.TYPE_INFO, timeout=5)
			else:
				self.session.open(MessageBox, "Download error", MessageBox.TYPE_INFO)
			self.console.sendCtrlC()
		self["progress"].hide()
		self["DownloadLabel"].hide()
		self.dl_file = None

	def Play(self, url):
		url = url and url[1]
		if url:
			sref = eServiceReference(4097, 0, ensure_str(url))
			sref.setName(self["movielist"].getCurrent()[1])
			self.session.open(Player, sref)

	def up(self):
		if self["movielist"]:
			self["movielist"].up()
			self.infos()

	def down(self):
		if self["movielist"]:
			self["movielist"].down()
			self.infos()

	def left(self):
		if self["movielist"]:
			self["movielist"].pageUp()
			self.infos()

	def right(self):
		if self["movielist"]:
			self["movielist"].pageDown()
			self.infos()

	def p_up(self):
		self["handlung"].pageUp()

	def p_down(self):
		self["handlung"].pageDown()

	def infos(self):
		if self["movielist"].getCurrent() is not None and isinstance(self["movielist"].getCurrent(), tuple):
			self["handlung"].setText(str(self["movielist"].getCurrent()[3]))
		if "MVW_PLAY" in self["movielist"].getCurrent()[0]:
			callInThread(self.mvw_image, self["movielist"].getCurrent()[4])
		else:
			self.show_cover()

	def show_cover(self):
		if self["movielist"].getCurrent() is not None:
			url = self["movielist"].getCurrent()[4]
			if url.startswith("http"):
				callInThread(self.getimage, url, self["movielist"].getIndex())
			elif url.startswith("/usr/"):
				self.get_cover(url)
			else:
				self.get_cover("%s/img/nocover.png" % PLUGINPATH)

	def getimage(self, url, index=0):
		try:
			data = geturl(url)
			with open(TMPIC, "wb") as f:
				f.write(data)
			if index == int(self["movielist"].getIndex()):
				self.get_cover(TMPIC)
		except (OSError, IOError):
			pass

	def get_cover(self, img):
		picload = ePicLoad()
		self["cover"].instance.setPixmap(gPixmapPtr())
		size = self["cover"].instance.size()
		picload.setPara((size.width(), size.height(), 1, 1, False, 1, "#FF000000"))
		if picload.startDecode(img, 0, 0, False) == 0:
			ptr = picload.getData()
			if ptr is not None:
				self["cover"].instance.setPixmap(ptr)
				self["cover"].show()


class Player(MoviePlayer):
	ENABLE_RESUME_SUPPORT = True

	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.skinName = "MoviePlayer"

	def up(self):
		pass

	def down(self):
		pass

	def leavePlayer(self):
		if config.plugins.MVW.SaveResumePoint.value and hasattr(InfoBarGenerics, "setResumePoint"):
			InfoBarGenerics.setResumePoint(self.session)
		self.close()

	def leavePlayerOnExit(self):
		self.leavePlayer()

	def doEofInternal(self, playing):
		if not playing or not self.execing:
			return
		self.close()


class ConfigScreen(ConfigListScreen, Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		ConfigListScreen.__init__(self, [])
		self.skin = readskin("Filesetup").replace("{name}", "config")
		self.skinName = "mvwConfigScreen_org" if config.plugins.MVW.INTSKIN.value else "mvwConfigScreen"
		self["PluginName"] = ScrollLabel("Einstellungen")
		self["key_red"] = StaticText("Abbrechen")
		self["key_green"] = StaticText("Speichern")
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"], {"cancel": self.cancel, "red": self.cancel, "ok": self.ok, "green": self.save}, -2)
		self.list = [("Skin", config.plugins.MVW.SkinColor), ("Download-Verzeichnis:", config.plugins.MVW.savetopath), ("Zukünftige Einträge anzeigen", config.plugins.MVW.FUTURE), ("Untertitel Downloaden", config.plugins.MVW.UT_DL), ("Cover Downloaden", config.plugins.MVW.COVER_DL), ("Handlung Downloaden", config.plugins.MVW.DESC), ("AutoPlay Beste Qualität", config.plugins.MVW.AUTOPLAY), ("Interne Skins benutzen", config.plugins.MVW.INTSKIN)]

		if hasattr(InfoBarGenerics, "setResumePoint"):
			self.list.append(("Letzte Abspielposition speichern", config.plugins.MVW.SaveResumePoint))
		self["config"].list = self.list

	def save(self):
		self.keySave()
		configfile.save()
		self.close()

	def cancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def ok(self):
		if self["config"].getCurrent()[1] == config.plugins.MVW.savetopath:
			dldir = config.plugins.MVW.savetopath.value
			self.session.openWithCallback(self.dl_Path, Browser, dldir)

	def dl_Path(self, res):
		if res:
			config.plugins.MVW.savetopath.value = res


class Browser(Screen):
	def __init__(self, session, dldir):
		Screen.__init__(self, session)
		self["PluginName"] = ScrollLabel("FileBrowser")
		self.skin = readskin("Filesetup").replace("{name}", "filelist")
		self.skinName = "mvwFileBrowser_org" if config.plugins.MVW.INTSKIN.value else "mvwFileBrowser"
		self["key_red"] = StaticText("Abbrechen")
		self["key_green"] = StaticText("Speichern")
		if not path.exists(dldir):
			dldir = "/"
		self.filelist = FileList(dldir, showFiles=False)
		self["filelist"] = self.filelist
		self["FilelistActions"] = ActionMap(["SetupActions", "ColorActions"], {"cancel": self.cancel, "red": self.cancel, "ok": self.ok, "green": self.save}, -2)

	def ok(self):
		if self.filelist.canDescent():
			self.filelist.descent()

	def save(self):
		fullpath = self["filelist"].getSelection()[0]
		if fullpath is not None and fullpath.endswith("/"):
			self.close(fullpath)

	def cancel(self):
		self.close(False)


class Choicebox(ChoiceBox):
	def __init__(self, session, title="", list=None):
		ChoiceBox.__init__(self, session, title, list)
		self["PluginName"] = ScrollLabel(title)
		self.skin = readskin("Filesetup").replace("{name}", "list")
		self.skinName = "mvwChoiceBox_org" if config.plugins.MVW.INTSKIN.value else "mvwChoiceBox"
		self["key_red"] = StaticText("Abbrechen")
		self["key_green"] = StaticText("Download" if "Dow" in title else "Play")

	def keyRed(self):
		self.close()

	def keyGreen(self):
		cursel = self["list"].l.getCurrentSelection()
		if cursel:
			self.goEntry(cursel[0])
		else:
			self.cancel()
