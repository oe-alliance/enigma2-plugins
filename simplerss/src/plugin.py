# PYTHON IMPORTS
from os import remove
from os.path import join, exists
from requests import get, exceptions
from traceback import print_exc
from twisted.internet.reactor import callInThread
from xml.etree.cElementTree import fromstring

# ENIGMA IMPORTS
from enigma import eTimer, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_BOTTOM, RT_WRAP, BT_SCALE, BT_KEEP_ASPECT_RATIO, BT_HALIGN_CENTER, BT_VALIGN_CENTER
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSubList, ConfigEnableDisable, ConfigNumber, ConfigText, ConfigSelection
from Components.ConfigList import ConfigListScreen
from Components.MenuList import MenuList
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.PluginComponent import plugins
from Components.ScrollLabel import ScrollLabel
from Components.Sources.Boolean import Boolean
from Components.Sources.List import List
from Components.Sources.StaticText import StaticText
from Plugins.Extensions.PicturePlayer import ui
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.Toolkit.TagStrip import strip, strip_readable
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from skin import parseFont
from Tools import Notifications
from Tools.Notifications import AddPopup, RemovePopup, AddNotificationWithID

# PLUGIN IMPORTS
from . import _  # for localized messages

# GLOBALS
rssPoller = None
tickerView = None
update_callbacks = []
TEMPPATH = "/tmp/"
MODULE_NAME = __name__.split(".")[-2]
NOTIFICATIONID = 'SimpleRSSUpdateNotification'
NS_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
NS_RSS_09 = "{http://my.netscape.com/rdf/simple/0.9/}"
NS_RSS_10 = "{http://purl.org/rss/1.0/}"

# Initialize Configuration
config.plugins.simpleRSS = ConfigSubsection()
simpleRSS = config.plugins.simpleRSS
simpleRSS.update_notification = ConfigSelection(choices=[("notification", _("Notification")), ("preview", _("Preview")), ("ticker", _("Ticker")), ("none", _("none"))], default="ticker")
simpleRSS.interval = ConfigNumber(default=15)
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
	if rssPoller is None:  # Create one if we have none (no autostart)
		rssPoller = RSSPoller()
	if rssPoller.feeds:  # Show Overview when we have feeds
		session.openWithCallback(closed, RSSOverview, rssPoller)
	else:  # Show Setup otherwise
		session.openWithCallback(closed, RSSSetup, rssPoller)  # Plugin window has been closed


def closed():  # If SimpleRSS should not run in Background: shutdown
	if not (config.plugins.simpleRSS.autostart.value or config.plugins.simpleRSS.keep_running.value):
		global rssPoller  # Get Global rssPoller-Object
		if rssPoller:
			rssPoller.shutdown()
		rssPoller = None


def autostart(reason, **kwargs):  # Autostart
	global rssPoller, tickerView
	if "session" in kwargs and config.plugins.simpleRSS.update_notification.value == "ticker" and tickerView is None:
		tickerView = kwargs["session"].instantiateDialog(RSSTickerView)
	# Instanciate when enigma2 is launching, autostart active and session present or installed during runtime
	if reason == 0 and config.plugins.simpleRSS.autostart.value and (not plugins.firstRun or "session" in kwargs):
		rssPoller = RSSPoller()
	elif reason == 1 and rssPoller is not None:
		rssPoller.shutdown()
		rssPoller = None


class MovingLabel(Label):  # Simple Label which allows to display badly scrolling text.
	def __init__(self, text=""):
		self.offset = 0
		self.displayLength = 100
		Label.__init__(self, text)
		self.moveTimer = eTimer()
		self.moveTimer.callback.append(self.doMove)

	def applySkin(self, desktop, screen):
		if self.skinAttributes is not None:
			attribs = []
			append = attribs.append
			for attrib, value in self.skinAttributes:
				if attrib == "displayLength":
					self.displayLength = int(value)
				else:
					append((attrib, value))
			self.skinAttributes = attribs
		return Label.applySkin(self, desktop, screen)

	def setText(self, text):
		text = (self.displayLength * " ") + text
		self.longText = text
		self.offset = 0
		text = text[:self.displayLength]
		Label.setText(self, text)

	def stopMoving(self):
		self.moveTimer.stop()
		self.offset = 0

	def startMoving(self):
		self.moveTimer.start(125)

	def doMove(self):
		offset = self.offset + 1
		text = self.longText[offset:self.displayLength + offset]
		self.offset = offset
		if not text:
			self.stopMoving()  # it appears we're done displaying the full text, so stop now or waste cpu time forever :D
		try:
			Label.setText(self, text)
		except Exception:
			self.stopMoving()


