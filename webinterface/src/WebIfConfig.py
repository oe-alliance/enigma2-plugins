Version = '$Header$';

from Screens.Screen import Screen
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ActionMap import ActionMap
        
class WebIfConfigScreen(ConfigListScreen,Screen):
    skin = """
        <screen position="100,100" size="550,400" title="Webinterface Setup" >
        <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
        <widget name="buttonred" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        <widget name="buttongreen" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        </screen>"""
    def __init__(self, session, args = 0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("start Webinterface"), config.plugins.Webinterface.enable))
        self.list.append(getConfigListEntry(_("use Authorization"), config.plugins.Webinterface.useauth))
        self.list.append(getConfigListEntry(_("use Port"), config.plugins.Webinterface.port))
        self.list.append(getConfigListEntry(_("enable /hdd"), config.plugins.Webinterface.includehdd))
        self.list.append(getConfigListEntry(_("write debug-file"), config.plugins.Webinterface.debug))
        self.list.append(getConfigListEntry(_("autowrite timer"), config.plugins.Webinterface.autowritetimer))
        self.list.append(getConfigListEntry(_("load movie-length"), config.plugins.Webinterface.loadmovielength))
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
