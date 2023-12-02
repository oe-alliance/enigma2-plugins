# general RSS-documentation: https://cyber.harvard.edu/rss/rss.html

# PYTHON IMPORTS
from os import mkdir, remove
from os.path import join, exists
from PIL import Image
from re import search
from requests import get, exceptions
from shutil import copy, rmtree
from traceback import print_exc
from twisted.internet.reactor import callInThread
from xml.etree.ElementTree import tostring, parse, fromstring

# current feed:
# self.feed: <<class 'Plugins.Extensions.SimpleRSS.plugin.UniversalFeed'>, "Title", "Description", 5 items>
# feed collection
# self.feeds: [(<Plugins.Extensions.SimpleRSS.plugin.BaseFeed object at 0xa688def0>,), (<Plugins.Extensions.SimpleRSS.plugin.UniversalFeed object at 0xa6890030>,), (<Plugins.Extensions.SimpleRSS.plugin.UniversalFeed object at 0xa68900b0>,), (<Plugins.Extensions.SimpleRSS.plugin.UniversalFeed object at 0xa68900d0>,), (<Plugins.Extensions.SimpleRSS.plugin.UniversalFeed object at 0xa68900f0>,), (<Plugins.Extensions.SimpleRSS.plugin.UniversalFeed object at 0xa6890110>,)]

# ENIGMA IMPORTS
from enigma import getDesktop, eTimer, BT_SCALE, BT_KEEP_ASPECT_RATIO, BT_HALIGN_CENTER, BT_VALIGN_CENTER
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSubList, ConfigEnableDisable, ConfigNumber, ConfigSelectionNumber, ConfigText, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Extensions.PicturePlayer import ui
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.Toolkit.TagStrip import strip, strip_readable
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools import Notifications
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from Tools.Notifications import AddPopup, RemovePopup, AddNotificationWithID

# PLUGIN IMPORTS
from . import _  # for localized messages

# GLOBALS
rssPoller = None
tickerView = None
update_callbacks = []
MODULE_NAME = __name__.split(".")[-2]
TEMPPATH = join("/tmp/", MODULE_NAME)  # /tmp/SimpleRSS/
PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/%s" % MODULE_NAME)  # /usr/lib/enigma2/python/Plugins/Extensions/SimpleRSS/
NOLOGO = "no_logo.png"
NOPIC = "no_pic.png"
NEWSLOGO = "latest_news.png"
NOTIFICATIONID = 'SimpleRSSUpdateNotification'
NS_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
NS_RSS_09 = "{http://my.netscape.com/rdf/simple/0.9/}"
NS_RSS_10 = "{http://purl.org/rss/1.0/}"

# Initialize Configuration
config.plugins.simpleRSS = ConfigSubsection()
simpleRSS = config.plugins.simpleRSS
simpleRSS.update_notification = ConfigSelection(choices=[("notification", _("Notification")), ("preview", _("Preview")), ("ticker", _("Ticker")), ("none", _("none"))], default="none")
simpleRSS.ticker_frequency = ConfigSelectionNumber(20, 200, 5, default=70)
simpleRSS.ticker_scrollspeed = ConfigSelectionNumber(1, 16, 1, default=4)
simpleRSS.interval = ConfigSelection(choices=[("5", "5"), ("10", "10"), ("15", "15"), ("30", "30"), ("45", "45"), ("60", "60"), ("90", "90"), ("120", "120")], default="15")
simpleRSS.feedcount = ConfigNumber(default=0)
simpleRSS.autostart = ConfigEnableDisable(default=False)
simpleRSS.keep_running = ConfigEnableDisable(default=True)
simpleRSS.feed = ConfigSubList()
i = 0
while i < simpleRSS.feedcount.value:
	s = ConfigSubsection()
	s.uri = ConfigText(default="http://", fixed_size=False)
	s.autoupdate = ConfigEnableDisable(default=True)
	simpleRSS.feed.append(s)
	i += 1
	del s
del simpleRSS, i


def main(session, **kwargs):  # Main Function
	global rssPoller  # Get Global rssPoller-Object
	if not exists(TEMPPATH):
		mkdir(TEMPPATH)
	for file in [NEWSLOGO, NOLOGO, NOPIC]:
		if exists(join(PLUGINPATH, "icons/", file)):
			copy(join(PLUGINPATH, "icons/", file), join(TEMPPATH, file))
	if rssPoller is None:  # Create one if we have none (no autostart)
		rssPoller = RSSPoller()
	if rssPoller.feeds:  # Show Overview when we have feeds
		session.openWithCallback(closed, RSS_Overview, rssPoller)
	else:  # Show Setup otherwise
		session.openWithCallback(closed, RSS_Setup, rssPoller)  # Plugin window has been closed


def closed():  # If SimpleRSS should not run in Background: shutdown
	if not (config.plugins.simpleRSS.autostart.value or config.plugins.simpleRSS.keep_running.value):
		global rssPoller  # Get Global rssPoller-Object
		if rssPoller:
			rssPoller.shutdown()
		rssPoller = None


def autostart(reason, **kwargs):  # Autostart
	global rssPoller, tickerView
	if "session" in kwargs:
		if config.plugins.simpleRSS.update_notification.value == "ticker" and tickerView is None:
			print("[%s] Ticker instantiated on autostart" % MODULE_NAME)
			tickerView = kwargs["session"].instantiateDialog(RSS_TickerView)
	# Instanciate when enigma2 is launching, autostart active and session present or installed during runtime
	if reason == 0 and config.plugins.simpleRSS.autostart.value and (not plugins.firstRun or "session" in kwargs):
		rssPoller = RSSPoller()
	elif reason == 1 and rssPoller:
		rssPoller.shutdown()
		rssPoller = None


def readSkin(skin):
	skintext = ""
	skinfile = join(PLUGINPATH, "skin_%s.xml" % ("fHD" if getDesktop(0).size().width() > 1300 else "HD"))
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