class MovingCallbackLabel(MovingLabel):  # Extended MovingLabel that allows to set a callback when done scrolling.
	def __init__(self, text="", callback=None):
		MovingLabel.__init__(self, text)
		self.callback = callback

	def stopMoving(self):
		MovingLabel.stopMoving(self)
		if self.callback:
			self.callback()


class RSSTickerView(Screen):  # pragma mark RSSTickerView, kinda sucks because of overscan, but gives me "good enough" results
	skin = """
	<screen position="0,536" size="720,30" flags="wfNoBorder">
		<widget name="newsLabel" position="0,0" size="720,20" font="Regular;18" halign="left" noWrap="1"/>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["newsLabel"] = MovingCallbackLabel(callback=self.hide)

	def updateText(self, feed):
		text = _("New Items") + ': ' + ' +++ '.join((item[0] for item in feed.history))
		self["newsLabel"].setText(text)

	def display(self, feed=None):
		if feed:
			self.updateText(feed)
		self.show()
		self["newsLabel"].startMoving()


class RSSFeedEdit(ConfigListScreen, Screen):  # Edit an RSS-Feed
	def __init__(self, session, ident):
		Screen.__init__(self, session)
		self.ident = ident
		self.skinName = ["RSSFeedEdit", "Setup"]
		s = config.plugins.simpleRSS.feed[ident]
		clist = [getConfigListEntry(_("Autoupdate"), s.autoupdate), getConfigListEntry(_("Feed URI"), s.uri)]
		ConfigListScreen.__init__(self, clist, session)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"save": self.save,
			"cancel": self.keyCancel
		}, -1)
		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		self.setTitle(_("Simple RSS Reader Setup"))

	def save(self):
		config.plugins.simpleRSS.feed[self.ident].save()
		config.plugins.simpleRSS.feed.save()
		self.close()


class RSSSetup(ConfigListScreen, Screen):  # Setup for SimpleRSS, quick-edit for Feed-URIs and settings present.
	skin = """
		<screen name="RSSSetup" position="center,center" size="560,400" title="Simple RSS Reader Setup" >
			<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="80,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="160,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="320,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<ePixmap position="500,0" size="140,40" pixmap="skin_default/buttons/key_menu" transparent="1" alphatest="on" />
			<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_green" render="Label" position="80,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_yellow" render="Label" position="160,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_blue" render="Label" position="320,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget source="key_menu" render="Label" position="500,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="config" position="5,45" size="550,350" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, rssPoller=None):
		Screen.__init__(self, session)
		self.rssPoller = rssPoller
		self.createSetup()
		config.plugins.simpleRSS.autostart.addNotifier(self.elementChanged, initial_call=False)
		ConfigListScreen.__init__(self, self.list, session)  # Initialize ConfigListScreen
		self["VKeyIcon"] = Boolean(False)
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("New"))
		self["key_blue"] = StaticText(_("Delete"))
		self["keymenu"] = StaticText(_("Import from '%sfeeds.xml'") % TEMPPATH)
		self["content"] = List([])
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"blue": self.delete,
			"yellow": self.new,
			"save": self.keySave,
			"menu": self.importFeedlist,
			"cancel": self.keyCancel,
			"ok": self.ok
		}, -1)
		self.onLayoutFinish.append(self.setCustomTitle)
		self.onClose.append(self.abort)

	def setCustomTitle(self):
		self.setTitle(_("Simple RSS Reader Setup"))

	def createSetup(self):
		simpleRSS = config.plugins.simpleRSS
		flist = [getConfigListEntry(_("Feed"), x.uri) for x in simpleRSS.feed]  # Create List of all Feeds
		flist.append(getConfigListEntry(_("Start automatically with Enigma2"), simpleRSS.autostart))
		self.keep_running = getConfigListEntry(_("Keep running in background"), simpleRSS.keep_running)  # Save keep_running in instance as we want to dynamically add/remove it
		if not simpleRSS.autostart.value:
			flist.append(self.keep_running)
		flist.extend((getConfigListEntry(_("Show new Messages as"), simpleRSS.update_notification), getConfigListEntry(_("Update Interval (min)"), simpleRSS.interval),))  # Append Last two config Elements
		self.list = flist

	def elementChanged(self, instance):
		self.createSetup()
		self["config"].setList(self.list)

	def notificationChanged(self, instance):
		global tickerView
		if instance and instance.value == "ticker":
			if tickerView is None:
				print("[%s] Ticker instantiated on startup" % MODULE_NAME)
				tickerView = self.session.instantiateDialog(RSSTickerView)
		else:
			if tickerView is not None:
				self.session.deleteDialog(tickerView)
				tickerView = None

	def delete(self):
		self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this entry?\nIt cannot be recovered!"), MessageBox.TYPE_YESNO, default=False)

	def deleteConfirm(self, result):
		if result:
			ident = self["config"].getCurrentIndex()
			del config.plugins.simpleRSS.feed[ident]
			config.plugins.simpleRSS.feedcount.value -= 1
			config.plugins.simpleRSS.feedcount.save()
			self.createSetup()
			self["config"].setList(self.list)

	def ok(self):
		ident = self["config"].getCurrentIndex()
		if ident < len(config.plugins.simpleRSS.feed):
			self.session.open(RSSFeedEdit, ident)

	def importFeedlist(self):
		feedfile = join(TEMPPATH, "feeds.xml")
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
		else:
			print("[%s] File '%s' was not found, import was aborted!" % (MODULE_NAME, feedfile))
			self.session.open(MessageBox, _("File '%s' was not found, import was aborted!" % feedfile), type=MessageBox.TYPE_ERROR, timeout=5)

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
			self.createSetup()
			self["config"].setList(self.list)

	def keySave(self):  # Tell Poller to recreate List if present
		if self.rssPoller is not None:
			self.rssPoller.triggerReload()
		ConfigListScreen.keySave(self)

	def abort(self):
		simpleRSS = config.plugins.simpleRSS
		simpleRSS.autostart.removeNotifier(self.elementChanged)  # Remove Notifier
		self.notificationChanged(simpleRSS.update_notification)  # Handle ticker
		simpleRSS.feedcount.value = len(simpleRSS.feed)  # Keep feedcount sane
		simpleRSS.feedcount.save()


