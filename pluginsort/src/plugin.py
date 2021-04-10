from __future__ import print_function

from . import _

# Plugin definition
from Plugins.Plugin import PluginDescriptor

from Screens import PluginBrowser
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.PluginComponent import PluginComponent, plugins
from Components.Label import Label
from Tools.Directories import resolveFilename, fileExists, SCOPE_SKIN_IMAGE, SCOPE_PLUGINS
from Tools.BoundFunction import boundFunction
from Screens.InfoBarGenerics import InfoBarPlugins
from Components.config import config, ConfigSubsection, ConfigYesNo
from Components.PluginList import PluginList
from Components.Converter.TemplatedMultiContent import TemplatedMultiContent
from Components.Renderer.Listbox import Listbox as ListboxRenderer

from Components.ActionMap import ActionMap, NumberActionMap
from operator import attrgetter # python 2.5+

from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest

from enigma import eListboxPythonMultiContent, gFont
from Tools.LoadPixmap import LoadPixmap

from xml.etree.cElementTree import parse as cet_parse
try:
	from xml.etree.cElementTree import ParseError
except ImportError as ie:
	ParseError = SyntaxError
from Tools.XMLTools import stringToXML

from shutil import copyfile, Error

import six


XML_CONFIG = "/etc/enigma2/pluginsort.xml"
DEBUG = False

config.plugins.pluginsort = ConfigSubsection()
config.plugins.pluginsort.show_help = ConfigYesNo(default=True)

def MyPluginEntryComponent(plugin, backcolor_sel=None):
	if plugin.icon is None:
		png = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/plugin.png"))
	else:
		png = plugin.icon

	return [
		plugin, plugin.name, plugin.description, png,
		#plugin, backcolor_sel, plugin.name, plugin.description, png,
	]

# TODO: make selected color themable
SelectedPluginEntryComponent = lambda plugin: MyPluginEntryComponent(plugin, backcolor_sel=8388608)

class MyPluginList(PluginList):
	def __init__(self, *args, **kwargs):
		PluginList.__init__(self, *args, **kwargs)
		self.__inst = None

	def __instance(self):
		if self.__inst is not None:
			return self.__inst
		for x in self.downstream_elements:
			if isinstance(x, TemplatedMultiContent):
				for y in x.downstream_elements:
					if isinstance(y, ListboxRenderer):
						self.__inst = y.instance
						return self.__inst
		return None

	def up(self):
		instance = self.__instance()
		if instance:
			instance.moveSelection(instance.moveUp)
	def down(self):
		instance = self.__instance()
		if instance:
			instance.moveSelection(instance.moveDown)
	def pageUp(self):
		instance = self.__instance()
		if instance:
			instance.moveSelection(instance.pageUp)
	def pageDown(self):
		instance = self.__instance()
		if instance:
			instance.moveSelection(instance.pageDown)

WHEREMAP = {}
pdict = PluginDescriptor.__dict__
for where in pdict:
	if where.startswith('WHERE_'):
		WHEREMAP[where] = pdict[where]
del pdict

try:
	dict.iteritems
	iteritems = lambda d: six.iteritems(d)
except AttributeError:
	iteritems = lambda d: d.items()
reverse = lambda map: dict((v, k) for k, v in iteritems(map))

