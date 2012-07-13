#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Plugins.Plugin import PluginDescriptor
from Tools.HardwareInfo import HardwareInfo
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigDirectory, ConfigYesNo, Config, ConfigText
from InternetRadioScreen import InternetRadioScreen

# for localized messages
from . import _


config.plugins.internetradio = ConfigSubsection()
config.plugins.internetradio.showinextensions = ConfigYesNo(default = True)
config.plugins.internetradio.dirname = ConfigDirectory(default = "/hdd/streamripper/")
config.plugins.internetradio.riptosinglefile = ConfigYesNo(default = False)
config.plugins.internetradio.createdirforeachstream = ConfigYesNo(default = True)
config.plugins.internetradio.addsequenceoutputfile = ConfigYesNo(default = False)
config.plugins.internetradio.filter = ConfigText(default=_("Countries"))
if HardwareInfo().get_device_name() == "dm500hd":
	config.plugins.internetradio.visualization = ConfigSelection(choices = [("2", _("On")), ("3", _("Off"))], default = "2")
else:
	config.plugins.internetradio.visualization = ConfigSelection(choices = [("0", _("Screen and OLED")), ("1", _("OLED only")), ("2", _("Screen only")), ("3", _("Off"))], default = "2")
config.plugins.internetradio.googlecover = ConfigYesNo(default = False)
config.plugins.internetradio.startupname = ConfigText(default = "")
config.plugins.internetradio.startuptext = ConfigText(default = "")
config.plugins.internetradio.fullscreenautoactivation = ConfigSelection(choices = [("30", _("30 seconds")), ("60", _("1 minutes")), ("180", _("3 minutes")), ("-1", _("Off"))], default = "30")
config.plugins.internetradio.fullscreenlayout = ConfigSelection(choices = [("0", _("Visualization and Text")), ("1", _("Text only")), ("2", _("Blank"))], default = "0")


def sessionstart(reason, **kwargs):
	if reason == 0 and "session" in kwargs:
		try:
			from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
			from Plugins.Extensions.WebInterface.WebChilds.Screenpage import ScreenPage
			from twisted.python import util
			from twisted.web import static
			if hasattr(static.File, 'render_GET'):
				class File(static.File):
					def render_POST(self, request):
						return self.render_GET(request)
			else:
				File = static.File
			session = kwargs["session"]
			root = File(util.sibpath(__file__, "web-data"))
			root.putChild("web", ScreenPage(session, util.sibpath(__file__, "web"), True))
			addExternalChild( ("internetradio", root, "Internet-Radio", "1", True) )
		except ImportError:
			pass # pah!

def main(session,**kwargs):
	session.open(InternetRadioScreen)

def Plugins(**kwargs):
	list = [PluginDescriptor(name="Internet-Radio", description=_("listen to internet-radio"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main)] # always show in plugin menu
	if config.plugins.internetradio.showinextensions.value:
		list.append (PluginDescriptor(name="Internet-Radio", description=_("listen to internet-radio"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main))
	list.append (PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False))
	return list