class RSSSummary(Screen):
	skin = """
	<screen position="0,0" size="132,64">
		<widget source="parent.Title" render="Label" position="6,4" size="120,21" font="Regular;18" />
		<widget source="entry" render="Label" position="6,25" size="120,21" font="Regular;16" />
		<widget source="global.CurrentTime" render="Label" position="56,46" size="82,18" font="Regular;16" >
			<convert type="ClockToText">WithSeconds</convert>
		</widget>
	</screen>"""

	def __init__(self, session, parent):
		Screen.__init__(self, session, parent=parent)
		self["entry"] = StaticText("")
		parent.onChangedEntry.append(self.selectionChanged)
		self.onShow.append(parent.updateInfo)
		self.onClose.append(self.removeWatcher)

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)

	def selectionChanged(self, text):
		self["entry"].text = text


class RSSBaseView(Screen):  # Base Screen for all Screens used in SimpleRSS
	def __init__(self, session, poller, parent=None):
		Screen.__init__(self, session, parent)
		self.onChangedEntry = []
		self.rssPoller = poller
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

	def selectEnclosure(self, enclosures, show=True):  # Empty List
		if enclosures:
			return self.showEnclosure(enclosures, show)
#		else:
#			self.session.open(MessageBox, _("Found no Enclosure we can display."), type=MessageBox.TYPE_INFO, timeout=3)

	def showEnclosure(self, enclosures, show=True):
		filelist = []
		index = 0
		for enclosure in enclosures:
			if enclosure[1] in ["image/jpg", "image/png", "image/gif"]:
				filename = enclosure[0][enclosure[0].rfind("/") + 1:].lower()
				if self.pollEnclosure(enclosure[0], join(TEMPPATH, filename)):
					filelist.append(((join(TEMPPATH, filename), False), None))
				index = len(filelist) - 1
		if filelist:
			if show:
				self.session.open(ui.Pic_Full_View, filelist, index, TEMPPATH)
			return filelist

	def pollEnclosure(self, url, filename):
		header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0", "Accept": "text/xml"}
		if url:
			response = get
			try:
				response = get(url.encode(), headers=header, timeout=(3.05, 6))
				response.raise_for_status()
			except exceptions.RequestException as err:
				print("[%s] ERROR in module 'pollEnclosure': '%s" % (MODULE_NAME, str(err)))
			try:
				if not exists(filename):
					with open(filename, "wb") as f:
						f.write(response.content)
				return True
			except Exception as err:
				errmsg = "[%s] ERROR in module 'pollEnclosure': invalid xml data from server. %s" % (MODULE_NAME, str(err))
				print(errmsg)
		else:
			errmsg = "[%s] ERROR in module 'pollEnclosure': missing link." % MODULE_NAME
			print(errmsg)


