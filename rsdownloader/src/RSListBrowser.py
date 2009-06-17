##
## RS Downloader
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.FileList import FileList
from Components.Label import Label
from Components.MenuList import MenuList
from RSTranslation import TitleScreen
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists

if fileExists("/usr/lib/enigma2/python/Screens/LTKeyBoard.pyc"):
	from Screens.LTKeyBoard import LTKeyBoard
	LT = True
else:
	from Components.Input import Input
	from Screens.InputBox import InputBox
	LT = False

##############################################################################

class RSListBrowser(TitleScreen):
	skin = """
		<screen position="center,center" size="560,400" title="RS Downloader">
			<widget name="list" position="0,0" size="560,395" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, path):
		TitleScreen.__init__(self, session)
		self["list"] = FileList(path, False, True, "^.*\.(txt)")
		self["actions"] = ActionMap(["OkCancelActions"], {"ok": self.okClicked, "cancel": self.close}, -1)

	def okClicked(self):
		sel = self["list"].getFilename()
		if sel:
			dir = self["list"].getCurrentDirectory()
			self.session.open(TextEditor, "%s%s" % (dir, sel))
##############################################################################

class TextEditor(TitleScreen):
	skin = """
		<screen position="center,center" size="560,360" title="RS Downloader">
			<ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/yellow.png" position="280,0" size="140,40" transparent="1" alphatest="on" />
			<ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" transparent="1" alphatest="on" />
			<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" valign="center" halign="center" backgroundColor="#1f771f" transparent="1" />
			<widget name="list" position="10,45" size="540,300" scrollbarMode="showOnDemand" />
		</screen>"""

	def __init__(self, session, file):
		TitleScreen.__init__(self, session)
		
		self.file = file
		self.content = []
		
		self["key_red"] = Label(_("Clear"))
		self["key_green"] = Label(_("Save"))
		self["key_yellow"] = Label(_("Reload"))
		self["key_blue"] = Label(_("Delete"))
		self["list"] = MenuList(self.content)
		
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"red": self.clear,
				"green": self.save,
				"yellow": self.reload,
				"blue": self.delete,
				"ok": self.edit,
				"cancel": self.close
			}, -1)
		
		self.reload()

	def clear(self):
		while len(self.content):
			del self.content[0]
		self["list"].setList(self.content)

	def save(self):
		content = ""
		for x in self.content:
			content = "%s%s\n" % (content, x)
		content = content.replace("\n\n", "\n")
		if content == "\n":
			content = ""
		try:
			f = open(self.file, "w")
			f.write(content)
			f.close()
			self.session.open(MessageBox, _("%s saved.") % self.file, MessageBox.TYPE_INFO)
		except:
			self.session.open(MessageBox, _("Error while writing %s!") % self.file, MessageBox.TYPE_ERROR)

	def reload(self):
		self.clear()
		try:
			f = open(self.file, "r")
			content = f.read()
			f.close()
		except:
			content = ""
		if content.__contains__("\r"):
			content = content.split("\r")
		else:
			content = content.split("\n")
		for x in content:
			if (x != "\r") and (x != "\n") and (x != ""):
				self.content.append(x)
		self["list"].setList(self.content)

	def edit(self):
		if len(self.content) > 0:
			self.idx = self["list"].getSelectionIndex()
			text = self.content[self.idx]
			if LT:
				self.session.openWithCallback(self.editCallback, LTKeyBoard, title=_("Edit:"), text=text)
			else:
				self.session.openWithCallback(self.editCallback, InputBox, title=_("Edit:"), text=text, maxSize=False, type=Input.TEXT)

	def editCallback(self, callback):
		if callback:
			del self.content[self.idx]
			self.content.append(callback)
			self["list"].setList(self.content)

	def delete(self):
		if len(self.content) > 0:
			idx = self["list"].getSelectionIndex()
			del self.content[idx]
			self["list"].setList(self.content)