class PluginWeights:
	def __init__(self):
		self.plugins = {}
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
			print("[PluginSort] Parse Error occured in configuration, backing it up and starting from scratch!")
			try:
				copyfile(XML_CONFIG, "/etc/enigma2/pluginsort.xml.%d" % (int(time()),))
			except Error as she:
				print("[PluginSort] Uh oh, failed to create the backup... I hope you have one anyway :D")
			return

		for wheresection in config.findall('where'):
			where = wheresection.get('type')
			whereid = WHEREMAP.get(where, None)
			whereplugins = wheresection.findall('plugin')
			if whereid is None or not whereplugins:
				print("[PluginSort] Ignoring section %s because of invalid id (%s) or no plugins (%s)" % (where, repr(whereid), repr(whereplugins)))
				continue

			for plugin in whereplugins:
				name = plugin.get('name')
				try:
					weight = int(plugin.get('weight'))
				except ValueError as ve:
					print("[PluginSort] Invalid weight of %s received for plugin %s, ignoring" % (repr(plugin.get('weight')), repr(name)))
				else:
					self.plugins.setdefault(whereid, {})[name] = weight

	def save(self):
		lst = ['<?xml version="1.0" ?>\n<pluginsort>\n\n']
		append = lst.append
		extend = lst.extend

		idmap = reverse(WHEREMAP)
		for key in list(self.plugins.keys()):
			whereplugins = self.plugins.get(key, None)
			if not whereplugins:
				continue

			where = idmap[key]
			extend((' <where type="', str(where), '">\n'))
			for key, value in iteritems(whereplugins):
				extend(('  <plugin name="', stringToXML(str(key)), '" weight="', str(value), '" />\n'))
			append((' </where>\n'))
		append('\n</pluginsort>\n')
		
		file = open(XML_CONFIG, 'w')
		file.writelines(lst)
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
	if len(plugin.where) > 1:
		print("[PluginSort] Splitting %s up in individual entries (%s)" % (plugin.name, repr(plugin.where)))
		for x in plugin.where:
			pd = PluginDescriptor(name=plugin.name, where=[x], description=plugin.description, icon=plugin.icon, fnc=plugin.__call__, wakeupfnc=plugin.wakeupfnc, needsRestart=plugin.needsRestart, internal=plugin.internal, weight=plugin.weight)

			newWeight = pluginWeights.get(pd)
			if DEBUG:
				print("[PluginSort] Setting weight of %s from %d to %d" % (pd.name, pd.weight, newWeight))
			pd.weight = newWeight
			PluginComponent.pluginSort_baseAddPlugin(self, pd, *args, **kwargs)

		# installedPluginList is a list of original descriptors, but we changed it to be a copy, not a reference. so keep it up to date
		if self.firstRun:
			self.installedPluginList.append(plugin)
			if DEBUG:
				print("[PluginSort] Adding %s to list of installed plugins (%s, %s)." % (plugin.name, plugin.path, repr(plugin.where)))
		return

	newWeight = pluginWeights.get(plugin)
	if DEBUG:
		print("[PluginSort] Setting weight of %s from %d to %d" % (plugin.name, plugin.weight, newWeight))
	plugin.weight = newWeight
	PluginComponent.pluginSort_baseAddPlugin(self, plugin, *args, **kwargs)

	if self.firstRun:
		if DEBUG:
			print("[PluginSort] Adding %s to list of installed plugins (%s, %s)." % (plugin.name, plugin.path, repr(plugin.where)))
		self.installedPluginList.append(plugin)

if DEBUG:
	def PluginComponent_removePlugin(self, plugin, *args, **kwargs):
		print("[PluginSort] Supposed to remove plugin: %s (%s, %s)." % (plugin.name, plugin.path, repr(plugin.where)))
		try:
			PluginComponent.pluginSort_baseRemovePlugin(self, plugin, *args, **kwargs)
		except ValueError as ve:
			revMap = reverse(WHEREMAP)
			print("-"*40)
			print("-"*40)
			print("-"*40)
			print("[PluginSort] pluginList: %s" % (repr([(x.name, x.path, repr([revMap[y] for y in x.where])) for x in self.pluginList]),))
			for w in plugin.where:
				print("[PluginSort] plugins[%s]: %s" % (revMap[w], repr([(x.name, x.path, repr([revMap[y] for y in x.where])) for x in self.plugins[w]])))
	PluginComponent.pluginSort_baseRemovePlugin = PluginComponent.removePlugin
	PluginComponent.removePlugin = PluginComponent_removePlugin