class RSSEntryView(RSSBaseView):  # Shows a RSS Item
	skin = """
		<screen position="center,center" size="460,920" title="Simple RSS Reader" >
			<widget source="info" render="Label" position="0,0" size="460, 20" halign="right" font="Regular; 18" />
			<widget name="picture" position="54,305" size="200,100" alphatest="blend" />
			<widget name="content" position="0,20" size="460,400" font="Regular; 22" />
		</screen>"""

	def __init__(self, session, data, feedTitle="", cur_idx=None, entries=None, parent=None):
		RSSBaseView.__init__(self, session, None, parent)
		self.data = data
		self.feedTitle = feedTitle
		self.cur_idx = cur_idx
		self.entries = entries
		self["info"] = StaticText(_("Entry %s/%s") % (cur_idx + 1, entries)) if cur_idx is not None and entries is not None else StaticText()
		self["content"] = ScrollLabel(''.join((data[0], '\n\n', data[2], '\n\n', str(len(data[3])), ' ', _("Enclosures")))) if data else ScrollLabel()
		self["picture"] = Pixmap()
		self["actions"] = ActionMap(["OkCancelActions", "ChannelSelectBaseActions", "ColorActions", "DirectionActions"],
		{
			"cancel": self.close,
			"ok": self.selectEnclosure,
			"yellow": self.selectEnclosure,
			"up": self.up,
			"down": self.down,
			"right": self.next,
			"left": self.previous,
			"nextBouquet": self.nextFeed,
			"prevBouquet": self.previousFeed,
		})
		self.filelist = self.selectEnclosure(False)
		self.onLayoutFinish.append(self.setConditionalTitle)
		self.onClose.append(self.removeEnclosures)

	def setConditionalTitle(self):
		self["picture"].hide()
		self.setTitle(_("Simple RSS Reader: %s") % (self.feedTitle))
		self.setContent()

	def updateInfo(self):
		text = self.data[0] if self.data else _("No such Item.")
		for x in self.onChangedEntry:
			x(text)

	def up(self):
		self["content"].pageUp()

	def down(self):
		self["content"].pageDown()

	def next(self):
		if self.parent is not None:
			(self.data, self.cur_idx, self.entries) = self.parent.nextEntry()
			self.setContent()

	def previous(self):
		if self.parent is not None:
			(self.data, self.cur_idx, self.entries) = self.parent.previousEntry()
			self.setContent()

	def nextFeed(self):  # Show next Feed
		if self.parent is not None:
			self.showFeed(self.parent.next)

	def previousFeed(self):  # Show previous Feed
		if self.parent is not None:
			self.showFeed(self.parent.previous)

	def showFeed(self, direction):  # Show desired Feed
		result = direction()
		self.feedTitle = result[0]
		self.entries = len(result[1])
		if self.entries:
			self.cur_idx = 0
			self.data = result[1][0]
		else:
			self.cur_idx = None
			self.data = None
		self.setConditionalTitle()
		self.setContent()

	def setContent(self):
		if self.cur_idx is not None and self.entries is not None:
			self["info"].text = _("Entry %s/%s") % (self.cur_idx + 1, self.entries)
		else:
			self["info"].text = ""
		data = self.data
		if data:
			self["content"].setText(''.join((data[0], '\n\n', data[2], '\n\n', str(len(data[3])), ' ', _("Enclosures"))))
		else:
			self["content"].setText(_("No such Item."))
		if self.filelist:
			picfile = join(TEMPPATH, self.filelist[0][0][0])
			if exists(picfile):
				self["picture"].instance.setPixmapScaleFlags(BT_SCALE | BT_KEEP_ASPECT_RATIO | BT_HALIGN_CENTER | BT_VALIGN_CENTER)
				self["picture"].instance.setPixmapFromFile(picfile)
				self["picture"].show()
		self.updateInfo()

	def selectEnclosure(self, show=True):
		if self.data:
			return RSSBaseView.selectEnclosure(self, self.data[3], show)

	def removeEnclosures(self):
		if self.filelist:
			for file in self.filelist:
				if exists(file[0][0]):
					remove(file[0][0])


