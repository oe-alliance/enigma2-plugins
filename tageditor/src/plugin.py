# for localized messages
from . import _

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Components.config import config
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Components.SelectionList import SelectionList
from enigma import eServiceReference, eServiceCenter, iServiceInformation
from os import path as os_path

def main(session, service, **kwargs):
	session.open(MovieTagEditor, service, session.current_dialog, **kwargs)

def Plugins(**kwargs):
	try:
		from Screens.MovieSelection import setPreferredTagEditor
		setPreferredTagEditor(TagEditor)
	except Exception:
		pass
	# TRANSLATORS: this is the string used in the movie context menu for TagEditor
	return PluginDescriptor(name="TagEditor", description=_("edit tags"), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main, needsRestart=False)

class TagEditor(Screen):
	skin = """
	<screen name="TagEditor" position="center,center" size="600,310">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<ePixmap position="562,10" size="35,25" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
		<widget name="list" position="5,40" size="590,270" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session, tags, txt=None, args=0, parent=None):
		Screen.__init__(self, session, parent=parent)

		# Initialize Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		self["key_yellow"] = StaticText(_("New"))
		self["key_blue"] = StaticText(_("Load"))

		self["list"] = SelectionList()

		allTags = self.loadTagsFile()
		self.joinTags(allTags, tags)
		self.updateMenuList(allTags, tags)

		self.ghostlist = tags[:]
		self.ghosttags = allTags[:]
		self.origtags = allTags[:]
		self.tags = allTags

		# Define Actions
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MenuActions"],
		{
			"ok": self["list"].toggleSelection,
			"cancel": self.cancel,
			"red": self.cancel,
			"green": self.accept,
			"yellow": self.addCustom,
			"blue": self.loadFromHdd,
			"menu": self.showMenu
		}, -1)

		self.onLayoutFinish.append(self.setCustomTitle)

	def setCustomTitle(self):
		# TRANSLATORS: This is the title of the TagEditor main screen
		self.setTitle(_("Edit Tags"))

	def addCustom(self):
		self.session.openWithCallback(
			self.addCustomCallback,
			InputBox,
			title=_("Please enter the new tag")
		)

	def addCustomCallback(self, ret):
		ret = ret and ret.strip().replace(" ", "_").capitalize()
		tags = self.tags
		if ret and ret not in tags:
			tags.append(ret)
			self.updateMenuList(tags, [ret])

	def loadTagsFile(self):
		try:
			file = open("/etc/enigma2/movietags")
			tags = [x.rstrip() for x in file]
			while "" in tags:
				tags.remove("")
			file.close()
		except IOError as ioe:
			tags = []
		return tags

	def saveTagsFile(self, tags):
		try:
			file = open("/etc/enigma2/movietags", "w")
			file.write("\n".join(tags)+"\n")
			file.close()
		except IOError as ioe:
			pass

	def joinTags(self, taglist, newtags):
		for tag in newtags:
			if not tag in taglist:
				taglist.append(tag)

	def setTimerTags(self, timer, tags):
		if timer.tags != tags:
			timer.tags = tags
			self.timerdirty = True

	def setMovieTags(self, ref, tags):
		file = ref.getPath()
		if file.endswith(".ts"):
			file = file + ".meta"
		else:
			file = file + ".ts.meta"
		if os_path.exists(file):
			metafile = open(file, "r")
			sid = metafile.readline()
			title = metafile.readline()
			descr = metafile.readline()
			time = metafile.readline()
			oldtags = metafile.readline().rstrip()
			metafile.close()
			tags = " ".join(tags)
			if tags != oldtags:
				metafile = open(file, "w")
				metafile.write("%s%s%s%s%s" %(sid, title, descr, time, tags))
				metafile.close()

	def foreachTimerTags(self, func):
		self.timerdirty = False
		for timer in self.session.nav.RecordTimer.timer_list + self.session.nav.RecordTimer.processed_timers:
			if timer.tags:
				func(timer, timer.tags[:])
		if self.timerdirty:
			self.session.nav.RecordTimer.saveTimer()

	def foreachMovieTags(self, func):
		serviceHandler = eServiceCenter.getInstance()
		for dir in config.movielist.videodirs.value:
			if os_path.isdir(dir):
				root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + dir)
				list = serviceHandler.list(root)
				if list is None:
					continue
				while True:
					serviceref = list.getNext()
					if not serviceref.valid():
						break
					if (serviceref.flags & eServiceReference.mustDescent):
						continue
					info = serviceHandler.info(serviceref)
					if info is None:
						continue
					tags = info.getInfoString(serviceref, iServiceInformation.sTags).split(' ')
					if not tags or tags == ['']:
						continue
					func(serviceref, tags)

	def updateMenuList(self, tags, extrasel=[]):
		seltags = [x[1] for x in self["list"].getSelectionsList()] + extrasel
		tags.sort()
		self["list"].setList([])
		for tag in tags:
			self["list"].addSelection(tag, tag, 0, tag in seltags)

	def loadFromHdd(self):
		tags = self.tags[:]
		self.foreachTimerTags(lambda t, tg: self.joinTags(tags, tg))
		self.foreachMovieTags(lambda r, tg: self.joinTags(tags, tg))
		self.updateMenuList(tags)
		self.tags = tags

	def removeUnused(self):
		tags = [x[1] for x in self["list"].getSelectionsList()]
		self.foreachTimerTags(lambda t, tg: self.joinTags(tags, tg))
		self.foreachMovieTags(lambda r, tg: self.joinTags(tags, tg))
		self.updateMenuList(tags)
		self.tags = tags

	def listReplace(self, lst, fr, to=None):
		if fr in lst:
			lst.remove(fr)
			if to != None and not to in lst:
				lst.append(to)
				lst.sort()
		return lst

	def renameTag(self):
		self.thistag = self["list"].list[self["list"].getSelectedIndex()][0]
		self.session.openWithCallback(
			self.renameTagCallback,
			InputBox,
			title=_("Replace tag \"%s\" everywhere with:   (Note that 'Cancel' will not undo this!)") % (self.thistag[1]),
			text=self.thistag[1]
		)

	def renameTagCallback(self, res):
		res = res and res.strip().replace(" ", "_").capitalize()
		if res and len(res) and res != self.thistag[1]:
			thistag = self.thistag[1]
			self.foreachTimerTags(lambda t, tg: (thistag in tg) and self.setTimerTags(t, self.listReplace(tg, thistag, res)))
			self.foreachMovieTags(lambda r, tg: (thistag in tg) and self.setMovieTags(r, self.listReplace(tg, thistag, res)))
			self.listReplace(self.tags, thistag, res)
			self.listReplace(self.ghosttags, thistag, res)
			self.listReplace(self.ghostlist, thistag, res)
			self.updateMenuList(self.tags, self.thistag[3] and [res] or [])

	def removeTag(self):
		self.thistag = self["list"].list[self["list"].getSelectedIndex()][0]
		self.session.openWithCallback(
			self.removeTagCallback,
			MessageBox,
			_("Do you really want to delete tag \"%s\" everywhere?\n(Note that 'Cancel' will not undo this!)") % (self.thistag[1])
		)

	def removeTagCallback(self, res):
		if res:
			thistag = self.thistag[1]
			self.foreachTimerTags(lambda t, tg: (thistag in tg) and self.setTimerTags(t, self.listReplace(tg, thistag)))
			self.foreachMovieTags(lambda r, tg: (thistag in tg) and self.setMovieTags(r, self.listReplace(tg, thistag)))
			self.listReplace(self.tags, thistag)
			self.listReplace(self.ghosttags, thistag)
			self.listReplace(self.ghostlist, thistag)
			self.updateMenuList(self.tags)

	def removeAll(self):
		self.session.openWithCallback(
			self.removeAllCallback,
			MessageBox,
			_("Do you really want to delete all tags everywhere?\n(Note that 'Cancel' will not undo this!)")
		)

	def removeAllCallback(self, res):
		if res:
			self.foreachTimerTags(lambda t, tg: tg and self.setTimerTags(t, []))
			self.foreachMovieTags(lambda r, tg: tg and self.setMovieTags(r, []))
			self.tags = []
			self.ghosttags = []
			self.ghostlist = []
			self.updateMenuList(self.tags)

	def showMenu(self):
		menu = [
			(_("Add new tag..."), self.addCustom),
			(_("Rename this tag..."), self.renameTag),
			(_("Delete this tag..."), self.removeTag),
			(_("Delete unused tags"), self.removeUnused),
			(_("Delete all tags..."), self.removeAll)
		]
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title="", list=menu)

	def menuCallback(self, choice):
		if choice:
			choice[1]()

	def cancel(self):
		if not self.origtags == self.ghosttags:
			self.saveTagsFile(self.ghosttags)
			self.close(self.ghostlist)
		else:
			self.close(None)

	def accept(self):
		list = [x[1] for x in self["list"].getSelectionsList()]
		if not self.origtags == self.tags:
			self.saveTagsFile(self.tags)
		self.close(list)

class MovieTagEditor(TagEditor):
	def __init__(self, session, service, parent, args=0):
		self.service = service
		serviceHandler = eServiceCenter.getInstance()
		info = serviceHandler.info(service)
		path = service.getPath()
		if path.endswith(".ts"):
			path = path[:-3]
		self.path = path
		tags = info.getInfoString(service, iServiceInformation.sTags)
		if tags:
			tags = tags.split(' ')
		else:
			tags = []
		TagEditor.__init__(self, session, tags, args, parent=parent)
		self.skinName = ["MovieTagEditor", "TagEditor"]

	def saveTags(self, file, tags):
		if os_path.exists(file + ".ts.meta"):
			metafile = open(file + ".ts.meta", "r")
			sid = metafile.readline()
			title = metafile.readline()
			descr = metafile.readline()
			time = metafile.readline()
			oldtags = metafile.readline().rstrip()
			metafile.close()
			tags = " ".join(tags)
			if tags != oldtags:
				metafile = open(file + ".ts.meta", "w")
				metafile.write("%s%s%s%s%s" %(sid, title, descr, time, tags))
				metafile.close()

	def cancel(self):
		if not self.origtags == self.ghosttags:
			self.saveTagsFile(self.ghosttags)
			self.exitDialog()
		else:
			self.close()

	def accept(self):
		list = [x[1] for x in self["list"].getSelectionsList()]
		if not self.origtags == self.tags:
			self.saveTagsFile(self.tags)
		self.saveTags(self.path, list)
		self.exitDialog()

	def exitDialog(self):
		self.close()
		# This will try to get back to an updated movie list.
		# A proper way to do this should be provided in enigma2.
		try:
			parentscreen = self.parent
			parentscreen.csel.reloadList()
			parentscreen.close()
		except AttributeError:
			pass

