# -*- coding: utf-8 -*-
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from enigma import eTimer
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigText, ConfigSelection, ConfigSubsection, ConfigYesNo
from urllib2 import Request, urlopen
from base64 import encodestring
global sessions
from twisted.internet import reactor

sessions = []

config.plugins.DynDNS = ConfigSubsection()
config.plugins.DynDNS.enable = ConfigYesNo(default = False)
config.plugins.DynDNS.interval = ConfigSelection(default = "10", choices = [("5", _("5 min.")),("10", _("10 min.")),("15", _("15 min.")),("30", _("30 min.")),("60", _("60 min."))])
config.plugins.DynDNS.hostname = ConfigText(default = "", fixed_size = False)
config.plugins.DynDNS.user = ConfigText(default = "", fixed_size = False)
config.plugins.DynDNS.password = ConfigText(default = "", fixed_size = False)

class DynDNSScreenMain(ConfigListScreen,Screen):
    skin = """
        <screen position="100,100" size="550,400" title="DynDNS Setup" >
        <widget name="config" position="0,0" size="550,300" scrollbarMode="showOnDemand" />
        <widget name="buttonred" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
        <widget name="buttongreen" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
        </screen>"""
    def __init__(self, session, args = 0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("activate DynDNS"), config.plugins.DynDNS.enable))
        self.list.append(getConfigListEntry(_("Interval to check IP-Adress"), config.plugins.DynDNS.interval))
        self.list.append(getConfigListEntry(_("Hostname"), config.plugins.DynDNS.hostname))
        self.list.append(getConfigListEntry(_("Username"), config.plugins.DynDNS.user))
        self.list.append(getConfigListEntry(_("Password"), config.plugins.DynDNS.password))
        ConfigListScreen.__init__(self, self.list)
        self["buttonred"] = Label(_("cancel"))
        self["buttongreen"] = Label(_("ok"))
        self["setupActions"] = ActionMap(["SetupActions"],
        {
            "green": self.save,
            "red": self.cancel,
            "save": self.save,
            "cancel": self.cancel,
            "ok": self.save,
        }, -2)

    def save(self):
        print "[DynDNS] saving config"
        for x in self["config"].list:
            x[1].save()
        self.close(True)

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close(False)

class DynDNSService:
	enabled = False
	sessions = []
	lastip = ""
	def __init__(self):
		self.timer = eTimer()
		self.timer.timeout.get().append(self.checkCurrentIP)

	def enable(self):
		if config.plugins.DynDNS.enable.value:
			self.enabled = True
			reactor.callLater(1, self.checkCurrentIP)

	def disable(self):
		if self.enabled:
			self.timer.stop()
			self.enabled = False

	def addSession(self,session):
		self.sessions.append(session)

	def checkCurrentIP(self):
		print "[DynDNS] checking IP"
		try:
			html = self.getURL("http://checkip.dyndns.org")
			str = html.split("<body>")[1]
			str = str.split("</body>")[0]
			str = str.split(":")[1]
			str = str.lstrip().rstrip()

			if self.lastip != str:
				self.lastip=str
				reactor.callLater(1, self.onIPchanged)
			self.timer.start(int(config.plugins.DynDNS.interval.value)*60000)
		except Exception,e:
			print "[DynDNS]",e
			str = "coundnotgetip"

	def onIPchanged(self):
		print "[DynDNS] IP change, setting new one",self.lastip
		try:
			url = "http://members.dyndns.org/nic/update?system=dyndns&hostname=%s&myip=%s&wildcard=ON&offline=NO"%(config.plugins.DynDNS.hostname.value,self.lastip)
			if self.getURL(url).find("good") is not -1:
				print "[DynDNS] ip changed"
		except Exception,e:
			print "[DynDNS] ip was not changed",e

	def getURL(self,url):
		request =  Request(url)
   		base64string = encodestring('%s:%s' % (config.plugins.DynDNS.user.value,config.plugins.DynDNS.password.value))[:-1]
   		request.add_header("Authorization", "Basic %s" % base64string)
   		htmlFile = urlopen(request)
   		htmlData = htmlFile.read()
   		htmlFile.close()
   		return htmlData

def onPluginStart(session, **kwargs):
	session.openWithCallback(onPluginStartCB,DynDNSScreenMain)

def onPluginStartCB(changed):
	print "[DynDNS] config changed=",changed
	global dyndnsservice
	if changed:
		dyndnsservice.disable()
		dyndnsservice.enable()

global dyndnsservice
dyndnsservice = DynDNSService()

def onSessionStart(reason, **kwargs):
	global dyndnsservice
	if config.plugins.DynDNS.enable.value is not False:
		if "session" in kwargs:
			dyndnsservice.addSession(kwargs["session"])
		if reason == 0:
			dyndnsservice.enable()
		elif reason == 1:
			dyndnsservice.disable()

def Plugins(path,**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = onSessionStart),
		    PluginDescriptor(name=_("DynDNS"), description=_("use www.DynDNS.org on your Box"),where = [PluginDescriptor.WHERE_PLUGINMENU], fnc = onPluginStart, icon="icon.png")]

