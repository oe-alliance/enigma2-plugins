##
## Movielist Preview
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigInteger, ConfigSelection, ConfigSubsection, ConfigYesNo, getConfigListEntry

from Components.ConfigList import ConfigListScreen
from Components.Console import Console
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MovieList import MovieList
from Components.Pixmap import Pixmap
from Components.ServiceEventTracker import InfoBarBase
from Components.VideoWindow import VideoWindow
from enigma import ePicLoad, ePoint, eServiceReference, eSize, eTimer, getDesktop
from os import listdir
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarCueSheetSupport
from Screens.MessageBox import MessageBox
from Screens.MovieSelection import MovieSelection
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
import os, gettext, random

##############################################################################

config.plugins.MovielistPreview = ConfigSubsection()
config.plugins.MovielistPreview.enabled = ConfigYesNo(default=True)
config.plugins.MovielistPreview.position_x = ConfigInteger(default=100)
config.plugins.MovielistPreview.position_y = ConfigInteger(default=100)
config.plugins.MovielistPreview.size = ConfigSelection(choices=["250x200", "200x160", "150x120", "100x80"], default="250x200")

##############################################################################

PluginLanguageDomain = "MovielistPreview"
PluginLanguagePath = "Extensions/MovielistPreview/locale/"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())

##############################################################################

SKIN = """
	<screen position="0,0" size="250,200" zPosition="10" flags="wfNoBorder" backgroundColor="#FF000000" >
		<widget name="background" position="0,0" size="250,200" zPosition="1" backgroundColor="#00000000" />
		<widget name="preview" position="0,0" size="250,200" zPosition="2" />
	</screen>"""

##############################################################################

class MovielistPreviewScreen(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = SKIN
		self["background"] = Label("")
		self["preview"] = Pixmap()
		self.onShow.append(self.movePosition)

	def movePosition(self):
		if self.instance:
			self.instance.move(ePoint(config.plugins.MovielistPreview.position_x.value, config.plugins.MovielistPreview.position_y.value))
			size = config.plugins.MovielistPreview.size.value.split("x")
			self.instance.resize(eSize(int(size[0]), int(size[1])))
			self["background"].instance.resize(eSize(int(size[0]), int(size[1])))
			self["preview"].instance.resize(eSize(int(size[0]), int(size[1])))

##############################################################################

class MovielistPreview():
	def __init__(self):
		self.dialog = None
		self.mayShow = True
		self.working = False

	def gotSession(self, session):
		if not self.dialog:
			self.dialog = session.instantiateDialog(MovielistPreviewScreen)

	def changeVisibility(self):
		if config.plugins.MovielistPreview.enabled.value:
			config.plugins.MovielistPreview.enabled.value = False
		else:
			config.plugins.MovielistPreview.enabled.value = True
		config.plugins.MovielistPreview.enabled.save()

	def showPreview(self, movie):
		if self.working == False:
			self.dialog.hide()
			if movie and self.mayShow and config.plugins.MovielistPreview.enabled.value:
				png = movie + "_mp.jpg"
				if fileExists(png):
					self.working = True
					sc = AVSwitch().getFramebufferScale()
					self.picload = ePicLoad()
					self.picload.PictureData.get().append(self.showPreviewCallback)
					size = config.plugins.MovielistPreview.size.value.split("x")
					self.picload.setPara((int(size[0]), int(size[1]), sc[0], sc[1], False, 1, "#00000000"))
					self.picload.startDecode(png)

	def showPreviewCallback(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			self.dialog["preview"].instance.setPixmap(ptr)
			self.dialog.show()
		self.working = False

	def hideDialog(self):
		self.mayShow = False
		self.dialog.hide()

	def showDialog(self):
		self.mayShow = True
		self.dialog.show()
movielistpreview = MovielistPreview()

##############################################################################

class MovielistPreviewPositionerCoordinateEdit(ConfigListScreen, Screen):
	skin = """
		<screen position="center,center" size="560,110" title="%s">
			<ePixmap pixmap="buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="config" position="0,45" size="560,60" scrollbarMode="showOnDemand" />
		</screen>""" % _("Movielist Preview")

	def __init__(self, session, x, y, w, h):
		Screen.__init__(self, session)

		self["key_green"] = Label(_("OK"))

		self.xEntry = ConfigInteger(default=x, limits=(0, w))
		self.yEntry = ConfigInteger(default=y, limits=(0, h))

		ConfigListScreen.__init__(self, [
			getConfigListEntry("x position:", self.xEntry),
			getConfigListEntry("y position:", self.yEntry)])

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"green": self.ok,
				 "cancel": self.close
			}, -1)

	def ok(self):
		self.close([self.xEntry.value, self.yEntry.value])