def downloadPicfile(url, picfile, resize=None, fixedname=None, callback=None):
	if picfile:
		header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0", "Accept": "text/xml"}
		if url:
			try:
				response = get(url.encode(), headers=header, timeout=(3.05, 6))
				picdata = response.content[:]  # make shallow copy
				response.raise_for_status()
				response.close()
				picfile = picfile.replace("jpeg", ".jpg")
				if fixedname:
					picfile = fixedname
				if not exists(picfile):
					with open(picfile, "wb") as f:
						f.write(picdata)
				isnotpng = not picfile.endswith(".png")
				if resize or isnotpng:
					img = Image.open(picfile)
					if resize:
						img.thumbnail(resize, Image.LANCZOS)  # resize, keeping aspect ratio and antialiasing
					pngfile = "%s.png" % picfile.split(".")[0]
					img.save(pngfile)  # forced save as PNG because some boxes (e.g. HD51) wrongly display JPGs transparently
					img.close()
					if isnotpng:
						remove(picfile)
				else:
					pngfile = picfile
				if callback:
					callback()
			except exceptions.RequestException as err:
				print("[%s] ERROR in module 'downloadPicfile': '%s" % (MODULE_NAME, str(err)))
		else:
			errmsg = "[%s] ERROR in module 'downloadPicfile': missing link." % MODULE_NAME
			print(errmsg)
	else:
		errmsg = "[%s] ERROR in module 'downloadPicfile': unsupported picture fileformat: %s" % (picfile, MODULE_NAME)
		print(errmsg)


def url2filename(url, forcepng=False):
	for itype in [".jpg", ".jpeg", ".png", ".gif"]:
		if itype in url:
			return "%s.png" % hash(url) if forcepng else ("%s%s" % (hash(url), itype)).replace(".jpeg", ".jpg")
	return ""


class RSS_TickerView(Screen):
	def __init__(self, session):
		self.session = session
		skin = readSkin("RSS_TickerView")
		newoptions = ["steptime=%d,step=%d" % (config.plugins.simpleRSS.ticker_frequency.value, config.plugins.simpleRSS.ticker_scrollspeed.value)]
		options = search(r'options\s*="(.*?)"', skin)
		if options:
			options = options.group(1)
			for option in options.split(","):
				if "step" not in option:  # remove entries 'steptime=' and 'step='…
					newoptions.append(option)
			newoptions = ",".join(newoptions)
			skin = skin.replace(options, newoptions)  # …and add/replace it with own entries
		self.skin = skin
		Screen.__init__(self, session, skin)
		self["newsLabel"] = StaticText()

	def updateText(self, feed):
		text = "%s: %s" % (_("New Items"), " +++ ".join((item[0] for item in feed.history)))
		self["newsLabel"].setText(text)

	def display(self, feed=None):
		if feed:
			self.updateText(feed)
		self.show()


class RSSFeedEdit(ConfigListScreen, Screen):  # Edit an RSS-Feed
	def __init__(self, session, ident):
		Screen.__init__(self, session)
		self.ident = ident
		self.skinName = ["RSSFeedEdit", "Setup"]
		s = config.plugins.simpleRSS.feed[ident]
		clist = [getConfigListEntry(_("Autoupdate"), s.autoupdate), getConfigListEntry(_("Feed URI"), s.uri)]
		ConfigListScreen.__init__(self, clist)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["setupActions"] = ActionMap(["SetupActions"], {"save": self.save, "cancel": self.keyCancel}, -1)
		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Simple RSS Reader Setup"))

	def save(self):
		config.plugins.simpleRSS.feed[self.ident].save()
		config.plugins.simpleRSS.feed.save()
		self.close()