class RSSFeedView(RSSBaseView):  # Shows a RSS-Feed
	skin = """
		<screen position="center,center" size="460,415" title="Simple RSS Reader" >
			<widget source="info" render="Label" position="0,0" size="460,20" halign="right" font="Regular; 18" />
			<widget source="content" render="Listbox" position="0,20" size="460,300" scrollbarMode="showOnDemand">
				<convert type="TemplatedMultiContent">
					{"template": [
							MultiContentEntryText(pos=(0, 3), size=(460, 294), font=0, flags = RT_HALIGN_LEFT|RT_WRAP, text = 0)
						],
					 "fonts": [gFont("Regular", 22)],
					 "itemHeight": 50
					}
				</convert>
			</widget>
			<widget source="summary" render="Label" position="0,320" size="460,95" font="Regular;16" />
		</screen>"""

	def __init__(self, session, feed=None, newItems=False, parent=None, rssPoller=None, ident=None):
		RSSBaseView.__init__(self, session, rssPoller, parent)
		self.feed = feed
		self.newItems = newItems
		self.ident = ident
		self["content"] = List(feed.history) if feed else List([])
		self["summary"] = StaticText()
		self["info"] = StaticText()
		if not newItems:
			self["actions"] = ActionMap(["OkCancelActions", "ChannelSelectBaseActions", "MenuActions", "ColorActions"],
			{
				"ok": self.showCurrentEntry,
				"cancel": self.close,
				"nextBouquet": self.next,
				"prevBouquet": self.previous,
				"menu": self.menu,
				"yellow": self.selectEnclosure,
			})
			self.onLayoutFinish.append(self.__show)
			self.onClose.append(self.__close)
			self.timer = None
		else:
			self["actions"] = ActionMap(["OkCancelActions"],
			{
				"cancel": self.close,
			})
			self.timer = eTimer()
			self.timer.callback.append(self.timerTick)
			self.onExecBegin.append(self.startTimer)
		self["content"].onSelectionChanged.append(self.updateInfo)
		self.onLayoutFinish.extend((self.updateInfo, self.setConditionalTitle))

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
		if self.timer is not None:
			self.timer.callback.remove(self.timerTick)
			self.timer = None
		self.rssPoller.removeCallback(self.pollCallback)

	def pollCallback(self, ident=None):
		print("[%s] SimpleRSSFeed called back" % MODULE_NAME)
		if (ident is None or ident + 1 == self.ident) and self.feed:
			self["content"].updateList(self.feed.history)
			self.setConditionalTitle()
			self.updateInfo()

	def setConditionalTitle(self):
		if self.feed:
			self.setTitle(_("Simple RSS Reader: %s") % (self.feed.title))

	def updateInfo(self):
		current_entry = self["content"].current
		if current_entry:
			self["summary"].text = current_entry[2]
			cur_idx = self["content"].index
			if self.feed:
				self["info"].text = _("Entry %s/%s") % (cur_idx + 1, len(self.feed.history))
			summary_text = current_entry[0]
		else:
			self["summary"].text = _("Feed is empty.")
			self["info"].text = ""
			summary_text = _("Feed is empty.")
		for x in self.onChangedEntry:
			x(summary_text)

	def menu(self):
		if self.ident and self.id > 0:
			self.singleUpdate(self.ident - 1)

	def nextEntry(self):
		self["content"].selectNext()
		if self.feed:
			return (self["content"].current, self["content"].index, len(self.feed.history))

	def previousEntry(self):
		self["content"].selectPrevious()
		if self.feed:
			return (self["content"].current, self["content"].index, len(self.feed.history))

	def next(self):
		if self.parent is not None:  # Show next Feed
			(self.feed, self.ident) = self.parent.nextFeed()
			self["content"].list = self.feed.history
			self["content"].index = 0
			self.updateInfo()
			self.setConditionalTitle()  # Update title
			return (self.feed.title, self.feed.history, self.ident)
		if self.feed:
			return (self.feed.title, self.feed.history, self.ident)

	def previous(self):
		if self.parent is not None:  # Show previous Feed
			(self.feed, self.id) = self.parent.previousFeed()
			self["content"].list = self.feed.history
			self["content"].index = 0
			self.updateInfo()
			self.setConditionalTitle()  # Update title
			return (self.feed.title, self.feed.history, self.ident)
		if self.feed:
			return (self.feed.title, self.feed.history, self.ident)

	def checkEmpty(self):
		if self.ident and self.feed and self.ident > 0 and not len(self.feed.history):
			self.singleUpdate(self.ident - 1)

	def showCurrentEntry(self):
		current_entry = self["content"].current
		if current_entry and self.feed:
			self.session.openWithCallback(self.updateInfo, RSSEntryView, current_entry, cur_idx=self["content"].index, entries=len(self.feed.history), feedTitle=self.feed.title, parent=self)

	def selectEnclosure(self):
		current_entry = self["content"].current
		if current_entry:
			RSSBaseView.selectEnclosure(self, current_entry[3])


