from os import access, chmod, X_OK
from os.path import getsize
from enigma import eEnv, eServiceCenter, iServiceInformation, eTimer

from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigNothing, ConfigSelection, ConfigText
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.Task import Job, job_manager as JobManager, Task
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.LocationBox import MovieLocationBox
from .__init__ import _

mcut_path = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/MovieCut/bin/mcut")


def main(session, service, **kwargs):
	# Hack to make sure it is executable
	if not access(mcut_path, X_OK):
		chmod(mcut_path, 493)
	session.open(MovieCut, service, **kwargs)


def Plugins(**kwargs):
	return PluginDescriptor(name="MovieCut", description=_("Execute cuts..."), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main)


import struct
cutsParser = struct.Struct('>QI')  # big-endian, 64-bit PTS and 32-bit type


def _getCutsLength(filename, len_sec):
	len_pts = in_pts = 0
	try:
		with open(filename + '.cuts', 'rb') as f:
			while True:
				data = f.read(cutsParser.size)
				if len(data) < cutsParser.size:
					break
				pts, cutType = cutsParser.unpack(data)
				if cutType == 0:  # In cut
					if not in_pts:
						in_pts = pts
				elif cutType == 1:  # Out cut
					if in_pts is not None:
						len_pts += pts - in_pts
						in_pts = None
			if in_pts is not None and len_sec:
				len_pts += len_sec * 90000 - in_pts
	except Exception:
		pass
	return len_pts / 90000


class MovieCut(ChoiceBox):
	def __init__(self, session, service):
		self.service = service
		serviceHandler = eServiceCenter.getInstance()
		self.path = self.service.getPath()
		info = serviceHandler.info(self.service)
		if not info:
			self.name = self.path
			self.len = 0
		else:
			self.name = info.getName(self.service)
			self.len = info.getLength(self.service)
		tlist = [
			(_("Don't cut"), "CALLFUNC", self.confirmed0),
			(_("Replace the original movie with the cut movie"), "CALLFUNC", self.confirmed1),
			(_("Place the cut movie in a new file ending with \" cut\""), "CALLFUNC", self.confirmed2),
			(_("Advanced cut specification..."), "CALLFUNC", self.confirmed3),
		]
		ChoiceBox.__init__(self, session, _("How would you like to cut \"%s\"?") % (self.name), list=tlist)
		self.skinName = "ChoiceBox"

	def confirmed0(self, arg):
		self.close()

	def confirmed1(self, arg):
		self.cut(self.name, self.path, self.path[:-3] + '.tmpcut.ts', self.len, _getCutsLength(self.path, self.len), ["-r", self.path])

	def confirmed2(self, arg):
		self.cut(self.name, self.path, self.path[:-3] + ' cut.ts', self.len, _getCutsLength(self.path, self.len), [self.path])

	def confirmed3(self, arg):
		serviceHandler = eServiceCenter.getInstance()
		info = serviceHandler.info(self.service)
		path = self.path
		self.name = info.getName(self.service)
		descr = info.getInfoString(self.service, iServiceInformation.sDescription)
		self.session.openWithCallback(self.advcutConfirmed, AdvancedCutInput, self.name, path, descr)

	def advcutConfirmed(self, ret):
		if len(ret) <= 1 or not ret[0]:
			self.close()
			return
		clist = []
		if ret[1] is True:
			clist.append("-r")
		clist.append(self.path)
		if ret[2] is not False:
			clist += ["-o", ret[2]]
			outpath = ret[2]
		elif ret[1] is True:
			outpath = self.path[:-3] + '.tmpcut.ts'
		else:
			outpath = self.path[:-3] + ' cut.ts'
		if ret[3] is not False:
			clist += ["-n", ret[3]]
		if ret[4] is not False:
			clist += ["-d", ret[4]]
		if ret[5] is not False:
			clist.append("-c")
			clist += ret[5]
			cut_len = 0
			in_t = None
			try:
				for t in ret[5]:
					tt = t.split(':')
					if len(tt) == 3:
						tt = int(tt[0]) * 3600 + int(tt[1]) * 60 + float(tt[2])
					elif len(tt) == 2:
						tt = int(tt[0]) * 60 + float(tt[1])
					elif len(tt) == 1:
						tt = float(tt[0])
					else:
						cut_len = 0
						break
					if not in_t:
						in_t = t
					else:
						cut_len += tt - in_t
						in_t = None
				if in_t or cut_len > self.len:
					cut_len = 0
			except Exception:
				cut_len = 0
		else:
			cut_len = _getCutsLength(self.path, self.len)
		self.cut(self.name, self.path, outpath, self.len, cut_len, clist)

	def cut(self, name, inpath, outpath, inlen, outlen, clist):
		job = Job(_("Execute cuts"))
		CutTask(job, self.session, name, inpath, outpath, inlen, outlen, mcut_path, clist)
		JobManager.AddJob(job, onFail=self.noFail)
		self.close()

	# Prevent the normal aborted notification, using our own from cleanup.
	def noFail(self, job, task, problems):
	    return False