class RSS_Setup(ConfigListScreen, Screen):  # Setup for SimpleRSS, quick-edit for Feed-URIs and settings present.
	def __init__(self, session, rssPoller=None):
		self.session = session
		self.skin = readSkin("RSS_Setup")
		Screen.__init__(self, session, self.skin)
		self.rssPoller = rssPoller
		config.plugins.simpleRSS.autostart.addNotifier(self.elementChanged, initial_call=False)
		ConfigListScreen.__init__(self, self.getSetupList(), on_change=self.elementChanged)
		self["title"] = StaticText(_("Simple RSS Reader Setup"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("New"))
		self["key_blue"] = StaticText(_("Delete"))
		self["content"] = List([])
		self["setupActions"] = ActionMap(["ColorActions",
											"SetupActions",
											"OkCancelActions",
											"MenuActions"], {"red": self.keyCancel,
															"green": self.keySave,
															"blue": self.delete,
															"yellow": self.new,
															"save": self.keySave,
															"menu": self.choiceImportSource,
															"cancel": self.keyCancel,
															"ok": self.ok
															}, -1)
		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Simple RSS Reader Setup"))

	def getSetupList(self):
		simpleRSS = config.plugins.simpleRSS
		clist = [getConfigListEntry(_("Feed"), x.uri) for x in simpleRSS.feed]  # Create List of all Feeds
		clist.append(getConfigListEntry(_("Start automatically with Enigma2"), simpleRSS.autostart))
		self.keep_running = getConfigListEntry(_("Keep running in background"), simpleRSS.keep_running)  # Save keep_running in instance as we want to dynamically add/remove it
		if not simpleRSS.autostart.value:
			clist.append(self.keep_running)
		clist.append(getConfigListEntry(_("Update Interval [min]"), simpleRSS.interval))
		clist.append(getConfigListEntry(_("Show new Messages as"), simpleRSS.update_notification))
		if simpleRSS.update_notification.value == "ticker":
			clist.append(getConfigListEntry(_(" *Frequency of scrollsteps [ms] (low values slow down the box)"), simpleRSS.ticker_frequency))
			clist.append(getConfigListEntry(_(" *Scrollspeed [pixels per step] (high values lead to jerking)"), simpleRSS.ticker_scrollspeed))
			clist.append(("",))
			clist.append((_(" *=please perform a GUI-restart for these changes to take effect"),))
		clist.append(("-" * 120,))
		clist.append((_("Note: If box becomes extremely slow, please reduce the quantity of feeds."),))
		return clist

	def elementChanged(self, instance=None):
		self["config"].setList(self.getSetupList())

	def notificationChanged(self, instance):
		global tickerView
		if instance and instance.value == "ticker":
			if tickerView is None:
				print("[%s] Ticker instantiated on startup" % MODULE_NAME)
				tickerView = self.session.instantiateDialog(RSS_TickerView)
		else:
			if tickerView:
				self.session.deleteDialog(tickerView)
				tickerView = None

	def delete(self):
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this entry?\nIt cannot be recovered!"), MessageBox.TYPE_YESNO, timeout=30, default=False)

	def deleteConfirm(self, result):
		if result:
			ident = self["config"].getCurrentIndex()
			del config.plugins.simpleRSS.feed[ident]
			config.plugins.simpleRSS.feedcount.value -= 1
			config.plugins.simpleRSS.feedcount.save()
			self["config"].setList(self.getSetupList())

	def ok(self):
		ident = self["config"].getCurrentIndex()
		if ident < len(config.plugins.simpleRSS.feed):
			self.session.open(RSSFeedEdit, ident)

	def choiceImportSource(self):
		possible_actions = (("/tmp/feeds.xml", "temp"), ("%s%s" % (PLUGINPATH, "feeds.xml"), "plugin"))
		self.session.openWithCallback(self.importFeedlist, ChoiceBox, _("Import feeds from:"), possible_actions)

	def importFeedlist(self, result):
		if not result:
			return
		feedpath = PLUGINPATH if result[1] == "plugin" else TEMPPATH
		feedfile = join(feedpath, "feeds.xml")
		if exists(feedfile):
			success = 0
			dupes = 0
			try:
				simpleRSS = config.plugins.simpleRSS
				with open(feedfile, "r") as f:
					xmlroot = fromstring(f.read())
					for child in xmlroot:
						if child.tag == "feed" and child[1].tag == "url":
							uri = child[1].text
							if uri in [x.uri.value for x in config.plugins.simpleRSS.feed]:
								print("[%s] Found double feed: '%s'" % (MODULE_NAME, uri))
								dupes += 1
							else:
								ident = self.addEntry()
								print("[%s] Feed was imported: '%s'" % (MODULE_NAME, uri))
								simpleRSS.feed[ident].uri.value = uri
								simpleRSS.feed[ident].save()
								simpleRSS.feedcount.value += 1
								success += 1
				if success:
					simpleRSS.feedcount.save()
					simpleRSS.feed.save()
			except Exception as err:
				print("[%s] ERROR in module 'importFeedlist' - xml-file was corrupt:\n%s" % (MODULE_NAME, str(err)))
				self.session.open(MessageBox, _("Xml-file '%s' was corrupt:\n%s" % (feedfile, str(err))), type=MessageBox.TYPE_ERROR, timeout=5)
				return
			print("[%s] Importing '%s': %s successfully, %s double" % (MODULE_NAME, feedfile, success, dupes))
			self.session.open(MessageBox, _("Importing '%s'\n%s feeds were imported successfully\n%s feeds were double and not imported") % (feedfile, success, dupes), type=MessageBox.TYPE_INFO, timeout=10)
			self.elementChanged(None)
		else:
			print("[%s] File '%s' was not found, import was aborted!" % (MODULE_NAME, feedfile))
			self.session.open(MessageBox, _("File '%s' was not found, import was aborted!") % feedfile, type=MessageBox.TYPE_ERROR, timeout=5)

	def addEntry(self):  # create entry
		l = config.plugins.simpleRSS.feed
		s = ConfigSubsection()
		s.uri = ConfigText(default="http://", fixed_size=False)
		s.autoupdate = ConfigEnableDisable(default=True)
		ident = len(l)
		l.append(s)
		return ident

	def new(self):
		self.session.openWithCallback(self.conditionalNew, RSSFeedEdit, self.addEntry())  # use default

	def conditionalNew(self):
		ident = len(config.plugins.simpleRSS.feed) - 1
		uri = config.plugins.simpleRSS.feed[ident].uri
		if uri.value == "http://":  # Check if new feed differs from default
			del config.plugins.simpleRSS.feed[ident]
		else:
			config.plugins.simpleRSS.feedcount.value = ident + 1
			self["config"].setList(self.getSetupList())

	def keySave(self):  # Tell Poller to recreate List if present
		if self.rssPoller:
			self.rssPoller.triggerReload()
		ConfigListScreen.keySave(self)
		self.close()

	def returnPolling(self):
		self.close()

	def errorPolling(self, errmsg=""):  # An error occured while polling
		self.session.open(MessageBox, _("Error while parsing Feed, this usually means there is something wrong with it."), type=MessageBox.TYPE_ERROR, timeout=3)
		if self.pollDialog:  # Don't show "we're updating"-dialog any longer
			self.pollDialog.close()
			self.pollDialog = None

	def keyCancel(self):
		simpleRSS = config.plugins.simpleRSS
		simpleRSS.autostart.removeNotifier(self.elementChanged)  # Remove Notifier
		self.notificationChanged(simpleRSS.update_notification)  # Handle ticker
		simpleRSS.feedcount.value = len(simpleRSS.feed)  # Keep feedcount sane
		simpleRSS.feedcount.save()
		self.close()


class RSSSummary(Screen):
	def __init__(self, session, parent):
		self.session = session
		self.skin = readSkin("RSSSummary")
		Screen.__init__(self, session, parent, self.skin)
		self["entry"] = StaticText("")
		parent.onChangedEntry.append(self.selectionChanged)
		self.onShow.append(parent.updateInfo)
		self.onClose.append(self.removeWatcher)

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)

	def selectionChanged(self, text):
		self["entry"].text = text


class RSSBaseView(Screen):  # Base Screen for all Screens used in SimpleRSS
	def __init__(self, session, poller):
		self.rssPoller = poller
		Screen.__init__(self, session)
		self.onChangedEntry = []
		self.pollDialog = None

	def createSummary(self):
		return RSSSummary

	def errorPolling(self, errmsg=""):  # An error occured while polling
		self.session.open(MessageBox, _("Error while parsing Feed, this usually means there is something wrong with it."), type=MessageBox.TYPE_ERROR, timeout=3)
		if self.pollDialog:  # Don't show "we're updating"-dialog any longer
			self.pollDialog.close()
			self.pollDialog = None

	def singleUpdate(self, feedid):  # Don't do anything if we have no poller
		if self.rssPoller:
			callInThread(self.rssPoller.singlePoll, feedid, errorback=self.errorPolling)  # Tell Poller to poll
			# Open Dialog and save locally
			self.pollDialog = self.session.open(MessageBox, _("Update is being done in Background.\nContents will automatically be updated when it's done."), type=MessageBox.TYPE_INFO, timeout=3)

	def findEnclosure(self, enclosures):
		if enclosures:
			urllist = []
			for enclosure in enclosures:
				if enclosure[1] in ["image/jpg", "image/jpeg", "image/png", "image/gif"]:
					urllist.append(enclosure[0].strip())
			return urllist


