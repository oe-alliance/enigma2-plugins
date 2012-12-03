##
## DVD Backup plugin for enigma2 by AliAbdul
## using the great open source dvdbackup by Olaf Beck
##
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigText, ConfigYesNo, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Console import Console as eConsole
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryProgress
from Components.Scanner import Scanner, ScanPath
from enigma import eListboxPythonMultiContent, eTimer, gFont, RT_HALIGN_CENTER
from fcntl import ioctl
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console as ConsoleScreen
from Screens.LocationBox import LocationBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from time import time
from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists, resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
import gettext, os, stat

#################################################

PluginLanguageDomain = "DVDBackup"
PluginLanguagePath = "Extensions/DVDBackup/locale/"
 
def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

#################################################

config.plugins.DVDBackup = ConfigSubsection()
config.plugins.DVDBackup.device = ConfigText(default="/dev/sr0", fixed_size=False)
config.plugins.DVDBackup.directory = ConfigText(default="/hdd/movie", fixed_size=False)
config.plugins.DVDBackup.name = ConfigText(default=_("Name of DVD"), fixed_size=False)
config.plugins.DVDBackup.log = ConfigYesNo(default=True)
config.plugins.DVDBackup.create_iso = ConfigYesNo(default=False)

#################################################

global SESSION
SESSION = None

def message(msg):
	SESSION.open(MessageBox, msg, type=MessageBox.TYPE_ERROR, timeout=10)

#################################################

def eject(dev):
	try:
		cd = open(dev)
		ioctl_flag = int(0x5307)
		ioctl(cd.fileno(), ioctl_flag)
		ioctl_flag = int(0x5329)
		ioctl(cd.fileno(), ioctl_flag)
		ioctl_flag = int(0x5309)
		ioctl(cd.fileno(), ioctl_flag)
		cd.close()
	except IOError, err:
		print err

#################################################

class DVDBackupFile:
	def __init__(self, name, size):
		self.name = name
		if name != "genisoimage":
			self.name = ("%s/%s/%s"%(config.plugins.DVDBackup.directory.value, config.plugins.DVDBackup.name.value, name)).replace("//", "/")
		self.size = size
		self.progress = 0

	def checkProgress(self):
		if self.name != "genisoimage":
			if fileExists(self.name):
				if self.progress < 100:
					file_stats = os.stat(self.name)
					self.progress = 100.0 * file_stats[stat.ST_SIZE] / self.size
			else:
				self.progress = 0

#################################################

class DVDBackup:
	def __init__(self):
		self.console = None
		self.working = False
		self.startTime = None
		self.files = []

	def backup(self):
		self.working = True
		self.startTime = time()
		del self.files
		self.files = []
		self.getInfo()

	def getInfo(self):
		if not self.console:
			self.console = eConsole()
		self.console.ePopen("dvdbackup --info -i %s"%config.plugins.DVDBackup.device.value, self.gotInfo)

	def gotInfo(self, result, retval, extra_args):
		if result and result.__contains__("File Structure DVD") and result.__contains__("Main feature:"):
			result = result[result.index("File Structure DVD"): result.index("Main feature:")]
			lines = result.split("\n")
			folder = ""
			for line in lines:
				tmp = line.split("\t")
				if len(tmp) == 1:
					folder = tmp[0]
				elif len(tmp) == 4:
					name = folder+tmp[1]
					size = tmp[2]
					if size.__contains__("."):
						size = size[:size.index(".")]
					if not name.__contains__("VTS_00_0."):
						self.files.append(DVDBackupFile(name, int(size)))
			if len(self.files) > 0:
				if not self.console:
					self.console = eConsole()
				if config.plugins.DVDBackup.log.value:
					log = " 2>> /tmp/dvdbackup.log"
				else:
					log = ""
				cmd = 'dvdbackup -M -v -i %s -o "%s" -n "%s"%s'%(config.plugins.DVDBackup.device.value, config.plugins.DVDBackup.directory.value, config.plugins.DVDBackup.name.value, log)
				self.console.ePopen(cmd, self.dvdbackupFinished)
			else:
				message(_("Could not find any file to backup!"))
				self.working = False
		else:
			message(_("Could not read the DVD informations!"))
			print "[DVD Backup]",result
			self.working = False

	def dvdbackupFinished(self, result, retval, extra_args):
		if retval != 0:
			message(_("Error while backup of DVD!"))
			print "[DVD Backup]", retval, result
			self.working = False
		else:
			if config.plugins.DVDBackup.create_iso.value:
				path = ("%s/%s"%(config.plugins.DVDBackup.directory.value, config.plugins.DVDBackup.name.value)).replace("//", "/")
				if not self.console:
					self.console = eConsole()
				self.genisoimage = DVDBackupFile("genisoimage", 0)
				self.files.append(self.genisoimage)
				cmd = 'genisoimage -dvd-video -udf -o "%s.iso" "%s"'%(path, path)
				self.console.ePopen(cmd, self.genisoimageCallback)
				self.console.appContainers[cmd].dataAvail.append(boundFunction(self.genisoimageProgress, cmd))
			else:
				self.finished()

	def genisoimageProgress(self, name, data):
		if data.__contains__("%"):
			for x in data.split("\n"):
				if x.__contains__("%"):
					x = x[:x.index("%")]
					if x.__contains__("."):
						x = x[:x.index(".")]
					x = x.replace(" ", "")
					if x != "":
						self.genisoimage.progress = int(x)

	def genisoimageCallback(self, result, retval, extra_args):
		if retval != 0:
			message(_("Error while backup of DVD!"))
			print "[DVD Backup]", result
			self.working = False
		else:
			self.genisoimage.progress = 100
			SESSION.openWithCallback(self.genisoimageCallback2, MessageBox, _("genisoimage job done.\nDelete DVD directory?"))

	def genisoimageCallback2(self, yesno):
		if yesno:
			cmd = ("rm -R %s/%s"%(config.plugins.DVDBackup.directory.value, config.plugins.DVDBackup.name.value)).replace("//", "/")
			try: os.system(cmd)
			except: pass
		self.finished()

	def finished(self):
		seconds = int(time() - self.startTime)
		minutes = 0
		while seconds > 60:
			seconds -= 60
			minutes += 1
		SESSION.openWithCallback(self.eject, MessageBox, "%s\n%s %d:%02d\n\n%s"%(_("Backup of DVD finished."), _("Duration:"), minutes, seconds, _("Eject DVD?")))

	def eject(self, yesno):
		if yesno:
			eject(config.plugins.DVDBackup.device.value)
		self.working = False