##############################################################################

class MovielistPreviewPositioner(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = SKIN
		self["background"] = Label("")
		self["preview"] = Pixmap()

		self["actions"] = ActionMap(["EPGSelectActions", "MenuActions", "WizardActions"],
		{
			"left": self.left,
			"up": self.up,
			"right": self.right,
			"down": self.down,
			"ok": self.ok,
			"back": self.exit,
			"menu": self.editCoordinates,
			"nextBouquet": self.bigger,
			"prevBouquet": self.smaller
		}, -1)

		desktop = getDesktop(0)
		self.desktopWidth = desktop.size().width()
		self.desktopHeight = desktop.size().height()

		self.moveTimer = eTimer()
		self.moveTimer.callback.append(self.movePosition)
		self.moveTimer.start(50, 1)

		self.onShow.append(self.__onShow)

	def __onShow(self):
		if self.instance:
			size = config.plugins.MovielistPreview.size.value.split("x")
			self.instance.resize(eSize(int(size[0]), int(size[1])))
			self["background"].instance.resize(eSize(int(size[0]), int(size[1])))
			self["preview"].instance.resize(eSize(int(size[0]), int(size[1])))

	def movePosition(self):
		self.instance.move(ePoint(config.plugins.MovielistPreview.position_x.value, config.plugins.MovielistPreview.position_y.value))
		self.moveTimer.start(50, 1)

	def left(self):
		value = config.plugins.MovielistPreview.position_x.value
		value -= 1
		if value < 0:
			value = 0
		config.plugins.MovielistPreview.position_x.value = value

	def up(self):
		value = config.plugins.MovielistPreview.position_y.value
		value -= 1
		if value < 0:
			value = 0
		config.plugins.MovielistPreview.position_y.value = value

	def right(self):
		value = config.plugins.MovielistPreview.position_x.value
		value += 1
		if value > self.desktopWidth:
			value = self.desktopWidth
		config.plugins.MovielistPreview.position_x.value = value

	def down(self):
		value = config.plugins.MovielistPreview.position_y.value
		value += 1
		if value > self.desktopHeight:
			value = self.desktopHeight
		config.plugins.MovielistPreview.position_y.value = value

	def ok(self):
		config.plugins.MovielistPreview.position_x.save()
		config.plugins.MovielistPreview.position_y.save()
		self.close()

	def exit(self):
		config.plugins.MovielistPreview.position_x.cancel()
		config.plugins.MovielistPreview.position_y.cancel()
		self.close()

	def editCoordinates(self):
		self.session.openWithCallback(self.editCoordinatesCallback, MovielistPreviewPositionerCoordinateEdit, config.plugins.MovielistPreview.position_x.value, config.plugins.MovielistPreview.position_y.value, self.desktopWidth, self.desktopHeight)

	def editCoordinatesCallback(self, callback=None):
		if callback:
			config.plugins.MovielistPreview.position_x.value = callback[0]
			config.plugins.MovielistPreview.position_y.value = callback[1]

	def bigger(self):
		if config.plugins.MovielistPreview.size.value == "200x160":
			config.plugins.MovielistPreview.size.value = "250x200"
		elif config.plugins.MovielistPreview.size.value == "150x120":
			config.plugins.MovielistPreview.size.value = "200x160"
		elif config.plugins.MovielistPreview.size.value == "100x80":
			config.plugins.MovielistPreview.size.value = "150x120"
		config.plugins.MovielistPreview.size.save()
		self.__onShow()

	def smaller(self):
		if config.plugins.MovielistPreview.size.value == "150x120":
			config.plugins.MovielistPreview.size.value = "100x80"
		elif config.plugins.MovielistPreview.size.value == "200x160":
			config.plugins.MovielistPreview.size.value = "150x120"
		elif config.plugins.MovielistPreview.size.value == "250x200":
			config.plugins.MovielistPreview.size.value = "200x160"
		config.plugins.MovielistPreview.size.save()
		self.__onShow()

##############################################################################

class PreviewCreator:
	def __init__(self):
		self.callback = None
		self.Console = Console()

	def grab(self, file):
		if not self.Console:
			self.Console = Console()
		self.Console.ePopen('/usr/bin/grab -v -r 250 -l -j 100 "%s"'%file, self.grabDone)

	def grabDone(self, result, retval, extra_args):
		if retval != 0:
			print result
		if self.callback:
			self.callback()
previewcreator = PreviewCreator()

##############################################################################

class MovielistPreviewManualCreator(Screen, InfoBarBase, InfoBarSeek, InfoBarCueSheetSupport):
	skin = """
		<screen position="center,center" size="560,380" title="%s">
			<widget name="video" position="100,20" size="360,288" backgroundColor="transparent" />
			<widget source="session.CurrentService" render="PositionGauge" position="145,330" size="270,10" pointer="position_pointer.png:540,0" transparent="1" foregroundColor="#20224f">
				<convert type="ServicePosition">Gauge</convert>
			</widget>
			<widget name="seekState" position="40,320" size="60,25" halign="right" font="Regular;18" valign="center" />
			<ePixmap pixmap="icons/mp_buttons.png" position="225,350" size="109,13" alphatest="on" />
		</screen>""" % _("Movielist Preview")

	def __init__(self, session, service):
		Screen.__init__(self, session)
		InfoBarSeek.__init__(self)
		InfoBarCueSheetSupport.__init__(self)
		InfoBarBase.__init__(self, steal_current_service=True)

		self.session = session
		self.service = service
		self.working = False
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.session.nav.playService(service)
		previewcreator.callback = self.grabDone

		desktopSize = getDesktop(0).size()
		self["video"] = VideoWindow(decoder=0, fb_width=desktopSize.width(), fb_height=desktopSize.height())
		self["seekState"] = Label()

		self.onPlayStateChanged.append(self.updateStateLabel)
		self.updateStateLabel(self.seekstate)

		self["actions"] = ActionMap(["OkCancelActions"],
			{
				"ok": self.grab,
				"cancel": self.exit
			}, -2)

	def checkSkipShowHideLock(self):
		pass

	def updateStateLabel(self, state):
		self["seekState"].setText(state[3].strip())

	def grab(self):
		if not self.working:
			self.working = True
			png = self.service.getPath() + "_mp.jpg"
			previewcreator.grab(png)

	def grabDone(self):
		self.working = False
		self.session.open(MessageBox,_("Preview created."), MessageBox.TYPE_INFO, timeout=5)

	def exit(self):
		if not self.working:
			self.session.nav.playService(self.oldService)
			self.close()

##############################################################################

class MovielistPreviewAutoCreator(Screen):
	skin = """
		<screen position="center,center" size="420,105" title="%s">
			<widget name="label" position="10,10" size="400,85" transparent="1" font="Regular;20" halign="center" valign="center" />
		</screen>""" % _("Movielist Preview")

	def __init__(self, session):
		Screen.__init__(self, session)

		self.session = session
		self.files = []
		self.filescount = 0
		self.current = 1
		self.working = True
		self.abort = False
		self.dir = config.movielist.last_videodir.value
		previewcreator.callback = self.grabDone
		self.playable = ["avi", "dat", "divx", "m2ts", "m4a", "mkv", "mp4", "mov", "mpg", "ts", "vob"]
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()

		self["label"] = Label()

		self.timer = eTimer()
		self.timer.callback.append(self.seekAndCreatePreview)

		self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.exit}, -1)

		self.onLayoutFinish.append(self.createPreviews)

	def exit(self):
		if self.working == False:
			self.session.nav.playService(self.oldService)
			self.close()
		else:
			self.abort = True

	def getExtension(self, name):
		ext = None
		if name.__contains__("."):
			tmp = name.split(".")
			ext = tmp[-1]
		return ext

	def createPreviews(self):
		try:
			files = listdir(self.dir)
		except:
			files = []
		for file in files:
			ext = self.getExtension(file)
			if ext and (ext.lower() in self.playable):
				self.files.append(file)
		self.filescount = len(self.files)
		if self.filescount == 0:
			self["label"].setText(_("Could not find any movie!"))
		else:
			self.createNextPreview()

	def createNextPreview(self):
		if len(self.files):
			file = self.files[0]
			movie = ("%s/%s" % (self.dir, file)).replace("//", "/")
			png = movie + "_mp.jpg"
			if fileExists(png):
				self.grabDone()
			else:
				counter = "%d / %d" % (self.current, self.filescount)
				self["label"].setText(_("%s - creating preview for movie %s") % (counter, movie))
				if movie.endswith(".ts"):
					ref = eServiceReference(1, 0, movie)
				else:
					ref = eServiceReference(4097, 0, movie)
				self.session.nav.playService(ref)
				self.png = png
				self.timer.start(5000, 1)
		else:
			self["label"].setText(_("Everything done ;)"))
			self.working = False

	def seekAndCreatePreview(self):
		service = self.session.nav.getCurrentService()
		if service:
			cue = service and service.cueSheet()
			if cue is not None:
				cue.setCutListEnable(0)
			seek = service.seek()
			if seek:
				length = int(seek.getLength()[1])
				seek.seekTo(random.randint(0, length))
			previewcreator.grab(self.png)
		else:
			self.grabDone()

	def grabDone(self):
		del self.files[0]
		self.current += 1
		if self.abort:
			self["label"].setText(_("Autocreate of previews aborted due user!"))
			self.working = False
		else:
			self.createNextPreview()