class RSS_EntryView(RSSBaseView):  # Shows a RSS Item
	def __init__(self, session, data, cur_idx=None, entries=None, feedTitle="", feedLogo=""):
		RSSBaseView.__init__(self, session, None)
		self.session = session
		self.data = data
		self.feedTitle = feedTitle
		self.cur_idx = cur_idx
		self.entries = entries
		self.feedpng = feedLogo
		self.pngfile = join(TEMPPATH, "entrypic.png")
		self.picsize = (382, 214) if getDesktop(0).size().width() > 1300 else (255, 143)
		self.skin = readSkin("RSS_EntryView")
		Screen.__init__(self, session, self.skin)
		self["title"] = StaticText(_("Simple RSS Reader EntryView"))
		self["info"] = StaticText(_("Entry %s/%s") % (cur_idx + 1, entries)) if cur_idx is not None and entries is not None else StaticText()
		self["content"] = ScrollLabel(''.join((data[0], '\n\n', data[2], '\n\n', str(len(data[3])), ' ', _("Enclosures")))) if data else ScrollLabel()
		self["feedlogo"] = Pixmap()
		self["picture"] = Pixmap()
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.selectEnclosure, "cancel": self.__close}, -1)
		self.onLayoutFinish.append(self.updateTitle)

	def updateTitle(self):
		feedpng = self.feedpng or join(TEMPPATH, NEWSLOGO)
		if exists(feedpng):
			self["feedlogo"].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
			self["feedlogo"].instance.setPixmapFromFile(feedpng)
			self["feedlogo"].show()
		else:
			self["feedlogo"].hide()
		self["picture"].hide()
		self.setTitle(_("Simple RSS Reader: %s") % (self.feedTitle))
		self["info"].text = _("Entry %s/%s") % (self.cur_idx + 1, self.entries) if self.cur_idx is not None and self.entries else ""
		data = self.data
		self["content"].setText(''.join((data[0], '\n\n', data[2], '\n\n', str(len(data[3])), ' ', _("Enclosures"))) if data else _("No such Item."))
		if data:
			urllist = RSSBaseView.findEnclosure(self, data[3])
			if urllist:
				picfile = join(TEMPPATH, url2filename(urllist[0]))
				callInThread(downloadPicfile, urllist[0], picfile, resize=self.picsize, fixedname=self.pngfile, callback=self.refreshPic)
		self.updateInfo()

	def updateInfo(self):
		text = self.data[0] if self.data else _("No such Item.")
		for x in self.onChangedEntry:
			x(text)
		self.refreshPic()

	def refreshPic(self):
		pngfile = self.pngfile if exists(self.pngfile) else join(TEMPPATH, NOPIC)
		self["picture"].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
		self["picture"].instance.setPixmapFromFile(pngfile)
		self["picture"].show()

	def selectEnclosure(self):
		if self.data:
			urllist = RSSBaseView.findEnclosure(self, self.data[3])
			if urllist:
				for url in urllist:
					self.filename = join(TEMPPATH, "full_%s" % url2filename(url))
					if exists(self.filename):
						self.showFullpic()
					else:
						callInThread(downloadPicfile, url, self.filename, callback=self.showFullpic)

	def showFullpic(self):
		pngfile = join(TEMPPATH, "%s.png" % self.filename.split(".")[0])
		piclist = []
		if exists(pngfile):
			piclist.append(((pngfile, False), None))
		if piclist:
			self.session.open(ui.Pic_Full_View, piclist, 0, TEMPPATH)

	def __close(self):
		if exists(self.pngfile):
			remove(self.pngfile)
		self.close()