OriginalPluginBrowser = PluginBrowser.PluginBrowser
class SortingPluginBrowser(OriginalPluginBrowser):
	def __init__(self, *args, **kwargs):
		self.movemode = False
		self.selected = -1
		if 'where' in kwargs:
			self.where = kwargs['where']
			del kwargs['where']
		else:
			self.where = PluginDescriptor.WHERE_PLUGINMENU

		OriginalPluginBrowser.__init__(self, *args, **kwargs)
		self.skinName = ["SortingPluginBrowser", "PluginBrowser"] # XXX: fallback is evil because it makes moving more confusing :P

		self["pluginlist"] = MyPluginList(self.list)

		self["key_yellow"] = Label()

		self["ColorActions"] = ActionMap(["ColorActions"],
			{
				"yellow": self.toggleMoveMode,
			}, -2
		)

		self["WizardActions"] = ActionMap(["WizardActions"],
			{
				"left": boundFunction(self.doMove, self["pluginlist"].pageUp),
				"right": boundFunction(self.doMove, self["pluginlist"].pageDown),
				"up": boundFunction(self.doMove, self["pluginlist"].up),
				"down": boundFunction(self.doMove, self["pluginlist"].down),
			}, -2
		)

		if self.where != PluginDescriptor.WHERE_PLUGINMENU:
			self.toggleMoveMode()
			self.onShow.append(self.setCustomTitle)
		else:
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

			self["MenuActions"] = ActionMap(["MenuActions"],
				{
					"menu": self.openMenu,
				}, -1
			)
		self.onFirstExecBegin.append(self.firstExec)

	def firstExec(self):
		if config.plugins.pluginsort.show_help.value and pluginSortHelp:
			config.plugins.pluginsort.show_help.value = False
			config.plugins.pluginsort.show_help.save()
			pluginSortHelp.open(self.session)

	def setCustomTitle(self):
		titleMap = {
			PluginDescriptor.WHERE_EXTENSIONSMENU: _("Sort Extensions"),
			PluginDescriptor.WHERE_MOVIELIST: _("Sort MovieList Extensions"),
			PluginDescriptor.WHERE_EVENTINFO: _("Sort EventInfo Extensions"),
		}
		title = titleMap.get(self.where, None)
		if title:
			self.setTitle(title)

	def keyNumberGlobal(self, number):
		if not self.movemode:
			realnumber = (number - 1) % 10
			if realnumber < len(self.list):
				self["pluginlist"].index = realnumber
				self.save()

	def close(self, *args, **kwargs):
		if self.movemode:
			self.toggleMoveMode()
		OriginalPluginBrowser.close(self, *args, **kwargs)

	# copied from PluginBrowser because we redo pretty much anything :-)
	def updateList(self):
		self.pluginlist = plugins.getPlugins(self.where)
		if self.where in (PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU):
			self.pluginlist.sort(key=attrgetter('weight', 'name')) # sort first by weight, then by name; we get pretty much a weight sorted but otherwise random list
		else: #if self.where in (PluginDescriptor.WHERE_EVENTINFO, PluginDescriptor.WHERE_MOVIELIST):
			self.pluginlist.sort(key=attrgetter('weight'))
		self.list = [MyPluginEntryComponent(plugin) for plugin in self.pluginlist]
		self["pluginlist"].list = self.list
		if self.where == PluginDescriptor.WHERE_PLUGINMENU:
			# TRANSLATORS: leaving this empty is encouraged to not cause any confusion (this string was taken directly from the standard PluginBrowser)
			self["key_red"].setText(_("Remove Plugins"))
			self["key_green"].setText(_("Download Plugins"))
			self["key_yellow"].setText(_("Sort") if not self.movemode else _("End Sort"))
			self["PluginDownloadActions"].setEnabled(True)
			self["ColorActions"].setEnabled(True)
		else:
			self["key_red"].setText("")
			self["key_green"].setText("")
			self["key_yellow"].setText(_("Sort") if not self.movemode else _("End Sort"))
			self["PluginDownloadActions"].setEnabled(False)
			self["ColorActions"].setEnabled(True)

	def doMove(self, func):
		if self.selected != -1:
			oldpos = self["pluginlist"].index
			func()
			entry = self.list.pop(oldpos)
			newpos = self["pluginlist"].index
			self.list.insert(newpos, entry)
			# XXX: modifyEntry is broken - I'd say a job well done :P
			#self["pluginlist"].modifyEntry(oldpos, self.list[oldpos])
			#self["pluginlist"].modifyEntry(newpos, self.list[newpos])
			self["pluginlist"].updateList(self.list)
		else:
			func()

	def save(self):
		selected = self.selected
		if not self.movemode:
			OriginalPluginBrowser.save(self)
		elif selected != -1:
			Len = len(self.pluginlist)
			newpos = self["pluginlist"].index
			entry = self.pluginlist[selected]
			self.pluginlist.remove(entry)
			self.pluginlist.insert(newpos, entry)

			# we moved up, increase weight of plugins after us
			if newpos < selected:
				print("[PluginSort]", entry.name, "moved up")
				i = newpos + 1
				# since we moved up, there has to be an entry after this one
				diff = abs(self.pluginlist[i].weight - self.pluginlist[newpos].weight) + 1
				print("[PluginSort] Using weight from %d (%d) and %d (%d) to calculate diff (%d)" % (i, self.pluginlist[i].weight, newpos, self.pluginlist[newpos].weight, diff))
				while i < Len:
					if DEBUG:
						print("[PluginSort] INCREASE WEIGHT OF", self.pluginlist[i].name, "BY", diff)
					self.pluginlist[i].weight += diff
					i += 1
			# we moved down, decrease weight of plugins before us
			elif newpos > selected:
				print("[PluginSort]", entry.name, "moved down")
				i = newpos - 1
				# since we moved up, there has to be an entry before this one
				diff = abs(self.pluginlist[newpos].weight - self.pluginlist[i].weight) + 1
				print("[PluginSort] Using weight from %d (%d) and %d (%d) to calculate diff (%d)" % (newpos, self.pluginlist[newpos].weight, i, self.pluginlist[i].weight, diff))
				while i > -1:
					if DEBUG:
						print("[PluginSort] DECREASE WEIGHT OF", self.pluginlist[i].name, "BY", diff)
					self.pluginlist[i].weight -= diff
					i -= 1
			else:
				if DEBUG:
					print("[PluginSort]", entry.name, "did not move (%d to %d)?" % (selected, newpos))

			self.list = [MyPluginEntryComponent(plugin) for plugin in self.pluginlist]
			if DEBUG:
				print("[PluginSort] NEW LIST:", [(plugin.name, plugin.weight) for plugin in self.pluginlist])
			# XXX: modifyEntry is broken - I'd say a job well done :P
			#self["pluginlist"].modifyEntry(newpos, self.list[newpos])
			self["pluginlist"].updateList(self.list)
			self.selected = -1
		else:
			self.selected = self["pluginlist"].index
			self.list[self.selected] = SelectedPluginEntryComponent(self.pluginlist[self.selected])
			# XXX: modifyEntry is broken - I'd say a job well done :P
			#self["pluginlist"].modifyEntry(self.selected, self.list[self.selected])
			self["pluginlist"].updateList(self.list)

	def openMenu(self):
		if self.movemode:
			# TRANSLATORS: there is no need to translate this string, as it was reused from e2 core
			moveString = _("disable move mode")
		else:
			# TRANSLATORS: there is no need to translate this string, as it was reused from e2 core
			moveString = _("enable move mode")

		list = [
			(moveString, self.toggleMoveMode),
			(_("move extensions"), boundFunction(self.openMover, PluginDescriptor.WHERE_EXTENSIONSMENU)),
			(_("move movie extensions"), boundFunction(self.openMover, PluginDescriptor.WHERE_MOVIELIST)),
			(_("move event extensions"), boundFunction(self.openMover, PluginDescriptor.WHERE_EVENTINFO)),
		]

		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/PluginHider/plugin.pyo")):
			list.insert(0, (_("hide selected plugin"), self.hidePlugin))

		if pluginSortHelp:
			list.insert(0, (_("Help"), boundFunction(pluginSortHelp.open, self.session)))

		self.session.openWithCallback(
			self.menuCallback,
			ChoiceBox,
			list=list,
		)

	def menuCallback(self, ret):
		ret and ret[1]()

	def openMover(self, where):
		self.session.open(SortingPluginBrowser, where=where)

	def hidePlugin(self):
		try:
			from Plugins.Extensions.PluginHider.plugin import hidePlugin
		except Exception as e:
			self.session.open(MessageBox, _("Unable to load PluginHider"), MessageBox.TYPE_ERROR)
		else:
			hidePlugin(self["pluginlist"].current[0])

			# we were actually in move mode, so save the current position
			if self.selected != -1:
				self.save()
			self.updateList()

	def toggleMoveMode(self):
		if self.movemode:
			if self.selected != -1:
				self.save()
			self["yellow"].setText(_("Sort"))

			for plugin in self.pluginlist:
				pluginWeights.set(plugin)
			pluginWeights.save()

			# auto-close if not "PluginBrowser"
			if self.where != PluginDescriptor.WHERE_PLUGINMENU:
				self.movemode = False
				return self.close()
		else:
			self["yellow"].setText(_("End Sort"))
		self.movemode = not self.movemode

