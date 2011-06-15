# GUI (Screens)
from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen

# GUI (Summary)
from Screens.Setup import SetupSummary

# GUI (Components)
from Components.ActionMap import ActionMap
from Components.SelectionList import SelectionList, SelectionEntryComponent
from Components.Sources.StaticText import StaticText

# Configuration
from Components.config import config

from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

LIST_PLUGINS = 0
LIST_EXTENSIONS = 1
class PluginHiderSetup(Screen):
	skin = """<screen name="PluginHiderSetup" title="PluginHider Setup" position="center,center" size="565,290">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="list" position="5,45" size="555,240" scrollbarMode="showOnDemand" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)

		# Initialize widgets
		self["key_green"] = StaticText(_("OK"))
		self["key_red"] = StaticText(_("Cancel"))
		self["key_yellow"] = StaticText(_("Plugins"))
		self["key_blue"] = StaticText(_("Extensions"))

		self["list"] = SelectionList([])
		self.selectedList = LIST_PLUGINS
		self.updateList()

		self["ColorActions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"ok": self["list"].toggleSelection,
				"red": self.cancel,
				"green": self.save,
				"yellow": self.plugins,
				"blue": self.extensions,
			}, -1
		)

		self.onLayoutFinish.append(self.setCustomTitle)

	def cancel(self):
		config.plugins.pluginhider.hideplugins.cancel()
		config.plugins.pluginhider.hideextensions.cancel()
		config.plugins.pluginhider.cancel()
		self.close()

	def save(self):
		self.keepCurrent()
		config.plugins.pluginhider.hideplugins.save()
		config.plugins.pluginhider.hideextensions.save()
		config.plugins.pluginhider.save()
		self.close()

	def plugins(self):
		self.keepCurrent()
		self.selectedList = LIST_PLUGINS
		self.updateList()

	def extensions(self):
		self.keepCurrent()
		self.selectedList = LIST_EXTENSIONS
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
		else:
			list = fnc([PluginDescriptor.WHERE_EXTENSIONSMENU])
			selected = config.plugins.pluginhider.hideextensions.value

		res = []
		i = 0
		for plugin in list:
			if plugin.description:
				name = "%s (%s)" % (plugin.name, plugin.description)
			else:
				name = plugin.name

			res.append(SelectionEntryComponent(
					name,
					plugin.name,
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
			config.plugins.pluginhider.hideplugins.value = [x[1] for x in selected]
		else:
			config.plugins.pluginhider.hideextensions.value = [x[1] for x in selected]