class RSS_FeedView(RSSBaseView):  # Shows a RSS-Feed
	def __init__(self, session, feed=None, newItems=False, rssPoller=None, parent=None, ident=None):
		# structure of feed.history: ["titletext", "homepage-URL", "summarytext", "picture-URL"]
		RSSBaseView.__init__(self, session, rssPoller)
		self.session = session
		self.skin = readSkin("RSS_FeedView")
		Screen.__init__(self, session, self.skin)
		self.feed = feed
		self.newItems = newItems
		self.parent = parent  # restore, because 'Screen.__init' will set self.parent = 'Screen of Skin'
		self.ident = ident
		self.nopic = join(TEMPPATH, NOPIC)
		self.picsize = (225, 105) if getDesktop(0).size().width() > 1300 else (150, 70)
		self["feedlogo"] = Pixmap()
		self["title"] = StaticText(_("Simple RSS Reader Feedview"))
		self["content"] = List([])
		self["summary"] = StaticText()
		self["info"] = StaticText()
		self["button_bouquet"] = Pixmap()
		self["key_bouquet"] = StaticText(_("change feed"))
		if not newItems:
			self["actions"] = ActionMap(["ColorActions",
										"OkCancelActions",
										"DirectionActions",
										"MenuActions"], {"ok": self.showCurrentEntry,
														"cancel": self.close,
														"chplus": self.keyPageUp,
														"chminus": self.keyPageDown,
														"moveDown": self.nextFeed,
														"moveUp": self.prevFeed,
														"menu": self.menu
														}, -1)
			self.onLayoutFinish.append(self.__show)
			self.onClose.append(self.__close)
			self.timer = None
		else:
			self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.close})
			self.timer = eTimer()
			self.timer.callback.append(self.timerTick)
			self.onExecBegin.append(self.startTimer)
		linefile = join(PLUGINPATH, "icons/line_%s.png" % ("fHD" if getDesktop(0).size().width() > 1300 else "HD"))
		self.linepix = LoadPixmap(cached=True, path=linefile) if exists(linefile) else None
		self["content"].onSelectionChanged.append(self.updateInfo)
		self.onLayoutFinish.append(self.onLayoutFinished)

	def onLayoutFinished(self):
		if self.feed and self.feed.title == _("New Items"):
			self["content"].style = "news"
		else:
			self["content"].style = "default"
		pngfile = join(PLUGINPATH, "icons/bouquet_%s.png" % ("fHD" if getDesktop(0).size().width() > 1300 else "HD"))
		if exists(pngfile):
			self["button_bouquet"].instance.setPixmapFromFile(pngfile)
			self["button_bouquet"].show()
		else:
			self["button_bouquet"].hide()
		self.updateTitle()

	def updateTitle(self):
		self.buildSkinList()
		self.updateInfo()
		if self.feed:
			if self.feed.logoUrl:
				logopng = join(TEMPPATH, url2filename(self.feed.logoUrl, forcepng=True))
			else:
				logopng = join(TEMPPATH, NEWSLOGO) if self.feed.title == _("New Items") else join(TEMPPATH, NOLOGO)
			if exists(logopng):
				self["feedlogo"].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
				self["feedlogo"].instance.setPixmapFromFile(logopng)
				self["feedlogo"].show()
			else:
				self["feedlogo"].hide()
		else:
			self["feedlogo"].hide()
		if self.feed:
			self.setTitle(_("Simple RSS Reader: %s") % self.feed.title or self.feed.description)

	def startTimer(self):
		if self.timer:
			self.timer.startLongTimer(5)

	def timerTick(self):
		if self.timer:
			self.timer.callback.remove(self.timerTick)
		self.close()

	def __show(self):
		self.rssPoller.addCallback(self.pollCallback)

	def __close(self):
		if self.timer:
			self.timer.callback.remove(self.timerTick)
			self.timer = None
		self.rssPoller.removeCallback(self.pollCallback)

	def pollCallback(self, ident=None):
		print("[%s] SimpleRSSFeed called back" % MODULE_NAME)
		if (ident is None or (isinstance(ident, int) and ident + 1 == self.feed)) and self.feed:
			self.buildSkinList()
			self.updateTitle()
			self.updateInfo()

	def buildSkinList(self):
		skinlist = []
		if self.feed:
			for content in self.feed.history:
				urllist = RSSBaseView.findEnclosure(self, content[3])
				if urllist and self.feed and self.feed.title != _("New Items"):
					picfile = join(TEMPPATH, url2filename(urllist[0]))
					pngfile = "%s.png" % picfile.split(".")[0]
					if not exists(pngfile):
						callInThread(downloadPicfile, urllist[0], picfile, resize=self.picsize, callback=self.refreshPics)
						pngfile = self.nopic
				else:
					pngfile = self.nopic
				picpix = LoadPixmap(cached=True, path=pngfile) if exists(pngfile) else None
				skinlist.append((content[0], self.linepix, picpix))
			self["content"].updateList(skinlist)

	def refreshPics(self):
		skinlist = []
		if self.feed:
			for content in self.feed.history:
				picurl = content[3][0][0] if len(content[3]) > 0 else ""
				pngfile = join(TEMPPATH, url2filename(picurl, forcepng=True)) if picurl else self.nopic
				picpix = LoadPixmap(cached=True, path=pngfile) if exists(pngfile) else None
				skinlist.append((content[0], self.linepix, picpix))
			self["content"].updateList(skinlist)

	def updateInfo(self):
		if self.feed:
			cur_idx = self["content"].index % (len(self.feed.history) - 1)
			curr_entry = self.feed.history[cur_idx]
			if curr_entry:
				self["summary"].text = curr_entry[2]
				if self.feed:
					self["info"].text = _("Entry %s/%s - %s") % (cur_idx + 1, len(self.feed.history), self.feed.title)
				summary_text = curr_entry[0]
			else:
				self["summary"].text = _("Feed is empty.")
				self["info"].text = ""
				summary_text = _("Feed is empty.")
			for x in self.onChangedEntry:
				x(summary_text)

	def menu(self):
		if self.ident and self.ident > 0:
			self.singleUpdate(self.ident - 1)

	def nextEntry(self):
		self["content"].selectNext()
		if self.feed:
			cur_idx = self["content"].index % (len(self.feed.history) - 1)
			return (self.feed.history[cur_idx], cur_idx, len(self.feed.history))

	def previousEntry(self):
		self["content"].selectPrevious()
		if self.feed:
			cur_idx = self["content"].index % (len(self.feed.history) - 1)
			return (self.feed.history[cur_idx], cur_idx, len(self.feed.history))

	def nextFeed(self):
		if self.parent and self.ident:
			self.ident = (self.ident + 1) % len(self.parent)
			if not self.ident:  # exclude collecting channel "New Items"
				self.ident = 1
			self.feed = self.parent[self.ident][0]
			self.jumpFeed()

	def prevFeed(self):
		if self.parent and self.ident:
			self.ident = (self.ident - 1) % len(self.parent)
			if not self.ident:  # exclude collecting channel "New Items"
				self.ident = len(self.parent) - 1
			self.feed = self.parent[self.ident][0]
			self.jumpFeed()

	def jumpFeed(self):
		self["content"].index = 0
		self.buildSkinList()
		self.updateInfo()
		self.updateTitle()

	def checkEmpty(self):
		if self.ident and self.feed and self.ident > 0 and not len(self.feed.history):
			self.singleUpdate(self.ident - 1)

	def showCurrentEntry(self):
		if self.feed:
			cur_idx = self["content"].index % (len(self.feed.history) - 1)
			curr_entry = self.feed.history[cur_idx]
			if curr_entry and self.feed:
				if self.feed.logoUrl:
					pngfile = join(TEMPPATH, url2filename(self.feed.logoUrl, forcepng=True))
				else:
					pngfile = join(TEMPPATH, NEWSLOGO) if self.feed.title == _("New Items") else join(TEMPPATH, NOLOGO)
				self.session.openWithCallback(self.updateInfo, RSS_EntryView, curr_entry, cur_idx=cur_idx, entries=len(self.feed.history), feedTitle=self.feed.title, feedLogo=pngfile)

	def keyPageUp(self):
		self["content"].pageUp()

	def keyPageDown(self):
		self["content"].pageDown()