def autostart(reason, *args, **kwargs):
	if reason == 0:
		if hasattr(PluginComponent, 'pluginSort_baseAddPlugin'):
			print("[PluginSort] Something went wrong as our autostart handler was called multiple times for startup, printing traceback and ignoring.")
			import traceback
			import sys
			traceback.print_stack(limit=5, file=sys.stdout)
		else:
			PluginComponent.pluginSort_baseAddPlugin = PluginComponent.addPlugin
			PluginComponent.addPlugin = PluginComponent_addPlugin

			# we use a copy for installed plugins because we might change the 'where'-lists
			plugins.installedPluginList = plugins.pluginList[:]
			def PluginComponent__setattr__(self, key, value):
				if key == 'installedPluginList':
					return
				else:
					self.__dict__[key] = value
			PluginComponent.__setattr__ = PluginComponent__setattr__

			if hasattr(plugins, 'pluginHider_baseGetPlugins'):
				pluginlist = plugins.pluginHider_baseGetPlugins([PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_MOVIELIST, PluginDescriptor.WHERE_EVENTINFO])
			else:
				pluginlist = plugins.getPlugins([PluginDescriptor.WHERE_PLUGINMENU, PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_MOVIELIST, PluginDescriptor.WHERE_EVENTINFO])

			# "fix" weight of plugins already added to list, future ones will be fixed automatically
			fixed = []
			for plugin in pluginlist:
				if plugin in fixed:
					continue # skip double entries

				# create individual entries for multiple wheres, this is potentially harmful!
				if len(plugin.where) > 1:
					# remove all entries except for a potential autostart one (highly unlikely to mix autostart with one of the above, but you never know :D)
					if PluginDescriptor.WHERE_AUTOSTART in plugin.where:
						plugin.where.remove(PluginDescriptor.WHERE_AUTOSTART)
						hadAutostart = True
					else:
						hadAutostart = False
					plugins.removePlugin(plugin)
					plugins.addPlugin(plugin) # this is our own addPlugin now, which automatically creates copies

					# HACK: re-add autostart entry to internal list inside PluginComponent
					if hadAutostart:
						plugin.where = [ PluginDescriptor.WHERE_AUTOSTART ]
						plugins.pluginList.append(plugin)

				# we're keeping the entry, just fix the weight
				else:
					newWeight = pluginWeights.get(plugin)
					print("[PluginSort] Fixing weight for %s (was %d, now %d)" % (plugin.name, plugin.weight, newWeight))
					plugin.weight = newWeight

				fixed.append(plugin)

			# let movieepg fix extensions list sorting if installed, else do this ourselves
			if not fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/MovieEPG/plugin.py")):
				def InfoBarPlugins_getPluginList(self, *args, **kwargs):
					l = InfoBarPlugins.pluginSort_baseGetPluginList(self, *args, **kwargs)
					try:
						l.sort(key=lambda e: (e[0][1].args[0].weight, e[2]))
					except Exception as e:
						print("[PluginSort] Failed to sort extensions", e)
					return l

				InfoBarPlugins.pluginSort_baseGetPluginList = InfoBarPlugins.getPluginList
				InfoBarPlugins.getPluginList = InfoBarPlugins_getPluginList


			PluginBrowser.PluginBrowser = SortingPluginBrowser
	else:
		if hasattr(PluginComponent, 'pluginSort_baseAddPlugin'):
			PluginComponent.addPlugin = PluginComponent.pluginSort_baseAddPlugin
			del PluginComponent.pluginSort_baseAddPlugin
		if hasattr(InfoBarPlugins, 'pluginSort_baseGetPluginList'):
			InfoBarPlugins.getPluginList = InfoBarPlugins.pluginSort_baseGetPluginList
			del InfoBarPlugins.pluginSort_baseGetPluginList
		PluginBrowser.PluginBrowser = OriginalPluginBrowser

#pragma mark - Help
try:
	from Plugins.SystemPlugins.MPHelp import registerHelp, showHelp, XMLHelpReader
	file = open(resolveFilename(SCOPE_PLUGINS, "Extensions/PluginSort/mphelp.xml"), 'r')
	reader = XMLHelpReader(file)
	file.close()
	pluginSortHelp = registerHelp(*reader)
except Exception as e:
	print("[PluginSort] Unable to initialize MPHelp:", e, "- Help not available!")
	pluginSortHelp = None
#pragma mark -

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=True,
		),
	]