class RSSOverview(RSSBaseView):  # Shows an Overview over all RSS-Feeds known to rssPoller
	skin = """
		<screen position="center,center" size="460,415" title="Simple RSS Reader" >
			<widget source="info" render="Label" position="0,0" size="460,20" halign="right" font="Regular; 18" />
			<widget name="content" position="0,20" size="460,300" scrollbarMode="showOnDemand" />
			<widget source="summary" render="Label" position="0,320" size="460,95" font="Regular;16" />
		</screen>"""

	def __init__(self, session, poller):
		RSSBaseView.__init__(self, session, poller)
		self["actions"] = ActionMap(["OkCancelActions", "MenuActions", "ColorActions", "ChannelSelectBaseActions"],
		{
			"ok": self.showCurrentEntry,
			"cancel": self.close,
			"menu": self.menu,
			"yellow": self.selectEnclosure,
			"nextBouquet": self.keyPageDown,
			"prevBouquet": self.keyPageUp,
		})
		self.fillFeeds()
		self["content"] = RSSFeedList(self.feeds)  # We always have at least "New Items"-Feed
		self["summary"] = StaticText(' '.join((str(len(self.feeds[0][0].history)), _("Entries"))))
		self["info"] = StaticText(_("Feed %s/%s") % (1, len(self.feeds)))
		self["content"].connectSelChanged(self.updateInfo)
		self.onLayoutFinish.append(self.__show)
		self.onClose.append(self.__close)

	def __show(self):
		self.rssPoller.addCallback(self.pollCallback)
		self.setTitle(_("Simple RSS Reader"))

	def __close(self):
		global tickerView
		self.rssPoller.removeCallback(self.pollCallback)
		if tickerView is not None:
			self.session.deleteDialog(tickerView)
			tickerView = None

	def fillFeeds(self):  # Feedlist contains our virtual Feed and all real ones
		self.feeds = [(self.rssPoller.newItemFeed,)]
		self.feeds.extend([(feed,) for feed in self.rssPoller.feeds])

	def pollCallback(self, ident=None):
		print("[%s] SimpleRSS called back" % MODULE_NAME)
		self.fillFeeds()
		self["content"].setList(self.feeds)
		self.updateInfo()
		self["content"].invalidate()

	def updateInfo(self):
		current_entry = self["content"].getCurrent()
		self["summary"].text = ' '.join((str(len(current_entry.history)), _("Entries")))
		self["info"].text = _("Feed %s/%s") % (self["content"].getSelectedIndex() + 1, len(self.feeds))
		summary_text = current_entry.title
		for x in self.onChangedEntry:
			x(summary_text)

	def menu(self):
		cur_idx = self["content"].getSelectedIndex()
		possible_actions = ((_("Update Feed"), "update"), (_("Setup"), "setup"), (_("Close"), "close")) if cur_idx > 0 else ((_("Setup"), "setup"), (_("Close"), "close"))
		self.session.openWithCallback(self.menuChoice, ChoiceBox, _("What to do?"), possible_actions)

	def menuChoice(self, result):
		if result:
			if result[1] == "update":
				cur_idx = self["content"].getSelectedIndex()
				if cur_idx > 0:
					self.singleUpdate(cur_idx - 1)
			elif result[1] == "setup":
				self.session.openWithCallback(self.refresh, RSSSetup, rssPoller=self.rssPoller)
			elif result[1] == "close":
				self.close()

	def refresh(self):
		current_entry = self["content"].getCurrent()
		self.fillFeeds()
		self["content"].setList(self.feeds)
		self["content"].moveToEntry(current_entry)
		self.updateInfo()

	def nextFeed(self):
		self["content"].up()
		return (self["content"].getCurrent(), self["content"].getSelectedIndex())

	def previousFeed(self):
		self["content"].down()
		return (self["content"].getCurrent(), self["content"].getSelectedIndex())

	def keyPageUp(self):
		self["content"].pageUp()

	def keyPageDown(self):
		self["content"].pageDown()

	def showCurrentEntry(self):
		current_entry = self["content"].getCurrent()
		if current_entry and self.rssPoller:
			self.session.openWithCallback(self.updateInfo, RSSFeedView, feed=current_entry, parent=self, rssPoller=self.rssPoller, ident=self["content"].getSelectedIndex())

	def selectEnclosure(self):
		enclosures = []  # Build a list of all enclosures in this feed
		for entry in self["content"].getCurrent().history:
				enclosures.extend(entry[3])
		if enclosures:
			RSSBaseView.selectEnclosure(self, enclosures)


