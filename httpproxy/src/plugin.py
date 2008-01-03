# by 3c5x9@2008
from enigma import eTimer

from Screens.Screen import Screen

from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigInteger,ConfigYesNo
from Components.Network import Network
from Plugins.Plugin import PluginDescriptor

from twisted.web import proxy, http
from twisted.internet import reactor


###############################################################################
config.plugins.httpproxy = ConfigSubsection()
config.plugins.httpproxy.enable = ConfigYesNo(default = True)
config.plugins.httpproxy.port = ConfigInteger(8080,limits = (1, 65536))

###############################################################################
class HTTPProxyConfigScreen(ConfigListScreen,Screen):
    skin = """
        <screen position="100,100" size="550,400" title="HTTP Proxy Setup" >
        <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
        <widget name="buttonred" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
        <widget name="buttongreen" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
        </screen>"""

    def __init__(self, session, args = 0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("start HTTP Proxy"), config.plugins.httpproxy.enable))
        self.list.append(getConfigListEntry(_("use Port"), config.plugins.httpproxy.port))

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
        print "saving"
        for x in self["config"].list:
            x[1].save()
        self.close(True,self.session)

    def cancel(self):
        print "cancel"
        for x in self["config"].list:
            x[1].cancel()
        self.close(False,self.session)

###############################################################################
class ProxyFactory(http.HTTPFactory):
        protocol = proxy.Proxy

###############################################################################
def main(session, **kwargs):
    """ open config screen """
    session.open(HTTPProxyConfigScreen)

def autostart(**kwargs):
    """ start proxy in background """
    if config.plugins.httpproxy.enable.value:
        try:
            nw = Network()
            for adaptername in nw.ifaces:
                extip = nw.ifaces[adaptername]['ip']
                if nw.ifaces[adaptername]['up'] is True:
                    extip = "%i.%i.%i.%i"%(extip[0],extip[1],extip[2],extip[3])
                    print "starting proxy on ",extip,":", config.plugins.httpproxy.port.value
                    reactor.listenTCP(int(config.plugins.httpproxy.port.value), ProxyFactory(),interface=extip)
        except Exception,e:
            print "starting the http proxy failed!"
            print e

def Plugins(**kwargs):
  return [
          PluginDescriptor(name="HTTP Proxy",description="use your Dreambox as Web Proxy",where = PluginDescriptor.WHERE_PLUGINMENU,fnc = main),
          PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart)
          ]

