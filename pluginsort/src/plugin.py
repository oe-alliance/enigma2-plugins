from . import _

# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Components.config import config, ConfigSubsection, ConfigSet
from Screens import PluginBrowser
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.PluginComponent import PluginComponent, plugins
from Components.PluginList import PluginEntryComponent
from Tools.Directories import resolveFilename, fileExists, SCOPE_SKIN_IMAGE, SCOPE_PLUGINS

from Components.ActionMap import ActionMap, NumberActionMap
from operator import attrgetter # python 2.5+

from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest

from enigma import eListboxPythonMultiContent, gFont
from Tools.LoadPixmap import LoadPixmap

from xml.etree.cElementTree import parse as cet_parse
try:
	from xml.etree.cElementTree import ParseError
except ImportError, ie:
	ParseError = SyntaxError

from shutil import copyfile, Error

XML_CONFIG = "/etc/enigma2/pluginsort.xml"

def SelectedPluginEntryComponent(plugin):
	if plugin.icon is None:
		png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/plugin.png"))
	else:
		png = plugin.icon

	return [
		plugin,
		MultiContentEntryText(pos=(0,0), size=(440, 50), backcolor_sel=8388608),
		MultiContentEntryText(pos=(120, 5), size=(320, 25), font=0, text=plugin.name),
		MultiContentEntryText(pos=(120, 26), size=(320, 17), font=1, text=plugin.description),
		MultiContentEntryPixmapAlphaTest(pos=(10, 5), size=(100, 40), png = png),
	]

WHEREMAP = {}
pdict = PluginDescriptor.__dict__
for where in pdict:
	if where.startswith('WHERE_'):
		WHEREMAP[where] = pdict[where]
del pdict
reverse = lambda map: dict(zip(map.values(), map.keys()))

class PluginWeights:
	def __init__(self):
		self.plugins = {}
		self.load()

	def load(self):
		if not fileExists(XML_CONFIG):
			return

		try:
			config = cet_parse(XML_CONFIG).getroot()
		except ParseError, pe:
			from time import time
			print "[PluginSort] Parse Error occured in configuration, backing it up and starting from scratch!"
			try:
				copyfile(XML_CONFIG, "/etc/enigma2/pluginsort.xml.%d" % (int(time()),))
			except Error, she:
				print "[PluginSort] Uh oh, failed to create the backup... I hope you have one anyway :D"
			return

		for wheresection in config.findall('where'):
			where = wheresection.get('type')
			whereid = WHEREMAP.get(where, None)
			whereplugins = wheresection.findall('plugin')
			if not whereid or not whereplugins:
				print "[PluginSort] Ignoring section %s because of invalid id (%s) or no plugins" % (where, repr(whereid))
				continue

			for plugin in whereplugins:
				name = plugin.get('name')
				try:
					weight = int(plugin.get('weight'))
				except ValueError, ve:
					print "[PluginSort] Invalid weight of %s received for plugin %s, ignoring" % (repr(plugin.get('weight')), repr(name))
				else:
					self.plugins.setdefault(whereid, {})[name] = weight

	def save(self):
		list = ['<?xml version="1.0" ?>\n<pluginsort>\n\n']
		append = list.append
		extend = list.extend

		idmap = reverse(WHEREMAP)
		for key in self.plugins.keys():
			whereplugins = self.plugins.get(key, None)
			if not whereplugins:
				continue

			where = idmap[key]
			extend((' <where type="', str(where), '">\n'))
			for key, value in whereplugins.iteritems():
				extend(('  <plugin name="', str(key), '" weight="', str(value), '" />\n'))
			append((' </where>\n'))
		append('\n</pluginsort>\n')
		
		file = open(XML_CONFIG, 'w')
		file.writelines(list)
		file.close()

	def get(self, plugin):
		for x in plugin.where:
			whereplugins = self.plugins.get(x, None)
			weight = whereplugins and whereplugins.get(plugin.name, None)
			if weight is not None:
				return weight
		return plugin.weight

	def set(self, plugin):
		for x in plugin.where:
			whereplugins = self.plugins.get(x, None)
			if whereplugins:
				whereplugins[plugin.name] = plugin.weight
			else:
				self.plugins[x] = {plugin.name: plugin.weight}

pluginWeights = PluginWeights()

def PluginComponent_addPlugin(self, plugin, *args, **kwargs):
	newWeight = pluginWeights.get(plugin)
	print "[PluginSort] Setting weight of %s from %d to %d" % (plugin.name, plugin.weight, newWeight)
	plugin.weight = newWeight
	PluginComponent.pluginSorter_baseAddPlugin(self, plugin, *args, **kwargs)