class RSSPoller:  # Keeps all Feed and takes care of (automatic) updates
	def __init__(self, poll=True):
		self.poll_timer = eTimer()  # Timer
		self.poll_timer.callback.append(self.poll)
		self.do_poll = poll
		self.reloading = False  # this indicates we're reloading the list of feeds
		self.newItemFeed = BaseFeed("", _("New Items"), _("New Items since last Auto-Update"),)
		self.feeds = [UniversalFeed(x.uri.value, x.autoupdate.value) for x in config.plugins.simpleRSS.feed]  # Generate Feeds
		if poll and self.poll_timer:
			self.poll_timer.start(0, 1)
		self.current_feed = 0  # Initialize Vars

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
			if ident is not None:  # Don't show this error when updating in background
				AddPopup(_("Sorry, this type of feed is unsupported:\n%s") % str(errmsg), MessageBox.TYPE_INFO, 5,)
			else:
				self.next_feed()  # We don't want to stop updating just because one feed is broken
		except Exception:
			print_exc()
			if errorback is not None:  # Errorback given, call it (asumme we don't need do restart timer!)
				errorback()
				return
			self.next_feed()  # Assume its just a temporary failure and jump over to next feed

	def singlePoll(self, feedid, errorback=None):
		self.pollXml(self.feeds[feedid].uri, errorback)

	def pollXml(self, feeduri, errorback=None):
		header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0", "Accept": "text/xml"}
		if feeduri:
			response = get
			try:
				response = get(feeduri.encode(), headers=header, timeout=(3.05, 6))
				response.raise_for_status()
			except exceptions.RequestException as err:
				print("[%s] ERROR in module 'pollXml': '%s" % (MODULE_NAME, str(err)))
				if errorback:
					errorback(str(err))
			try:
				xmlData = response.content
				if xmlData:
					self.gotPage(xmlData)
				else:
					print("[%s] ERROR in module 'pollXml': server access failed, no xml-data found." % MODULE_NAME)
			except Exception as err:
				print("[%s] ERROR in module 'pollXml': invalid xml data from server. %s" % (MODULE_NAME, str(err)))
				if errorback:
					errorback(str(err))
		else:
			print("[%s] ERROR in module 'pollXml': missing link." % MODULE_NAME)

	def gotPage(self, data, ident=None):
		feed = fromstring(data.decode())
		if ident is not None:  # For Single-Polling
			self.feeds[ident].gotFeed(feed)
			print("[%s] single feed parsed..." % MODULE_NAME)
			return
		new_items = self.feeds[self.current_feed].gotFeed(feed)
		print("[%s] feed parsed..." % MODULE_NAME)
		if new_items is not None:  # Append new items to locally bound ones
			self.newItemFeed.history.extend(new_items)
		self.next_feed()  # Start Timer so we can either fetch next feed or show new_items

	def poll(self):
		if self.reloading:  # Reloading, reschedule
			print("[%s] timer triggered while reloading, rescheduling" % MODULE_NAME)
			if self.poll_timer:
				self.poll_timer.start(10000, 1)
		elif len(self.feeds) <= self.current_feed:  # End of List
			if self.newItemFeed.history:  # New Items
				print("[%s] got new items, calling back" % MODULE_NAME)
				self.doCallback()
				update_notification_value = config.plugins.simpleRSS.update_notification.value  # Inform User
				if update_notification_value == "preview":
					RemovePopup(NOTIFICATIONID)
#					AddNotificationWithID(NOTIFICATIONID, RSSFeedView, feed=self.newItemFeed, newItems=True)  # ToDo: makes trobles when leaving plugin first time.
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
				self.poll_timer.startLongTimer(config.plugins.simpleRSS.interval.value * 60)
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
						if self.poll_timer:
							self.poll_timer.start(10000, 1)
				if clearHistory:
					for x in Xnotifications:
						if handler(x)[4] == NOTIFICATIONID:
							print("[%s] wont wipe history because it was never read" % MODULE_NAME)
							clearHistory = False
							break
			if clearHistory:
				del self.newItemFeed.history[:]
			feed = self.feeds[self.current_feed]  # Feed supposed to autoupdate
			if feed.autoupdate:
				self.pollXml(feed.uri, self.error)
			else:  # Go to next feed
				print("[%s] passing feed sucessfully" % MODULE_NAME)
				self.next_feed()

	def next_feed(self):
		self.current_feed += 1
		if self.poll_timer:
			self.poll_timer.start(1000, 1)

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
		self.poll()


