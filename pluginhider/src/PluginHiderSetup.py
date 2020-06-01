from . import _

# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.HelpMenu import HelpableScreen
from Screens.MessageBox import MessageBox
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import HelpableActionMap
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.Sources.StaticText import StaticText
from Components.Pixmap import MultiPixmap

# Configuration
from Components.config import config

from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

import inspect

LIST_PLUGINS = 0
LIST_EXTENSIONS = 1
LIST_EVENTINFO = 2
class PluginHiderSetup(Screen, HelpableScreen):
	skin = """<screen name="PluginHiderSetup" title="PluginHider Setup" position="center,center" size="565,395">
		<ePixmap position="0,358" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,358" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,358" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,358" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,358" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,358" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,358" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,358" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<ePixmap size="551,336" alphatest="on" position="5,21" pixmap="skin_default/border_epg.png" zPosition="3" />
		<widget size="320,25" alphatest="on" position="5,1" zPosition="1" name="tabbar" pixmaps="skin_default/epg_now.png,skin_default/epg_next.png,skin_default/epg_more.png" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="5,1" zPosition="2" source="plugins" render="Label" halign="center" font="Regular;18" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="111,1" zPosition="2" source="extensions" render="Label" halign="center" font="Regular;18" />
		<widget valign="center" transparent="1" size="108,22" backgroundColor="#25062748" position="216,1" zPosition="2" source="eventinfo" render="Label" halign="center" font="Regular;18" />
		<widget name="list" position="11,26" size="540,330" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		# Initialize widgets
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_yellow"] = StaticText("")
		self["key_blue"] = StaticText(_("Run"))
		self["plugins"] = StaticText(_("Plugins"))
		self["extensions"] = StaticText(_("Extensions"))
		self["eventinfo"] = StaticText(_("Eventinfo"))
		self["tabbar"] = MultiPixmap()

		self["list"] = SelectionList([])
		self.selectedList = LIST_PLUGINS
		self.updateList()

		self["PluginHiderSetupActions"] = HelpableActionMap(self, "PluginHiderSetupActions",
			{
				"ok": (self["list"].toggleSelection, _("toggle selection")),
				"cancel": (self.cancel, _("end editing")),
				"green": (self.save, _("save")),
				"blue": (self.run, _("run selected plugin")),
				"next": (self.next, _("select next tab")),
				"previous": (self.previous, _("select previous tab")),
			}, -1
		)

		self.onLayoutFinish.append(self.setCustomTitle)

	def run(self):
		cur = self["list"].getCurrent()
		cur = cur and cur[0]
		if cur:
			plugin = cur[1]

			if self.selectedList == LIST_PLUGINS:
				plugin(session=self.session)
			else: #if self.selectedList == LIST_EXTENSIONS or self.selectedList == LIST_EVENTINFO:
				from Screens.InfoBar import InfoBar
				instance = InfoBar.instance
				args = inspect.getargspec(plugin.__call__)[0]
				if len(args) == 1:
					plugin(session=self.session)
				elif instance and instance.servicelist:
					plugin(session=self.session, servicelist=instance.servicelist)
				else:
					session.open(MessageBox, _("Could not start Plugin:") + "\n" + _("Unable to access InfoBar."), type=MessageBox.TYPE_ERROR)

	def cancel(self):
		config.plugins.pluginhider.hideplugins.cancel()
		config.plugins.pluginhider.hideextensions.cancel()
		self.close()

	def save(self):
		self.keepCurrent()
		config.plugins.pluginhider.save()
		self.close()

	def previous(self):
		self.keepCurrent()
		self.selectedList -= 1
		if self.selectedList < 0:
			self.selectedList = LIST_EVENTINFO
		self.updateList()

	def next(self):
		self.keepCurrent()
		self.selectedList += 1
		if self.selectedList > LIST_EVENTINFO:
			self.selectedList = LIST_PLUGINS
		self.updateList()

	def setCustomTitle(self):
		self.setTitle(_("PluginHider Setup"))

	def updateList(self):
		if hasattr(plugins, 'pluginHider_baseGetPlugins'):
			fnc = plugins.pluginHider_baseGetPlugins
		else:
			fnc = plugins.getPlugins

		if self.selectedList == LIST_PLUGINS:
			list = fnc([PluginDescriptor.WHERE_PLUGINMENU])
			selected = config.plugins.pluginhider.hideplugins.value
		elif self.selectedList == LIST_EXTENSIONS:
			list = fnc([PluginDescriptor.WHERE_EXTENSIONSMENU])
			selected = config.plugins.pluginhider.hideextensions.value
		else: #if self.selectedList == LIST_EVENTINFO:
			list = fnc([PluginDescriptor.WHERE_EVENTINFO])
			selected = config.plugins.pluginhider.hideeventinfo.value
		self["tabbar"].setPixmapNum(self.selectedList)

		res = []
		i = 0
		for plugin in list:
			if plugin.description:
				name = "%s (%s)" % (plugin.name, plugin.description)
			else:
				name = plugin.name

			res.append(SelectionEntryComponent(
					name,
					plugin,
					i,
					plugin.name in selected,
			))
			i += 1
		self["list"].setList(res)
		if res:
			self["list"].moveToIndex(0)

	def keepCurrent(self):
		selected = self["list"].getSelectionsList()
		if self.selectedList == LIST_PLUGINS:
			config.plugins.pluginhider.hideplugins.value = [x[1].name for x in selected]
		elif self.selectedList == LIST_EXTENSIONS:
			config.plugins.pluginhider.hideextensions.value = [x[1].name for x in selected]
		else: #if self.selectedList == LIST_EVENTINFO:
			config.plugins.pluginhider.hideeventinfo.value = [x[1].name for x in selected]