OriginalPluginBrowser = PluginBrowser.PluginBrowser
class SortingPluginBrowser(OriginalPluginBrowser):
	def __init__(self, *args, **kwargs):
		self.movemode = False
		self.selected = -1

		OriginalPluginBrowser.__init__(self, *args, **kwargs)
		self.skinName = ["SortingPluginBrowser", "PluginBrowser"]

		self["MenuActions"] = ActionMap(["MenuActions"],
			{
				"menu": self.openMenu,
			}, -1
		)
		self["ColorActions"] = ActionMap(["ColorActions"],
			{
				"green": self.toggleMoveMode,
			}, -2
		)
		self["ColorActions"].setEnabled(False)

		self["WizardActions"] = ActionMap(["WizardActions"],
			{
				"left": self.left,
				"right": self.right,
				"up": self.up,
				"down": self.down,
			}, -2
		)

		self["NumberActions"] = NumberActionMap(["NumberActions"],
			{
				"1": self.keyNumberGlobal,
				"2": self.keyNumberGlobal,
				"3": self.keyNumberGlobal,
				"4": self.keyNumberGlobal,
				"5": self.keyNumberGlobal,
				"6": self.keyNumberGlobal,
				"7": self.keyNumberGlobal,
				"8": self.keyNumberGlobal,
				"9": self.keyNumberGlobal,
				"0": self.keyNumberGlobal,
			}, -2
		)

	def keyNumberGlobal(self, number):
		if not self.movemode:
			realnumber = (number - 1) % 10
			if realnumber < len(self.list):
				self["list"].moveToIndex(realnumber)
				self.save()

	def close(self, *args, **kwargs):
		if self.movemode:
			self.toggleMoveMode()
		OriginalPluginBrowser.close(self, *args, **kwargs)

	# copied from PluginBrowser because we redo pretty much anything :-)
	def updateList(self):
		self.pluginlist = plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU)
		self.pluginlist.sort(key=attrgetter('weight', 'name')) # sort first by weight, then by name; we get pretty much a weight sorted but otherwise random list
		self.list = [PluginEntryComponent(plugin) for plugin in self.pluginlist]
		self["list"].l.setList(self.list)
		if fileExists(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/SoftwareManager/plugin.py")):
			# TRANSLATORS: leaving this empty is encouraged to not cause any confusion (this string was taken directly from the standard PluginBrowser)
			self["red"].setText(_("Manage extensions"))
			self["green"].setText(_("Sort") if not self.movemode else _("End Sort"))
			self["SoftwareActions"].setEnabled(True)
			self["PluginDownloadActions"].setEnabled(False)
			self["ColorActions"].setEnabled(True)
		else:
			# TRANSLATORS: leaving this empty is encouraged to not cause any confusion (this string was taken directly from the standard PluginBrowser)
			self["red"].setText(_("Remove Plugins"))
			# TRANSLATORS: leaving this empty is encouraged to not cause any confusion (this string was taken directly from the standard PluginBrowser)
			self["green"].setText(_("Download Plugins"))
			self["SoftwareActions"].setEnabled(False)
			self["PluginDownloadActions"].setEnabled(True)
			self["ColorActions"].setEnabled(False)

	def doMove(self, func):
		if self.selected != -1:
			oldpos = self["list"].getSelectedIndex()
			func()
			entry = self.list.pop(oldpos)
			newpos = self["list"].getSelectedIndex()
			self.list.insert(newpos, entry)
			self["list"].l.setList(self.list)
		else:
			func()

	def left(self):
		self.doMove(self["list"].pageUp)

	def right(self):
		self.doMove(self["list"].pageDown)

	def up(self):
		self.doMove(self["list"].up)

	def down(self):
		self.doMove(self["list"].down)

	def save(self):
		selected = self.selected
		if not self.movemode:
			OriginalPluginBrowser.save(self)
		elif selected != -1:
			Len = len(self.pluginlist)
			newpos = self["list"].getSelectedIndex()
			entry = self.pluginlist[selected]
			self.pluginlist.remove(entry)
			self.pluginlist.insert(newpos, entry)

			# we moved up, increase weight of plugins after us
			if newpos < selected:
				print "[PluginSort]", entry.name, "moved up"
				i = newpos + 1
				# since we moved up, there has to be an entry after this one
				diff = abs(self.pluginlist[i].weight - self.pluginlist[newpos].weight) + 1
				print "[PluginSort] Using weight from %d (%d) and %d (%d) to calculate diff (%d)" % (i, self.pluginlist[i].weight, newpos, self.pluginlist[newpos].weight, diff)
				while i < Len:
					print "[PluginSort] INCREASE WEIGHT OF", self.pluginlist[i].name, "BY", diff
					self.pluginlist[i].weight += diff
					i += 1
			# we moved down, decrease weight of plugins before us
			elif newpos > selected:
				print "[PluginSort]", entry.name, "moved down"
				i = newpos - 1
				# since we moved up, there has to be an entry before this one
				diff = abs(self.pluginlist[newpos].weight - self.pluginlist[i].weight) + 1
				print "[PluginSort] Using weight from %d (%d) and %d (%d) to calculate diff (%d)" % (newpos, self.pluginlist[newpos].weight, i, self.pluginlist[i].weight, diff)
				while i > -1:
					print "[PluginSort] DECREASE WEIGHT OF", self.pluginlist[i].name, "BY", diff
					self.pluginlist[i].weight -= diff
					i -= 1
			else:
				print "[PluginSort]", entry.name, "did not move (%d to %d)?" % (selected, newpos)

			self.list = [PluginEntryComponent(plugin) for plugin in self.pluginlist]
			print "[PluginSort] NEW LIST:", [(plugin.name, plugin.weight) for plugin in self.pluginlist]
			self["list"].l.setList(self.list)
			self.selected = -1
		else:
			self.selected = self["list"].getSelectedIndex()
			self.list[self.selected] = SelectedPluginEntryComponent(self.pluginlist[self.selected])
			self["list"].l.setList(self.list)
	
	def openMenu(self):
		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/PluginHider/plugin.py")):
			if self.movemode:
				# TRANSLATORS: there is no need to translate this string, as it was reused from e2 core
				moveString = _("disable move mode")
			else:
				# TRANSLATORS: there is no need to translate this string, as it was reused from e2 core
				moveString = _("enable move mode")
			list = [
				(_("hide selected plugin"), self.hidePlugin),
				(moveString, self.toggleMoveMode),
			]
			self.session.openWithCallback(
				self.menuCallback,
				ChoiceBox,
				list = list,
			)
		else:
			self.toggleMoveMode()

	def menuCallback(self, ret):
		ret and ret[1]()

	def hidePlugin(self):
		try:
			from Plugins.Extensions.PluginHider.plugin import hidePlugin
		except Exception, e:
			self.session.open(MessageBox, _("Unable to load PluginHider"), MessageBox.TYPE_ERROR)
		else:
			hidePlugin(self["list"].l.getCurrentSelection()[0])

			# we were actually in move mode, so save the current position
			if self.selected != -1:
				self.save()
			self.updateList()

	def toggleMoveMode(self):
		if self.movemode:
			if self.selected != -1:
				self.save()
			if fileExists(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/SoftwareManager/plugin.py")):
				self["green"].setText(_("Sort"))

			for plugin in self.pluginlist:
				pluginWeights.set(plugin)
			pluginWeights.save()
		else:
			if fileExists(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/SoftwareManager/plugin.py")):
				self["green"].setText(_("End Sort"))
		self.movemode = not self.movemode

def autostart(reason, *args, **kwargs):
	if reason == 0:
		PluginComponent.pluginSorter_baseAddPlugin = PluginComponent.addPlugin
		PluginComponent.addPlugin = PluginComponent_addPlugin

		# "fix" weight of plugins already added to list, future ones will be fixed automatically
		for plugin in plugins.getPlugins(PluginDescriptor.WHERE_PLUGINMENU):
			# enigma2 older than 3.3.2011 does not know plugin weights, so default them to 0 manually
			try:
				newWeight = pluginWeights.get(plugin)
			except AttributeError, ae:
				plugin.weight = 0
				newWeight = 0
				PluginDescriptor.weight = 0
				print "[PluginSort] Introduced weight attribute to PluginDescriptor for old enigma2 (this message may show multiple times)"

			print "[PluginSort] Fixing weight for %s (was %d, now %d)" % (plugin.name, plugin.weight, newWeight)
			plugin.weight = newWeight

		PluginBrowser.PluginBrowser = SortingPluginBrowser
	else:
		PluginComponent.addPlugin = PluginComponent.pluginSorter_baseAddPlugin
		PluginBrowser.PluginBrowser = OriginalPluginBrowser

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=False, # TODO: check this!
		),
	]
