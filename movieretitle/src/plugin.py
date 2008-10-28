from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.LocationBox import MovieLocationBox
import Screens.Standby
from Components.config import *
from Components.ActionMap import ActionMap, NumberActionMap
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.Button import Button
from Components.Label import Label
from Components.Pixmap import Pixmap
from enigma import eTimer, eServiceReference, eServiceCenter, iServiceInformation, eConsoleAppContainer
import os

def main(session, service, **kwargs):
	session.open(MovieRetitle, service, session.current_dialog, **kwargs)

def Plugins(**kwargs):
	return PluginDescriptor(name="MovieRetitle", description=_("Change name..."), where = PluginDescriptor.WHERE_MOVIELIST, fnc=main)


class MovieRetitle(Screen, ConfigListScreen):
	skin = """
	<screen name="TitleDescrInput" position="100,150" size="500,200" title="Name and Description Input">
		<widget name="config" position="10,10" size="480,120" />
		<widget name="ok" position="70,140" size="140,40" pixmap="skin_default/buttons/green.png" alphatest="on" />
		<widget name="oktext" position="70,140" size="140,40" valign="center" halign="center" zPosition="2" font="Regular;20" transparent="1" />
		<widget name="cancel" position="290,140" size="140,40" pixmap="skin_default/buttons/red.png" alphatest="on" />
		<widget name="canceltext" position="290,140" size="140,40" valign="center" halign="center" zPosition="2" font="Regular;20" transparent="1" />
	</screen>"""

	def __init__(self, session, service, parent, args = 0):
		Screen.__init__(self, session)
		self.session = session
		self.service = service
		self.parentscreen = parent
		Screen.__init__(self, session)
		serviceHandler = eServiceCenter.getInstance()
		info = serviceHandler.info(self.service)
		self.path = self.service.getPath()
		if self.path.endswith(".ts") is True:
			self.path = self.path[:-3]
		self.dir = self.dirName(self.path)
		self.file = self.baseName(self.path)
		self.name = info.getName(self.service)
		if self.file == self.baseName(self.name):
			self.title = ""
		else:
			self.title = self.name
		self.descr = info.getInfoString(self.service, iServiceInformation.sDescription)

		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))
		self["ok"] = Pixmap()
		self["cancel"] = Pixmap()

		self.input_file = ConfigText(default = self.file, fixed_size = False, visible_width = 42)
		self.input_title = ConfigText(default = self.title, fixed_size = False, visible_width = 42)
		self.input_descr = ConfigText(default = self.descr, fixed_size = False, visible_width = 42)
		tmp = config.movielist.videodirs.value
		if not self.dir in tmp:
			tmp.append(self.dir)
		self.input_dir = ConfigSelection(choices = tmp, default = self.dir)

		self["actions"] = NumberActionMap(["SetupActions"],
		{
			"ok": self.keySelectOrGo,
			"save": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list)
		self.createSetup(self["config"])

	def createSetup(self, configlist):
		self.list = []
		self.list.append(getConfigListEntry(_("Filename"), self.input_file))
		self.list.append(getConfigListEntry(_("Title"), self.input_title))
		self.list.append(getConfigListEntry(_("Description"), self.input_descr))
		self.list.append(getConfigListEntry(_("Location"), self.input_dir))
		configlist.list = self.list
		configlist.l.setList(self.list)

	def pathSelected(self, res):
		if res is not None:
			if config.movielist.videodirs.value != self.input_dir.choices:
				self.input_dir.setChoices(config.movielist.videodirs.value, default=res)
			self.input_dir.value = res

	def keySelectOrGo(self):
		if self["config"].getCurrent() == self.list[3]:
			self.session.openWithCallback(
				self.pathSelected,
				MovieLocationBox,
				_("Choose target folder"),
				self.input_dir.value,
			)
		else:
			self.keyGo()

	def keyGo(self):
		if self.input_title.value != self.title or self.input_descr.value != self.descr:
			self.setTitleDescr(self.path, self.input_title.value, self.input_descr.value)
		if self.input_file.value != self.file or self.input_dir.value != self.dir:
			self.maybeMoveMovieFiles(self.path, self.rejoinName(self.input_dir.value, self.input_file.value))
		else:
			self.exitDialog()

	def keyCancel(self):
		self.close()

	def setTitleDescr(self, file, title, descr):
		if os.path.exists(file + ".ts.meta"):
			metafile = open(file + ".ts.meta", "r")
			sid = metafile.readline()
			oldtitle = metafile.readline().rstrip()
			olddescr = metafile.readline().rstrip()
			rest = metafile.read()
			metafile.close()
			if not title and title != "":
				title = oldtitle
			if not descr and descr != "":
				descr = olddescr
			metafile = open(file + ".ts.meta", "w")
			metafile.write("%s%s\n%s\n%s" %(sid, title, descr, rest))
			metafile.close()

	def maybeMoveMovieFiles(self, fr, to):
		if os.path.exists(to+".ts"):
			self.inter_fr = fr
			self.inter_to = to
			self.session.openWithCallback(self.confirmedReplace, MessageBox, _("Target file %s.ts already exist.\nDo you want to replace it?") % (to), MessageBox.TYPE_YESNO)
		elif os.path.isdir(os.path.dirname(to)):
			self.moveMovieFiles(fr, to)
		else:
			self.session.openWithCallback(self.exitDialog, MessageBox, _("The target directory is not found. The file is not renamed."), MessageBox.TYPE_ERROR) 

	def confirmedReplace(self, answer):
		if answer == True:
			self.moveMovieFiles(self.inter_fr, self.inter_to)

	def moveMovieFiles(self, fr, to):
		try:
			os.rename(fr + ".ts", to + ".ts")
		except OSError:
			print "Moving in background"
			global_background_mover.enqueue(self.exitDialog, self.session, fr, to)
		else:
			print "Moving in foreground"
			for suff in [".ts.meta", ".ts.cuts", ".ts.ap", ".eit"]:
				if os.path.exists(fr + suff):
					os.rename(fr + suff, to + suff)
			self.exitDialog()

	def exitDialog(self, dummy=None):
		self.close()
		# This will try to get back to an updated movie list.
		# A proper way to do this should be provided in enigma2.
		try:
			self.parentscreen.csel.reloadList()
			self.parentscreen.close()
		except AttributeError:
			pass

	def baseName(self, str):
		name = str.split('/')[-1]
		if name.endswith(".ts") is True:
			return name[:-3]
		else:
			return name

	def dirName(self, str):
		return '/'.join(str.split('/')[:-1]) + '/'

	def rejoinName(self, dir, name):
		name = name.strip()
		if name.endswith(".ts") is True:
			return dir + name[:-3]
		else:
			return dir + name

class MovieRetitleBackgroundMover:
	def __init__(self):
		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.moveNextSuffBG)
		self.currid = 0;
		self.queue = []
		self.running = False
		self.messageQueue = []
		self.messageTimer = eTimer()
		self.messageTimer.callback.append(self.tryLaunchMessage)

	def message(self, session, id, cb, txt):
		global global_message_block
		done = False
		if global_message_block and global_message_block == id:
			self.messageQueue = [(session, id, txt)] + self.messageQueue
		else:
			i = 0
			for ele in self.messageQueue:
				if ele[1] == id:
					self.messageQueue[i] = (session, id, txt)
					done = True
					break
				i += 1
			if not done:
				self.messageQueue.append((session, id, txt))
		self.tryLaunchMessage(callback = cb)

	def tryLaunchMessage(self, dummy=0, callback = None):
		global global_message_block
		self.messageTimer.stop()
		if not self.messageQueue:
			if callback:
				callback()
		elif not Screens.Standby.inStandby and self.messageQueue[0][0].in_exec and (not global_message_block or global_message_block == self.messageQueue[0][1]):
			self.messageTimer.stop()
			session = self.messageQueue[0][0]
			id = self.messageQueue[0][1]
			mess = self.messageQueue[0][2]
			self.messageQueue = self.messageQueue[1:]
			if global_message_block == id:
				closeprev = session.current_dialog
			else:
				closeprev = None
			global_message_block = id
			try:
				session.openWithCallback(lambda x: self.tryLaunchMessageCallback(callback, closeprev), MessageBox, mess, MessageBox.TYPE_INFO)
			except:
				global_message_block = False
				self.tryLaunchMessage()
		else:
			self.messageTimer.start(1500, True)
			if callback:
				callback()

	def tryLaunchMessageCallback(self, callback, closeprev):
		global global_message_block
		global_message_block = False
		if closeprev:
			closeprev.close(True)
		self.tryLaunchMessage(callback = callback)

	def enqueue(self, cb, session, fr, to):
		self.currid += 1
		mess = _("The movie is moved in the background from %s to %s.") % (os.path.dirname(fr), os.path.dirname(to))
		self.message(session, self.currid, cb, mess)
		self.queue.append((session, self.currid, fr, to))
		if not self.running:
			self.running = True
			self.runNext()
			return True
		else:
			return False

	def runNext(self):
		if not self.queue:
			self.running = False
		else:
			self.moveMovieFilesBackground(self.queue[0])

	def runDone(self, retval):
		ele = self.queue[0]
		self.queue = self.queue[1:]
		self.runNext()

	def moveMovieFilesBackground(self, ele):
		self.ele = ele
		self.sufflst = [".ts.meta", ".ts.cuts", ".ts.ap", ".eit", ".ts"]
		self.sufflst2 = self.sufflst
		self.moveNextSuffBG(0)

	def moveNextSuffBG(self, retval):
		if self.sufflst and not retval:
			fr = self.ele[2] + self.sufflst[0]
			to = self.ele[3] + self.sufflst[0]
			self.sufflst = self.sufflst[1:]
			print "Moving %s to %s" % (fr, to)
			if os.path.exists(fr):
				self.container.execute("/bin/cp", ["/bin/cp", fr, to])
			else:
				self.moveNextSuffBG(0)
		elif retval:
			for suff in self.sufflst2:
				if os.path.exists(self.ele[3] + suff) and os.path.exists(self.ele[2] + suff):
					os.unlink(self.ele[3] + suff)
			mess = "Failed to move the movie %s to %s in the background" % (self.ele[2], self.ele[3])
			self.message(self.ele[0], self.ele[1], None, mess)
			self.runDone(1)
		else:
			for suff in self.sufflst2:
				if os.path.exists(self.ele[2] + suff) and os.path.exists(self.ele[3] + suff):
					os.unlink(self.ele[2] + suff)
			mess = "Successfully moved the movie %s" % (self.ele[2])
			self.message(self.ele[0], self.ele[1], None, mess)
			self.runDone(0)

global_background_mover = MovieRetitleBackgroundMover()

global_message_block = False