##############################################################################

class MovielistPreviewMenu(Screen):
	skin = """
		<screen position="center,center" size="420,105" title="%s">
			<widget name="list" position="5,5" size="410,100" />
		</screen>""" % _("Movielist Preview")

	def __init__(self, session, service):
		Screen.__init__(self, session)
		self.session = session
		self.service = service
		self["list"] = MenuList([])
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)
		self.onLayoutFinish.append(self.showMenu)

	def showMenu(self):
		list = []
		if config.plugins.MovielistPreview.enabled.value:
			list.append(_("Deactivate Movielist Preview"))
		else:
			list.append(_("Activate Movielist Preview"))
		list.append(_("Create preview"))
		list.append(_("Autocreate of missing previews"))
		list.append(_("Change Movielist Preview position"))
		self["list"].setList(list)

	def okClicked(self):
		idx = self["list"].getSelectionIndex()
		if movielistpreview.dialog is None:
			movielistpreview.gotSession(self.session)
		if idx == 0:
			movielistpreview.changeVisibility()
			self.showMenu()
		elif idx == 1:
			movielistpreview.dialog.hide()
			self.session.open(MovielistPreviewManualCreator, self.service)
		elif idx == 2:
			movielistpreview.dialog.hide()
			self.session.open(MovielistPreviewAutoCreator)
		else:
			movielistpreview.dialog.hide()
			self.session.open(MovielistPreviewPositioner)

