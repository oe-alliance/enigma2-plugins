# -*- coding: utf-8 -*-
# by 3c5x9@2008
from enigma import eTimer

from Screens.Screen import Screen

from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigInteger,ConfigYesNo
from Components.Network import iNetwork
from Plugins.Plugin import PluginDescriptor

from twisted.web import proxy, http
from twisted.internet import reactor


###############################################################################
config.plugins.httpproxy = ConfigSubsection()
config.plugins.httpproxy.enable = ConfigYesNo(default = True)
config.plugins.httpproxy.port = ConfigInteger(8080,limits = (1, 65536))
config.plugins.httpproxy.filter_hosts = ConfigYesNo(default = False)
config.plugins.httpproxy.filter_uri = ConfigYesNo(default = False)

global ALLOWED_CLIENTS,LOG_TO_STDOUT,URI_BLACKLIST
LOG_TO_STDOUT = False
ALLOWED_CLIENTS = ['192.168.1.3'] # only clients listed here with ther IP Adress passed
URI_BLACKLIST = ['microsoft','teen','porn'] # all uri s containig this words will be blocked


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
        self.list.append(getConfigListEntry(_("use Host Filter"), config.plugins.httpproxy.filter_hosts))
        self.list.append(getConfigListEntry(_("use URI Filter"), config.plugins.httpproxy.filter_uri))

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

class myProxyRequest(proxy.ProxyRequest):
    RESPONSE_CLIENTED_DENIED = "this client it not allowed to connect"
    ports = {'http': 80}

    def process(self):
        global URI_BLACKLIST
        check_passed = True
        if config.plugins.httpproxy.filter_hosts.value is True:
            if self.checkClientAccess(self.client) is not True:
                self.logMessage('BLOCKED/HOST_FILTER')
                self.renderResponse(self.RESPONSE_CLIENTED_DENIED)
                check_passed = False

        if check_passed is True and config.plugins.httpproxy.filter_uri.value is True:
            for i in URI_BLACKLIST:
                if self.uri.find(i) > 0:
                    self.logMessage('BLOCKED/URI_FILTER')
                    self.renderResponse('''<H1>Could not connect due to security issues</H1>''')
                    check_passed = False
                    break

        if check_passed:
            self.logMessage('OK')
            proxy.ProxyRequest.process(self)

    def renderResponse(self,message):
        self.transport.write("HTTP/1.0 200 blocked\r\n")
        self.transport.write("Content-Type: text/html\r\n")
        self.transport.write("\r\n")
        self.transport.write('<H1>%s</H1>'%message)
        self.transport.stopProducing()

    def checkClientAccess(self,client):
        global ALLOWED_CLIENTS
        if client.host not in ALLOWED_CLIENTS:
            return False
        else:
            return True

    def logMessage(self,status):
        global LOG_TO_STDOUT
        if LOG_TO_STDOUT:
            try:
                print "[PROXY]",self.client.host,self.uri,status
            except Exception:
                ''' now i am quite careful with logging webstuff with E2 '''
                pass

class ProxyProtocol(proxy.Proxy):
    requestFactory = myProxyRequest

class ProxyFactory(http.HTTPFactory):
        protocol = ProxyProtocol

###############################################################################
def main(session, **kwargs):
    """ open config screen """
    session.open(HTTPProxyConfigScreen)

def autostart(reason,**kwargs):
    """ start proxy in background """
    if reason is True and config.plugins.httpproxy.enable.value is True:
        try:
            for adaptername in iNetwork.ifaces:
                extip = iNetwork.ifaces[adaptername]['ip']
                if iNetwork.ifaces[adaptername]['up'] is True:
                    extip = "%i.%i.%i.%i" % (extip[0], extip[1], extip[2], extip[3])
                    print "starting proxy on ",extip,":", config.plugins.httpproxy.port.value
                    reactor.listenTCP(int(config.plugins.httpproxy.port.value), ProxyFactory(),interface=extip)
        except Exception,e:
            print "starting the http proxy failed!"
            print e


def Plugins(**kwargs):
  return [
          PluginDescriptor(name="HTTP Proxy",description="use your receiver as Web Proxy",where = PluginDescriptor.WHERE_PLUGINMENU,fnc = main),
          PluginDescriptor(where = [PluginDescriptor.WHERE_NETWORKCONFIG_READ], fnc = autostart)
          ]