class RSS_Overview(RSSBaseView):  # Shows an Overview over all RSS-Feeds known to rssPoller
	def __init__(self, session, poller):
		self.session = session
		RSSBaseView.__init__(self, session, poller)
		self.skin = readSkin("RSS_Overview")
		Screen.__init__(self, session, self.skin)
		self.logosize = (225, 105) if getDesktop(0).size().width() > 1300 else (150, 70)
		self.fillFeeds()
		self["title"] = StaticText(_("Simple RSS Reader Overview"))
		self["content"] = List([])
		self["summary"] = StaticText(' '.join((str(len(self.feeds[0][0].history)), _("Entries"))))
		self["info"] = StaticText(_("Feed 1/%s") % len(self.feeds))
		self["actions"] = ActionMap(["ColorActions",
									"OkCancelActions",
									"DirectionActions",
									"MenuActions"], {"ok": self.showCurrentEntry,
													"cancel": self.__close,
													"menu": self.menu,
													"up": self.keyUp,
													"down": self.keyDown,
													"right": self.keyPageDown,
													"left": self.keyPageUp,
													"chminus": self.keyPageDown,
													"chplus": self.keyPageUp
													}, -1)
		linefile = join(PLUGINPATH, "icons/line_%s.png" % ("fHD" if getDesktop(0).size().width() > 1300 else "HD"))
		self.linepix = LoadPixmap(cached=True, path=linefile) if exists(linefile) else None
		self.onLayoutFinish.append(self.__show)
		self.onClose.append(self.__close)

	def __show(self):
		self.buildSkinList()
		self.rssPoller.addCallback(self.pollCallback)
		self.setTitle(_("Simple RSS Reader"))

	def __close(self):
		global tickerView
		self.rssPoller.removeCallback(self.pollCallback)
		if tickerView:
			self.session.deleteDialog(tickerView)
			tickerView = None
		if exists(TEMPPATH):
			try:
				rmtree(TEMPPATH)
			except OSError:
				pass
		self.close()

	def fillFeeds(self):  # Feedlist contains our virtual Feed and all real ones
		self.feeds = [(self.rssPoller.newItemFeed,)]
		self.feeds.extend([(feed,) for feed in self.rssPoller.feeds])

	def pollCallback(self, ident=None):
		print("[%s] SimpleRSS called back" % MODULE_NAME)
		self.fillFeeds()
		self.buildSkinList()
		self.updateInfo()

	def updateInfo(self):
		cur_idx = self["content"].index % len(self.feeds)
		curr_entry = self.feeds[cur_idx][0]
		self["info"].text = _("Feed %s/%s") % (cur_idx + 1, len(self.feeds))
		self["summary"].text = ' '.join((str(len(curr_entry.history)), _("Entries")))
		summary_text = curr_entry.title
		for x in self.onChangedEntry:
			x(summary_text)

	def buildSkinList(self):
		skinlist = []
		for feed in self.feeds:
			title = feed[0].title
			descr = feed[0].description
			logourl = feed[0].logoUrl
			if logourl:
				logofile = join(TEMPPATH, url2filename(logourl))
				print("logofile: %s" % logofile)
				logopng = "%s.png" % logofile.split(".")[0]
				if not exists(logopng):
					callInThread(downloadPicfile, logourl, logofile, resize=self.logosize, callback=self.refreshPics)
			else:
				logopng = join(TEMPPATH, NEWSLOGO) if title == _("New Items") else join(TEMPPATH, NOLOGO)
			picpix = LoadPixmap(cached=True, path=logopng) if exists(logopng) else None
			skinlist.append((title, descr, self.linepix, picpix))
		self["content"].updateList(skinlist)

	def refreshPics(self):
		skinlist = []
		for feed in self.feeds:
			title = feed[0].title
			descr = feed[0].description
			logourl = feed[0].logoUrl
			if logourl:
				logofile = join(TEMPPATH, url2filename(logourl, forcepng=True))
			else:
				logofile = join(TEMPPATH, NEWSLOGO) if title == _("New Items") else join(TEMPPATH, NOLOGO)
			picpix = LoadPixmap(cached=True, path=logofile) if exists(logofile) else None
			skinlist.append((title, descr, self.linepix, picpix))
		self["content"].updateList(skinlist)

	def menu(self):
		cur_idx = self["content"].index
		possible_actions = ((_("Update Feed"), "update"), (_("Settings"), "setup"), (_("Close"), "close")) if cur_idx > 0 else ((_("Settings"), "setup"), (_("Close"), "close"))
		self.session.openWithCallback(self.menuChoice, ChoiceBox, _("What to do?"), possible_actions)

	def menuChoice(self, result):
		if result:
			if result[1] == "update":
				cur_idx = self["content"].index
				if cur_idx > 0:
					self.singleUpdate(cur_idx - 1)
			elif result[1] == "setup":
				self.session.openWithCallback(self.pollCallback, RSS_Setup, rssPoller=self.rssPoller)
			elif result[1] == "close":
				self.__close()

	def refresh(self):
		cur_idx = self["content"].index
		self.fillFeeds()
		self["content"].setIndex(cur_idx)
		self.updateInfo()

	def keyUp(self):
		self["content"].up()
		self.updateInfo()

	def keyDown(self):
		self["content"].down()
		self.updateInfo()

	def keyPageUp(self):
		self["content"].pageUp()
		self.updateInfo()

	def keyPageDown(self):
		self["content"].pageDown()
		self.updateInfo()

	def showCurrentEntry(self):
		cur_idx = self["content"].index % len(self.feeds)
		curr_entry = self.feeds[cur_idx][0]
		if curr_entry and self.rssPoller:
			self.session.openWithCallback(self.updateInfo, RSS_FeedView, feed=curr_entry, parent=self.feeds, rssPoller=self.rssPoller, ident=cur_idx)