##############################################################################

SelectionChanged = MovieList.selectionChanged
def selectionChanged(instance):
	SelectionChanged(instance)
	curr = instance.getCurrent()
	if curr and isinstance(curr, eServiceReference):
		movielistpreview.showPreview(curr.getPath())
MovieList.selectionChanged = selectionChanged

Hide = MovieSelection.hide
def hideMovieSelection(instance):
	Hide(instance)
	movielistpreview.hideDialog()
MovieSelection.hide = hideMovieSelection

Show = MovieSelection.show
def showMovieSelection(instance):
	Show(instance)
	movielistpreview.showDialog()
MovieSelection.show = showMovieSelection

##############################################################################

def selectionChanged2(instance):
	SelectionChanged2(instance)
	curr = instance.getCurrent()
	if curr and isinstance(curr, eServiceReference):
		movielistpreview.showPreview(curr.getPath())

def hideMovieSelection2(instance):
	Hide2(instance)
	movielistpreview.hideDialog()

def showMovieSelection2(instance):
	Show2(instance)
	movielistpreview.showDialog()

try:
	from Plugins.Extensions.Suomipoeka.MovieList import MovieList as MovieList2
	from Plugins.Extensions.Suomipoeka.MovieSelection import MovieSelectionSP
	SelectionChanged2 = MovieList2.selectionChanged
	MovieList2.selectionChanged = selectionChanged2
	Hide2 = MovieSelectionSP.hide
	MovieSelectionSP.hide = hideMovieSelection2
	Show2 = MovieSelectionSP.show
	MovieSelectionSP.show = showMovieSelection2
except ImportError:
	print "[Movielist Preview] Could not import Suomipoeka Plugin, maybe not installed or too old version?"

##############################################################################

def sessionstart(reason, **kwargs):
	if reason == 0:
		movielistpreview.gotSession(kwargs["session"])

def main(session, service):
	session.open(MovielistPreviewMenu, service)

##############################################################################

def Plugins(**kwargs):
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
		PluginDescriptor(name=_("Movielist Preview"), description=_("Movielist Preview"), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main)]
