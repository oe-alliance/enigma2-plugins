import Plugins.Plugin
from Components.config import config
from Components.config import ConfigSubsection
from Components.config import ConfigSelection
from Components.config import ConfigInteger
from Components.config import ConfigSubList
from Components.config import ConfigSubDict
from Components.config import ConfigText
from Components.config import configfile
from Components.config import ConfigYesNo
from Components.Network import iNetwork
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os,gettext

__version__ = "1.5beta2"

PluginLanguageDomain = "WebInterface"
PluginLanguagePath = "Extensions/WebInterface/locale"

def localeInit():
    lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
    os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
    print "[WebInterface] set language to ", lang
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        print "[WebInterface] fallback to default translation for", txt
        t = gettext.gettext(txt)
    return t
    
localeInit()
language.addCallback(localeInit)


config.plugins.Webinterface = ConfigSubsection()
config.plugins.Webinterface.enable = ConfigYesNo(default = True)
config.plugins.Webinterface.allowzapping = ConfigYesNo(default = True)
config.plugins.Webinterface.includehdd = ConfigYesNo(default = False)
config.plugins.Webinterface.autowritetimer = ConfigYesNo(default = False)
config.plugins.Webinterface.loadmovielength = ConfigYesNo(default = False)
config.plugins.Webinterface.version = ConfigText(__version__) # used to make the versioninfo accessible enigma2-wide, not confgurable in GUI. 
config.plugins.Webinterface.interfacecount = ConfigInteger(0)
config.plugins.Webinterface.interfaces = ConfigSubList()
config.plugins.Webinterface.warningsslsend = ConfigYesNo(default = False)


def addInterfaceConfig():
    choices = getCofiguredAndSpecialNetworkinterfaces()
    i = len(config.plugins.Webinterface.interfaces)
    config.plugins.Webinterface.interfaces.append(ConfigSubsection())
    config.plugins.Webinterface.interfaces[i].disabled = ConfigYesNo(default = False)
    config.plugins.Webinterface.interfaces[i].address = ConfigSelection(choices,default=choices[0])
    config.plugins.Webinterface.interfaces[i].port = ConfigInteger(80, (0,65535))
    config.plugins.Webinterface.interfaces[i].useauth = ConfigYesNo(default = False)
    config.plugins.Webinterface.interfaces[i].usessl = ConfigYesNo(default = False)
    config.plugins.Webinterface.interfacecount.value = i+1
    return i

def getCofiguredAndSpecialNetworkinterfaces():
    nw = iNetwork
    choices = []
    choices.append('0.0.0.0')
    choices.append('127.0.0.1')
    for adaptername in nw.ifaces:
        extip = nw.ifaces[adaptername]['ip']
        if nw.ifaces[adaptername]['up'] is True:
            extip = "%i.%i.%i.%i"%(extip[0],extip[1],extip[2],extip[3])
            choices.append(extip)
    return choices

if config.plugins.Webinterface.interfacecount.value == 0:
    # setting default interface
    # 0.0.0.0:80 auth=False
    config.plugins.Webinterface.interfaces.append(ConfigSubsection())
    config.plugins.Webinterface.interfaces[0].disabled = ConfigYesNo(default = False)
    
    #needs to be refreshed before each call, because ifaces can be changed since e2 boot 
    config.plugins.Webinterface.interfaces[0].address = ConfigSelection(getCofiguredAndSpecialNetworkinterfaces(),default='0.0.0.0')
    
    config.plugins.Webinterface.interfaces[0].port = ConfigInteger(80, (0,65535))
    config.plugins.Webinterface.interfaces[0].useauth = ConfigYesNo(default = False)
    config.plugins.Webinterface.interfaces[0].usessl = ConfigYesNo(default = False)
    config.plugins.Webinterface.interfacecount.value = 1
    config.plugins.Webinterface.interfacecount.save()
    config.plugins.Webinterface.interfaces[0].save()
else:    
    for i in range(0, config.plugins.Webinterface.interfacecount.value):
        addInterfaceConfig()