class RSSPoller:  # Keeps all Feed and takes care of (automatic) updates
	def __init__(self, poll=True):
		self.poll_timer = eTimer()  # Timer
		self.poll_timer.callback.append(self.poll)
		self.do_poll = poll
		self.reloading = False  # this indicates we're reloading the list of feeds
		self.newItemFeed = BaseFeed("", _("New Items"), _("New Items since last Auto-Update"),)
		self.feeds = [UniversalFeed(x.uri.value, x.autoupdate.value) for x in config.plugins.simpleRSS.feed]  # Generate Feeds
		self.current_feed = 0  # Initialize Vars
		if poll:
			self.poll()

	def addCallback(self, callback):
		if callback not in update_callbacks:
			update_callbacks.append(callback)

	def removeCallback(self, callback):
		if callback in update_callbacks:
			update_callbacks.remove(callback)

	def doCallback(self, ident=None):
		for callback in update_callbacks:
			callback(id)

	def error(self, error=""):
		print("[%s] failed to fetch feed: %s" % (MODULE_NAME, str(error)))
		self.next_feed()  # Assume its just a temporary failure and jump over to next feed

	def _gotPage(self, ident=None, callback=False, errorback=None, data=None):
		try:  # workaround: exceptions in gotPage-callback were ignored
			self.gotPage(data, ident)
			if callback:
				self.doCallback(ident)
		except NotImplementedError as errmsg:
			if ident:  # Don't show this error when updating in background
				AddPopup(_("Sorry, this type of feed is unsupported:\n%s") % str(errmsg), MessageBox.TYPE_INFO, timeout=3)
			else:
				self.next_feed()  # We don't want to stop updating just because one feed is broken
		except Exception:
			print_exc()
			if errorback:  # Errorback given, call it (asumme we don't need do restart timer!)
				errorback()
				return
			self.next_feed()  # Assume its just a temporary failure and jump over to next feed

	def singlePoll(self, feedid, errorback=None):
		callInThread(self.pollXml, self.feeds[feedid].uri, errorback)

	def pollXml(self, feeduri, errorback=None):
		header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0", "Accept": "text/xml"}
		if feeduri:
			try:
				response = get(feeduri.encode(), headers=header, timeout=(3.05, 6))
				response.raise_for_status()
				xmlData = response.content
				response.close()
				try:
					if xmlData:
						self.gotPage(xmlData)
					else:
						print("[%s] ERROR in module 'pollXml': server access failed, no xml-data found." % MODULE_NAME)
				except Exception as err:
					print("[%s] ERROR in module 'pollXml': invalid xml data from server. %s" % (MODULE_NAME, str(err)))
					if errorback:
						errorback(str(err))
			except exceptions.RequestException as err:
				print("[%s] ERROR in module 'pollXml': '%s" % (MODULE_NAME, str(err)))
				if errorback:
					errorback(str(err))
		else:
			print("[%s] ERROR in module 'pollXml': missing link." % MODULE_NAME)

	def gotPage(self, data, ident=None):
		feed = fromstring(data.decode())
		if ident:  # For Single-Polling
			self.feeds[ident].gotFeed(feed)
			print("[%s] single feed parsed..." % MODULE_NAME)
			return
		new_items = self.feeds[self.current_feed].gotFeed(feed)
		print("[%s] feed parsed..." % MODULE_NAME)
		if new_items:  # Append new items to locally bound ones
			self.newItemFeed.history.extend(new_items)
		self.next_feed()  # Start Timer so we can either fetch next feed or show new_items

	def poll(self):
		if self.reloading:  # Reloading, reschedule
			print("[%s] timer triggered while reloading, rescheduling" % MODULE_NAME)
		elif len(self.feeds) <= self.current_feed:  # End of List
			if self.newItemFeed.history:  # New Items
				print("[%s] got new items, calling back" % MODULE_NAME)
				self.doCallback()
				update_notification_value = config.plugins.simpleRSS.update_notification.value  # Inform User
				if update_notification_value == "preview":
					RemovePopup(NOTIFICATIONID)
					AddNotificationWithID(NOTIFICATIONID, RSS_FeedView, feed=self.newItemFeed, newItems=True)
				elif update_notification_value == "notification":
					AddPopup(_("Received %d new news item(s).") % (len(self.newItemFeed.history)), MessageBox.TYPE_INFO, 5, NOTIFICATIONID)
				elif update_notification_value == "ticker":
					if tickerView:
						tickerView.display(self.newItemFeed)
					else:
						print("[%s] missing ticker instance, something is wrong with the code" % MODULE_NAME)
			else:  # No new Items
				print("[%s] no new items" % MODULE_NAME)
			self.current_feed = 0
			if self.poll_timer:
				self.poll_timer.startLongTimer(int(config.plugins.simpleRSS.interval.value) * 60)
		else:  # It's updating-time
			clearHistory = self.current_feed == 0  # Assume we're cleaning history if current feed is 0
			if config.plugins.simpleRSS.update_notification.value != "none":
				if hasattr(Notifications.notifications, 'Notifications.notificationQueue'):
					Xnotifications = Notifications.notificationQueue.queue
					Xcurrent_notifications = Notifications.notificationQueue.current
					handler = lambda note: (note.fnc, note.screen, note.args, note.kwargs, note.id)
					handler_current = lambda note: (note[0].id,)
				else:
					Xnotifications = Notifications.notifications
					Xcurrent_notifications = Notifications.current_notifications
					handler_current = handler = lambda note: note
				for x in Xcurrent_notifications:
					if handler_current(x)[0] == NOTIFICATIONID:
						print("[%s] timer triggered while preview on screen, rescheduling" % MODULE_NAME)
				if clearHistory:
					for x in Xnotifications:
						if handler(x)[4] == NOTIFICATIONID:
							print("[%s] wont wipe history because it was never read" % MODULE_NAME)
							clearHistory = False
							break
			if clearHistory:
				del self.newItemFeed.history[:]  # make shallow copy
			feed = self.feeds[self.current_feed]  # Feed supposed to autoupdate
			if feed.autoupdate:
				callInThread(self.pollXml, feed.uri, self.error)
			else:  # Go to next feed
				print("[%s] passing feed sucessfully" % MODULE_NAME)
				self.next_feed()

	def next_feed(self):
		self.current_feed += 1
		self.poll()

	def shutdown(self):
		if self.poll_timer:
			self.poll_timer.callback.remove(self.poll)
			self.poll_timer = None
			self.do_poll = False

	def triggerReload(self):
		self.reloading = True
		newfeeds = []
		oldfeeds = self.feeds
		found = False
		for x in config.plugins.simpleRSS.feed:
			for feed in oldfeeds:
				if x.uri.value == feed.uri:
					feed.autoupdate = x.autoupdate.value  # Update possibly different autoupdate value
					newfeeds.append(feed)  # Append to new Feeds
					oldfeeds.remove(feed)  # Remove from old Feeds
					found = True
					break
			if not found:
				newfeeds.append(UniversalFeed(x.uri.value, x.autoupdate.value))
			found = False
		self.feeds = newfeeds
		self.reloading = False
		self.poll


class ElementWrapper:  # based on http://effbot.org/zone/element-rss-wrapper.htm
	def __init__(self, element, ns=""):
		self._element = element
		self._ns = ns

	def __getattr__(self, tag):
		if tag.startswith('__'):
			raise AttributeError(tag)
		return self._element.findtext("%s%s" % (self._ns, tag))