dvdbackup = DVDBackup()

#################################################

class DVDBackupList(MenuList):
	def __init__(self):
		MenuList.__init__(self, [], False, eListboxPythonMultiContent)
		self.l.setItemHeight(25)
		self.l.setFont(0, gFont("Regular", 20))

#################################################

def DVDBackupListEntry(file):
	res = [(file)]
	res.append(MultiContentEntryText(pos=(0, 0), size=(180, 25), font=0, text=file.name.split("/")[-1]))
	res.append(MultiContentEntryText(pos=(200, 0), size=(120, 25), font=0, text="%d %s"%((file.size / 1024) / 1024, "MB"), flags=RT_HALIGN_CENTER))
	res.append(MultiContentEntryProgress(pos=(340, 9), size=(100, 7), percent=file.progress, borderWidth=1))
	res.append(MultiContentEntryText(pos=(460, 0), size=(60, 25), font=0, text="%d%s"%(file.progress, "%"), flags=RT_HALIGN_CENTER))
	return res

#################################################

class DVDBackupProgress(Screen):
	skin = """
	<screen position="center,center" size="560,450" title="DVD Backup">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="list" position="0,45" size="560,400" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		
		self.refreshTimer = eTimer()
		self.refreshTimer.callback.append(self.refreshList)
		
		self.console = None
		self.working = False
		
		self["key_red"] = Label(_("Abort"))
		self["list"] = DVDBackupList()
		
		self["actions"] = ActionMap(["ColorActions", "OkCancelActions"],
			{
				"cancel": self.exit,
				"red": self.abort
			}, -1)
		
		self.onLayoutFinish.append(self.refreshList)

	def exit(self):
		if self.working == False:
			self.refreshTimer.stop()
			self.close()

	def refreshList(self):
		list = []
		tostart = []
		finished = []
		for file in dvdbackup.files:
			file.checkProgress()
			if file.progress == 0:
				tostart.append(DVDBackupListEntry(file))
			elif file.progress == 100:
				finished.append(DVDBackupListEntry(file))
			else:
				list.append(DVDBackupListEntry(file))
		for x in tostart:
			list.append(x)
		for x in finished:
			list.append(x)
		self["list"].setList(list)
		self.refreshTimer.start(3000, 1)

	def abort(self):
		if self.working == False and dvdbackup.working:
			self.working = True
			if not self.console:
				self.console = eConsole()
			tool = "dvdbackup"
			for file in dvdbackup.files:
				if file.name == "genisoimage":
					tool = "genisoimage"
			self.console.ePopen("killall -9 %s"%tool, self.abortCallback)

	def abortCallback(self, result, retval, extra_args):
		self.working = False

#################################################

class DVDBackupScreen(ConfigListScreen, Screen):
	skin = """
	<screen position="center,center" size="560,175" title="DVD Backup">
		<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
		<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
		<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
		<widget name="config" position="0,45" size="560,125" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, device=None):
		Screen.__init__(self, session)
		
		self.working = False
		self.session = session
		self.console = None
		
		self["key_red"] = Label(_("Progress"))
		self["key_green"] = Label(_("Backup"))
		self["key_yellow"] = Label(_("Keyboard"))
		self["key_blue"] = Label(_("Location"))
		
		if device:
			config.plugins.DVDBackup.device.value = device
		
		ConfigListScreen.__init__(self, [
			getConfigListEntry(_("Device:"), config.plugins.DVDBackup.device),
			getConfigListEntry(_("Directory:"), config.plugins.DVDBackup.directory),
			getConfigListEntry(_("Name:"), config.plugins.DVDBackup.name),
			getConfigListEntry(_("Log:"), config.plugins.DVDBackup.log),
			getConfigListEntry(_("Create iso:"), config.plugins.DVDBackup.create_iso)])
		
		self["actions"] = ActionMap(["ColorActions", "OkCancelActions"],
			{
				"red": self.progress,
				"green": self.backup,
				"yellow": self.keyboard,
				"blue": self.location,
				"cancel": self.exit
			}, -1)
		
		self["config"].onSelectionChanged.append(self.checkConfig)
		self.onLayoutFinish.append(self.getName)

	def progress(self):
		if self.working == False:
			self.session.open(DVDBackupProgress)

	def backup(self):
		if self.working == False:
			for x in self["config"].list:
				x[1].save()
			dvdbackup.backup()
			self.session.openWithCallback(self.close, DVDBackupProgress)

	def exit(self):
		if self.working == False:
			for x in self["config"].list:
				x[1].cancel()
			self.close()

	def checkConfig(self):
		current = self["config"].getCurrent()
		key = current and current[1]
		if isinstance(key, ConfigText):
			self["key_yellow"].show()
		else:
			self["key_yellow"].hide()

	def keyboard(self):
		if self.working == False:
			current = self["config"].getCurrent()
			self.toChange = current and current[1]
			if isinstance(self.toChange, ConfigText):
				self.session.openWithCallback(self.keyBoardCallback, VirtualKeyBoard, current and current[0], self.toChange.value)

	def keyBoardCallback(self, callback=None):
		if callback:
			self.toChange.value = callback
			self["config"].setList(self["config"].getList())

	def getName(self):
		self.working = True
		if not self.console:
			self.console = eConsole()
		self.console.ePopen("dvdbackup --info -i %s"%config.plugins.DVDBackup.device.value, self.gotInfo)

	def location(self):
		self.session.openWithCallback(self.locationCallback, LocationBox)

	def locationCallback(self, callback):
		if callback:
			config.plugins.DVDBackup.directory.value = callback
			self["config"].setList(self["config"].getList())

	def gotInfo(self, result, retval, extra_args):
		config.plugins.DVDBackup.name.value = _("Name of DVD")
		if result:
			lines = result.split("\n")
			for line in lines:
				if line.startswith("DVD-Video information of the DVD with title "):
					idx = line.index("title ")
					config.plugins.DVDBackup.name.value = line[idx+6:]
					break
		self["config"].setList(self["config"].getList())
		self.working = False

#################################################

def main(session, **kwargs):
	global SESSION
	SESSION = session
	if dvdbackup.working:
		session.open(DVDBackupProgress)
	else:
		session.open(DVDBackupScreen)

def filescan_open(list, session, **kwargs):
	global SESSION
	SESSION = session
	if len(list) == 1 and list[0].mimetype == "video/x-dvd":
		splitted = list[0].path.split('/')
		if len(splitted) > 2:
			if splitted[1] == 'autofs':
				session.open(DVDBackupScreen, device="/dev/%s"%(splitted[2]))
				return

def filescan(**kwargs):
	class LocalScanner(Scanner):
		def checkFile(self, file):
			return fileExists(file.path)
	return [LocalScanner(mimetypes=["video/x-dvd"], paths_to_scan=[ScanPath(path="video_ts", with_subdirs=False)], name="DVD", description=_("DVD Backup"), openfnc=filescan_open)]		

def Plugins(**kwargs):
	return [PluginDescriptor(name=_("DVD Backup"), description=_("Backup your Video-DVD to your harddisk"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="DVDBackup.png", fnc=main),
		PluginDescriptor(where=PluginDescriptor.WHERE_FILESCAN, fnc=filescan)]