class CutTask(Task):
	def __init__(self, job, session, name, inpath, outpath, inlen, outlen, cmd, args):
		Task.__init__(self, job, name)
		self.session = session
		self.name = name
		self.inpath = inpath
		self.outpath = outpath
		self.inlen = inlen
		self.outlen = outlen
		self.setCommandline(cmd, [cmd] + args)
		self.progressTimer = eTimer()
		self.progressTimer.callback.append(self.progressUpdate)

	def prepare(self):
		if self.inlen and self.outlen:
			try:
				self.end = getsize(self.inpath) * self.outlen / self.inlen
				self.end += self.end / 50  # add 2% for a bit of leeway
				self.progressTimer.start(1000)
			except Exception:
				pass

	def progressUpdate(self):
		try:
			self.setProgress(getsize(self.outpath))
		except Exception:
			pass

	def afterRun(self):
		self.progressTimer.stop()
		self.setProgress(self.end)

	def cleanup(self, failed):
		if failed or not 0 <= self.returncode <= 10:
			self.returncode = 11

		msg = (_("The movie \"%s\" is successfully cut"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Bad arguments"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Couldn't open input .ts file"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Couldn't open input .cuts file"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Couldn't open input .ap file"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Couldn't open output .ts file"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Couldn't open output .cuts file"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Couldn't open output .ap file"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Empty .ap file"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("No cuts specified"),
			   _("Cutting failed for movie \"%s\"") + ":\n" + _("Read/write error (disk full?)"),
			   _("Cutting was aborted for movie \"%s\""))[self.returncode]
		self.session.open(MessageBox, msg % self.name, type=MessageBox.TYPE_ERROR if self.returncode else MessageBox.TYPE_INFO, timeout=10)


class AdvancedCutInput(ConfigListScreen, Screen):
	def __init__(self, session, name, path, descr):
		Screen.__init__(self, session)
		self.skinName = ["AdvancedCutInput", "Setup"]

		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))

		if self.baseName(path) == self.baseName(name):
			title = ""
		else:
			title = name
		dir = self.dirName(path)
		file = self.baseName(path) + " cut"
		self.input_replace = ConfigSelection(choices=[("no", _("No")), ("yes", _("Yes"))], default="no")
		self.input_file = ConfigText(default=file, fixed_size=False, visible_width=45)
		self.input_title = ConfigText(default=title, fixed_size=False, visible_width=45)
		self.input_descr = ConfigText(default=descr, fixed_size=False, visible_width=45)
		tmp = config.movielist.videodirs.value
		if dir not in tmp:
			tmp.append(dir)
		self.input_dir = ConfigSelection(choices=tmp, default=dir)
		self.input_manual = ConfigSelection(choices=[("no", _("Cutlist")), ("yes", _("Manual specification"))], default="no")
		self.input_space = ConfigNothing()
		self.input_manualcuts = ConfigText(default="", fixed_size=False)
		self.input_manualcuts.setUseableChars(" 0123456789:.")

		self["actions"] = ActionMap(["SetupActions"],
		{
			"ok": self.keySelectOrGo,
			"save": self.keyGo,
			"cancel": self.keyCancel,
		}, -2)

		self.list = []
		ConfigListScreen.__init__(self, self.list)
		self.entry_replace = getConfigListEntry(_("Replace original:"), self.input_replace)
		self.entry_file = getConfigListEntry(_("New filename:"), self.input_file)
		self.entry_title = getConfigListEntry(_("New title:"), self.input_title)
		self.entry_descr = getConfigListEntry(_("New description:"), self.input_descr)
		self.entry_dir = getConfigListEntry(_("New location:"), self.input_dir)
		self.entry_manual = getConfigListEntry(_("Cut source:"), self.input_manual)
		self.entry_space = getConfigListEntry(_("Cuts (an IN OUT IN OUT ... sequence of hour:min:sec)"), self.input_space)
		self.entry_manualcuts = getConfigListEntry(":", self.input_manualcuts)
		self.createSetup(self["config"])

		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.setTitle(_("Cut Parameter Input"))

	def createSetup(self, configlist):
		items = [
			self.entry_replace
		]
		if self.input_replace.value == "no":
			items.extend((
				self.entry_file,
				self.entry_dir,
			))
		items.extend((
			self.entry_title,
			self.entry_descr,
			self.entry_manual,
		))
		if self.input_manual.value == "yes":
			items.extend((
				self.entry_space,
				self.entry_manualcuts,
			))
		self.list = items
		configlist.list = items
		configlist.l.setList(items)

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		cc = self["config"].getCurrent()
		if cc is self.entry_replace or cc is self.entry_manual:
			self.createSetup(self["config"])

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		cc = self["config"].getCurrent()
		if cc is self.entry_replace or cc is self.entry_manual:
			self.createSetup(self["config"])

	def pathSelected(self, res):
		if res is not None:
			if config.movielist.videodirs.value != self.input_dir.choices:
				self.input_dir.setChoices(config.movielist.videodirs.value, default=res)
			self.input_dir.value = res

	def keySelectOrGo(self):
		if self["config"].getCurrent() == self.entry_dir:
			self.session.openWithCallback(
				self.pathSelected,
				MovieLocationBox,
				_("Choose target folder"),
				self.input_dir.value,
			)
		else:
			self.keyGo()

	def keyGo(self):
		if self.input_replace.value == "yes":
			path = False
		else:
			path = self.rejoinName(self.input_dir.value, self.input_file.value)
		if self.input_manual.value == "no":
			cuts = False
		else:
			cuts = self.input_manualcuts.value.split(' ')
			while "" in cuts:
				cuts.remove("")
		self.close((True, self.input_replace.value == "yes", path, self.input_title.value, self.input_descr.value, cuts))

	def keyCancel(self):
		self.close((False,))

	def baseName(self, str):
		name = str.split('/')[-1]
		if name.endswith(".ts"):
			return name[:-3]
		elif name.endswith(".stream"):
			return name[:-7]
		else:
			return name

	def dirName(self, str):
		return '/'.join(str.split('/')[:-1]) + '/'

	def rejoinName(self, dir, name):
		name = name.strip()
		if name.endswith(".ts"):
			return dir + name[:-3]
		elif name.endswith(".stream"):
			return dir + name[:-7]
		else:
			return dir + name