class RSSEntryWrapper(ElementWrapper):
	def __getattr__(self, tag):
		if tag == "media:content":
			myl = []
			for elem in self._element.findall("%senclosure" % self._ns):
				myl.append((elem.get("url"), elem.get("type"), elem.get("width"), elem.get("height"), elem.get("medium")))
			return myl
		elif tag == "enclosures":
			myl = []
			for elem in self._element.findall("%senclosure" % self._ns):
				myl.append((elem.get("url"), elem.get("type"), elem.get("length")))
			return myl
		elif tag == "id":
			return self._element.findtext("%sguid" % self._ns, self.title + self.link)
		elif tag == "updated":
			tag = "lastBuildDate"
		elif tag == "summary":
			tag = "description"
		return ElementWrapper.__getattr__(self, tag)


class PEAEntryWrapper(ElementWrapper):
	def __getattr__(self, tag):
		if tag == "link":
			for elem in self._element.findall("%s%s" % (self._ns, tag)):
				if not elem.get("rel") == "enclosure":
					return elem.get("href")
			return ''
		elif tag == "enclosures":
			myl = []
			for elem in self._element.findall("%slink" % self._ns):
				if elem.get("rel") == "enclosure":
					myl.append((elem.get("href"), elem.get("type"), elem.get("length")))
			return myl
		elif tag == "summary":
			text = self._element.findtext("%ssummary" % self._ns)
			if not text:  # if we don't have a summary we use the full content instead
				elem = self._element.find("%scontent" % self._ns)
				if elem is not None and elem.get('type') == "html":
					text = elem.text
			return text
		return ElementWrapper.__getattr__(self, tag)


class RSSWrapper(ElementWrapper):
	def __init__(self, channel, items, ns=""):
		self._items = items
		ElementWrapper.__init__(self, channel, ns)

	def __iter__(self):
		self.idx = 0
		self.len = len(self) - 1
		return self

	def __next__(self):
		idx = self.idx
		if idx > self.len:
			raise StopIteration
		self.idx = idx + 1
		return self[idx]

	def __len__(self):
		return len(self._items)

	def __getitem__(self, index):
		return RSSEntryWrapper(self._items[index], self._ns)


class RSS1Wrapper(RSSWrapper):
	def __init__(self, feed, ns):
		RSSWrapper.__init__(self, feed.find("%schannel" % ns), feed.findall("%sitem" % ns), ns)

	def __getattr__(self, tag):
		if tag == 'logo':  # afaik not officially part of older rss, but can't hurt
			tag = 'image'
		return ElementWrapper.__getattr__(self, tag)


class RSS2Wrapper(RSSWrapper):
	def __init__(self, feed, ns):
		channel = feed.find("channel")
		RSSWrapper.__init__(self, channel, channel.findall("item"))

	def __getattr__(self, tag):
		if tag == 'logo':
			tag = 'image'
		return ElementWrapper.__getattr__(self, tag)


class PEAWrapper(RSSWrapper):
	def __init__(self, feed, ns):
		ns = feed.tag[:feed.tag.index("}") + 1]
		RSSWrapper.__init__(self, feed, feed.findall("%sentry" % ns), ns)

	def __getitem__(self, index):
		return PEAEntryWrapper(self._items[index], self._ns)

	def __getattr__(self, tag):
		if tag == "description":
			tag = "subtitle"
		return ElementWrapper.__getattr__(self, tag)


class BaseFeed:  # Base-class for all Feeds. Initializes needed Elements.
	MAX_HISTORY_ELEMENTS = 100

	def __init__(self, uri, title="", description=""):
		self.uri = uri  # Initialize
		self.title = title or uri
		self.description = description or _("trying to download the feed...")
		self.logoUrl = ""
		self.history = []

	def __str__(self):
		return "<%s, \"%s\", \"%s\", %d items>" % (self.__class__, self.title, self.description, len(self.history))


class UniversalFeed(BaseFeed):  # Feed which can handle rdf, rss and atom feeds utilizing abstraction wrappers.
	def __init__(self, uri, autoupdate, sync=False):
		BaseFeed.__init__(self, uri)
		self.autoupdate = autoupdate  # Set Autoupdate
		self.sync = sync  # Is this a synced feed?
		self.last_update = None  # Initialize
		self.last_idents = set()
		self.wrapper = None
		self.ns = ""

	def gotWrapper(self, wrapper):
		updated = wrapper.updated
		if updated and self.last_update == updated:
			return []
		idx = 0
		idents = self.last_idents
		for item in wrapper:
			title = strip(item.title)  # Try to read title, continue if none found
			if not title:
				continue
			ident = item.id  # Try to read id, continue if none found (invalid feed or internal error) or to be excluded
			if not ident or ident in idents:
				continue
			link = item.link  # Link
			summary = strip_readable(item.summary or "")   # Try to read summary, empty if none
			self.history.insert(idx, (title, link, summary, item.enclosures))  # Update Lists
			idents.add(ident)
			idx += 1
		del self.history[self.MAX_HISTORY_ELEMENTS:]  # Eventually cut history
		return self.history[:idx]

	def gotFeed(self, feed):  # select wrapping method and
		if self.wrapper:
			wrapper = self.wrapper(feed, self.ns)
		else:
			if feed.tag == "rss":
				self.wrapper = RSS2Wrapper
			elif feed.tag.startswith(NS_RDF):
				self.ns = NS_RDF
				self.wrapper = RSS1Wrapper
			elif feed.tag.startswith(NS_RSS_09):
				self.ns = NS_RSS_09
				self.wrapper = RSS1Wrapper
			elif feed.tag.startswith(NS_RSS_10):
				self.ns = NS_RSS_10
				self.wrapper = RSS1Wrapper
			elif feed.tag.endswith("feed"):
				self.wrapper = PEAWrapper
			else:
				raise NotImplementedError('Unsupported Feed: %s' % feed.tag)
			wrapper = self.wrapper(feed, self.ns)
			title = strip(wrapper.title) or ""
			self.title = title[title.find("-") + 1:].strip()  # remove leading "-"
			self.description = strip_readable(wrapper.description) or ""
			for child in feed.findall("channel"):  # perhaps not the most elegant way but it works
				image = child.find("image")
				if image:
					logoUrl = image.find("url").text
					self.logoUrl = logoUrl
		return self.gotWrapper(wrapper)


def Plugins(**kwargs):
	return [PluginDescriptor(name="RSS Reader", description=_("A simple to use RSS reader"), icon="plugin.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, needsRestart=False,),
			PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart, needsRestart=False,),
 			PluginDescriptor(name=_("View RSS..."), description="Let's you view current RSS entries", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main, needsRestart=False,)
			]