class RSSFeedList(MenuList):
	def __init__(self, entries):
		MenuList.__init__(self, entries, False, content=eListboxPythonMultiContent)
		l = self.l
		l.setFont(0, gFont("Regular", 22))
		self.descriptionFont = gFont("Regular", 20)
		l.setFont(1, self.descriptionFont)
		l.setItemHeight(115)
		l.setBuildFunc(self.buildListboxEntry)

	def applySkin(self, desktop, parent):
		attribs = []
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1, 1), (1, 1))))
				elif attrib == "descriptionFont":
					self.descriptionFont = parseFont(value, ((1, 1), (1, 1)))
					self.l.setFont(1, self.descriptionFont)
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)

	def connectSelChanged(self, fnc):
		if not fnc in self.onSelectionChanged:
			self.onSelectionChanged.append(fnc)

	def disconnectSelChanged(self, fnc):
		if fnc in self.onSelectionChanged:
			self.onSelectionChanged.remove(fnc)

	def invalidate(self):
		self.l.invalidate()

	def moveToEntry(self, feed):
		if feed is None:
			return
		idx = 0
		for x in self.list:
			if feed.uri == x[0].uri:
				self.instance.moveSelectionTo(idx)
				break
			idx += 1

	def buildListboxEntry(self, feed):
		size = self.l.getItemSize()
		width = size.width()
		descriptionHeight = self.descriptionFont.pointSize + 2
		titleHeight = size.height() - descriptionHeight
		return [
			None,
			(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, titleHeight, 0, RT_HALIGN_LEFT | RT_WRAP, feed.title),
			(eListboxPythonMultiContent.TYPE_TEXT, 0, int(titleHeight * 0.65), width, int(descriptionHeight * 2.2), 1, RT_HALIGN_LEFT | RT_VALIGN_BOTTOM | RT_WRAP, feed.description)
		]

	def getCurrent(self):
		return self.l.getCurrentSelection()[0]  # We know that the list will never be empty...


class ElementWrapper:  # based on http://effbot.org/zone/element-rss-wrapper.htm
	def __init__(self, element, ns=""):
		self._element = element
		self._ns = ns

	def __getattr__(self, tag):
		if tag.startswith('__'):
			raise AttributeError(tag)
		return self._element.findtext(self._ns + tag)


class RSSEntryWrapper(ElementWrapper):
	def __getattr__(self, tag):
		if tag == "enclosures":
			myl = []
			for elem in self._element.findall(self._ns + 'enclosure'):
				myl.append((elem.get("url"), elem.get("type"), elem.get("length")))
			return myl
		elif tag == "id":
			return self._element.findtext(self._ns + 'guid', self.title + self.link)
		elif tag == "updated":
			tag = "lastBuildDate"
		elif tag == "summary":
			tag = "description"
		return ElementWrapper.__getattr__(self, tag)


class PEAEntryWrapper(ElementWrapper):
	def __getattr__(self, tag):
		if tag == "link":
			for elem in self._element.findall(self._ns + tag):
				if not elem.get("rel") == "enclosure":
					return elem.get("href")
			return ''
		elif tag == "enclosures":
			myl = []
			for elem in self._element.findall(self._ns + 'link'):
				if elem.get("rel") == "enclosure":
					myl.append((elem.get("href"), elem.get("type"), elem.get("length")))
			return myl
		elif tag == "summary":
			text = self._element.findtext(self._ns + 'summary')
			if not text:  # if we don't have a summary we use the full content instead
				elem = self._element.find(self._ns + 'content')
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
		RSSWrapper.__init__(self, feed.find(ns + 'channel'), feed.findall(ns + 'item'), ns)

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
		RSSWrapper.__init__(self, feed, feed.findall(ns + "entry"), ns)

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
		self.last_ids = set()
		self.wrapper = None
		self.ns = ""

	def gotWrapper(self, wrapper):
		updated = wrapper.updated
		if updated and self.last_update == updated:
			return []
		idx = 0
		ids = self.last_ids
		for item in wrapper:
			title = strip(item.title)  # Try to read title, continue if none found
			if not title:
				continue
			ident = item.id  # Try to read id, continue if none found (invalid feed or internal error) or to be excluded
			if not ident or ident in ids:
				continue
			link = item.link  # Link
			summary = strip_readable(item.summary or "")   # Try to read summary, empty if none
			self.history.insert(idx, (title, link, summary, item.enclosures))  # Update Lists
			ids.add(ident)
			idx += 1
		del self.history[self.MAX_HISTORY_ELEMENTS:]  # Eventually cut history
		return self.history[:idx]

	def gotFeed(self, feed):
		if self.wrapper is not None:
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
			self.title = strip(wrapper.title)
			self.description = strip_readable(wrapper.description or "")
			self.logoUrl = wrapper.logo
		return self.gotWrapper(wrapper)


def Plugins(**kwargs):
	return [PluginDescriptor(name="RSS Reader", description=_("A simple to use RSS reader"), icon="plugin.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, needsRestart=False,),
			PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart, needsRestart=False,),
 			PluginDescriptor(name=_("View RSS..."), description="Let's you view current RSS entries", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main, needsRestart=False,)
			]
