from __future__ import print_function

from . import _
# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Screens.Menu import Menu, mdom
from Screens.HelpMenu import HelpableScreen

from Tools.BoundFunction import boundFunction
from Tools.Directories import fileExists

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, \
		RT_WRAP
from Components.MenuList import MenuList
from skin import parseColor, parseFont

from Components.ActionMap import HelpableActionMap, ActionMap
from Components.SystemInfo import SystemInfo
from Components.Sources.StaticText import StaticText

from xml.etree.cElementTree import parse as cet_parse
try:
	from xml.etree.cElementTree import ParseError
except ImportError as ie:
	ParseError = SyntaxError

try:
	dict.iteritems
	iteritems = lambda d: d.iteritems()
except AttributeError:
	iteritems = lambda d: d.items()

from operator import itemgetter
from shutil import copyfile, Error

XML_CONFIG = "/etc/enigma2/menusort.xml"
DEBUG = False
HIDDENWEIGHT = -195948557

class baseMethods:
	pass

class MenuWeights:
	def __init__(self):
		# map text -> (weight, hidden)
		self.weights = {}
		self.load()

	def load(self):
		if not fileExists(XML_CONFIG):
			return

		try:
			file = open(XML_CONFIG, 'r')
			config = cet_parse(file).getroot()
			file.close()
		except ParseError as pe:
			from time import time
			print("[MenuSort] Parse Error occured in configuration, backing it up and starting from scratch!")
			try:
				copyfile(XML_CONFIG, "/etc/enigma2/menusort.xml.%d" % (int(time()),))
			except Error as she:
				print("[MenuSort] Uh oh, failed to create the backup... I hope you have one anyway :D")
			return

		for node in config.findall('entry'):
			text = node.get('text', '').encode("UTF-8")
			weight = node.get("weight", None)
			hidden = node.get('hidden', False)
			hidden = hidden and hidden.lower() == "yes"
			try:
				weight = int(weight)
			except ValueError as ve:
				print("[MenuSort] Invalid value for weight on entry %s: %s" % (repr(text), repr(weight)))
				continue
			if not text or weight is None:
				print("[MenuSort] Invalid entry in xml (%s, %s), ignoring" % (repr(text), repr(weight)))
				continue
			self.weights[text] = (weight, hidden)

	def save(self):
		list = ['<?xml version="1.0" ?>\n<menusort>\n\n']
		append = list.append
		extend = list.extend

		for text, values in iteritems(self.weights):
			weight, hidden = values
			extend((' <entry text="', str(text), '" weight="', str(weight), '" hidden="', "yes" if hidden else "no", '"/>\n'))
		append('\n</menusort>\n')

		file = open(XML_CONFIG, 'w')
		file.writelines(list)
		file.close()

	def isHidden(self, tuple):
		weight, hidden = self.weights.get(tuple[0], (tuple[3], False))
		return hidden

	def get(self, tuple, supportHiding = True):
		weight, hidden = self.weights.get(tuple[0], (tuple[3], False))
		if supportHiding and hidden: return HIDDENWEIGHT
		return int(weight)

	def cmp(self, first, second):
		return self.get(first) - self.get(second)

	def set(self, tuple):
		self.weights[tuple[0]] = (tuple[3], tuple[4])
menuWeights = MenuWeights()

def Menu__init__(self, session, parent, *args, **kwargs):
	baseMethods.Menu__init__(self, session, parent, *args, **kwargs)
	list = self["menu"].list
	list.sort(key=menuWeights.get)

	# remove hidden entries from list
	i = 0
	for x in list:
		if menuWeights.get(x) == HIDDENWEIGHT: i += 1
		else: break
	if i:
		del list[:i]

	self["menu"].list = list

class SortableMenuList(MenuList):
	def __init__(self, list):
		MenuList.__init__(self, list, False, content=eListboxPythonMultiContent)

		l = self.l
		l.setFont(0, gFont("Regular", 22))
		l.setBuildFunc(self.buildListboxEntry)
		self.selected = None
		self.selectedColor = 8388608
		self.hiddenColor = 8388564

	def invalidate(self):
		self.l.invalidate()

	def applySkin(self, desktop, parent):
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.l.setFont(0, parseFont(value, ((1,1),(1,1))))
				elif attrib == "itemHeight":
					self.l.setItemHeight(int(value))
				elif attrib == "selectedColor":
					self.selectedColor = int(parseColor(value))
				elif attrib == "hiddenColor":
					self.hiddenColor = int(parseColor(value))
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent)

	def buildListboxEntry(self, *menu):
		size = self.l.getItemSize()
		height = size.height()
		width = size.width()
		color = self.hiddenColor if menu[4] else None

		l = [
			None,
			(eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT|RT_WRAP, menu[0], color, color),
		]
		if menu[0] == self.selected:
			l.insert(1, (eListboxPythonMultiContent.TYPE_TEXT, 0, 0, width, height, 0, RT_HALIGN_LEFT|RT_WRAP, '',  None, None, None, self.selectedColor, None, None))
		return l

class SortableMenu(Menu, HelpableScreen):
	skin = """<screen name="SortableMenu" position="center,center" size="210,330">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_blue" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="menu" position="5,95" size="200,225" scrollbarMode="showOnDemand" font="Regular;23" />
		</screen>"""
	def __init__(self, *args, **kwargs):
		baseMethods.Menu__init__(self, *args, **kwargs) # using the base initializer saves us a few cycles
		HelpableScreen.__init__(self)
		self.skinName = "SortableMenu"
		self.setTitle(_("Main menu"))

		# XXX: not nice, but makes our life a little easier
		l = [(x[0], x[1], x[2], menuWeights.get(x, supportHiding=False), menuWeights.isHidden(x)) for x in self["menu"].list]
		l.sort(key=itemgetter(3))
		self["menu"] = SortableMenuList(l)
		self["key_blue"] = StaticText(_("hide entry"))

		self["DirectionActions"] = ActionMap(["DirectionActions"],
			{
				"left": boundFunction(self.doMove, self["menu"].pageUp),
				"right": boundFunction(self.doMove, self["menu"].pageDown),
				"up": boundFunction(self.doMove, self["menu"].up),
				"down": boundFunction(self.doMove, self["menu"].down),
			}, -1
		)

		self["MenuSortActions"] = HelpableActionMap(self, "MenuSortActions",
			{
				"ignore": lambda: None, # we need to overwrite some regular actions :-)
				"toggleSelection": (self.toggleSelection, _("toggle selection")),
				"selectEntry": (self.okbuttonClick, _("enter menu")),
				"hideEntry": (self.hideEntry, _("hide entry")),
			}, -1
		)
		self.selected = -1

	def createSummary(self):
		return None

	def hideEntry(self):
		l = self["menu"].list
		idx = self["menu"].getSelectedIndex()
		x = l[idx]
		l[idx] = (x[0], x[1], x[2], x[3], not x[4])
		self["menu"].setList(l)

	# copied from original Menu for simplicity
	def addMenu(self, destList, node):
		requires = node.get("requires")
		if requires:
			if requires[0] == '!':
				if SystemInfo.get(requires[1:], False):
					return
			elif not SystemInfo.get(requires, False):
				return
		MenuTitle = _(node.get("text", "??").encode("UTF-8"))
		entryID = node.get("entryID", "undefined")
		weight = node.get("weight", 50)
		x = node.get("flushConfigOnClose")
		if x:
			a = boundFunction(self.session.openWithCallback, self.menuClosedWithConfigFlush, SortableMenu, node)
		else:
			a = boundFunction(self.session.openWithCallback, self.menuClosed, SortableMenu, node)
		#TODO add check if !empty(node.childNodes)
		destList.append((MenuTitle, a, entryID, weight))

	def close(self, *args, **kwargs):
		for entry in self["menu"].list:
			menuWeights.set(entry)
		menuWeights.save()
		Menu.close(self, *args, **kwargs)

	def doMove(self, func):
		if self.selected != -1:
			l = self["menu"].list
			oldpos = self["menu"].getSelectedIndex()
			func()
			entry = l.pop(oldpos)
			newpos = self["menu"].getSelectedIndex()
			l.insert(newpos, entry)
			self["menu"].setList(l)
		else:
			func()

	def toggleSelection(self):
		selected = self.selected
		if selected != -1:
			l = self["menu"].list
			Len = len(l)
			newpos = self["menu"].getSelectedIndex()
			entry = l[newpos]

			# we moved up, increase weight of plugins after us
			if newpos < selected:
				print("[MenuSort]", entry[0], "moved up")
				i = newpos + 1
				# since we moved up, there has to be an entry after this one
				diff = abs(int(l[i][3]) - int(l[newpos][3])) + 1
				print("[MenuSort] Using weight from %d (%d) and %d (%d) to calculate diff (%d)" % (i, int(l[i][3]), newpos, int(l[newpos][3]), diff))
				while i < Len:
					if DEBUG: print("[MenuSort] INCREASE WEIGHT OF", l[i][0], "BY", diff)
					l[i] = (l[i][0], l[i][1], l[i][2], int(l[i][3]) + diff, l[i][4])
					i += 1
			# we moved down, decrease weight of plugins before us
			elif newpos > selected:
				print("[MenuSort]", entry[0], "moved down")
				i = newpos - 1
				# since we moved up, there has to be an entry before this one
				diff = abs(int(l[i][3]) - int(l[newpos][3])) + 1
				print("[MenuSort] Using weight from %d (%d) and %d (%d) to calculate diff (%d)" % (newpos, int(l[newpos][3]), i, int(l[i][3]), diff))
				while i > -1:
					if DEBUG: print("[MenuSort] DECREASE WEIGHT OF", l[i][0], "BY", diff)
					l[i] = (l[i][0], l[i][1], l[i][2], int(l[i][3]) - diff, l[i][4])
					i -= 1
			else:
				if DEBUG: print("[MenuSort]", entry[0], "did not move (%d to %d)?" % (selected, newpos))

			if DEBUG: print("[MenuSort] NEW LIST:", l)
			self["menu"].setList(l)
			self.selected = -1
			self["menu"].selected = None
		else:
			sel = self["menu"].getCurrent()
			if sel:
				self["menu"].selected = sel[0]
				self.selected = self["menu"].getSelectedIndex()
				self["menu"].invalidate()
			else:
				self.selected = -1

	def keyNumberGlobal(self, number):
		pass

def autostart(reason, *args, **kwargs):
	if reason == 0:
		try:
			baseMethods.Menu__init__
		except AttributeError as ae:
			pass
		else:
			print("[MenuSort] Initialized more than once, ignoring request.")
			return

		baseMethods.Menu__init__ = Menu.__init__
		Menu.__init__ = Menu__init__
	else:
		Menu.__init__ = baseMethods.Menu__init__

def main(session, *args, **kwargs):
	session.open(SortableMenu, mdom.getroot())

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=False,
		),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_PLUGINMENU,
			name="MenuSort",
			description=_("Sort main menu"),
			fnc=main,
			needsRestart=False,
		),
	]
