from enigma import *
from Screens.Screen import Screen
from Components.config import config, getConfigListEntry
from Components.ConfigList import *
from Components.Label import Label
from Components.ActionMap import ActionMap
       
class LastFMConfigScreen(ConfigListScreen,Screen):
    skin = """
        <screen position="100,100" size="550,400" title="Last.FM Setup" >
        <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
        <widget name="buttonred" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        <widget name="buttongreen" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        </screen>"""
    def __init__(self, session, args = 0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("Last.FM Username"), config.plugins.LastFM.username))
        self.list.append(getConfigListEntry(_("Password"), config.plugins.LastFM.password))
        self.list.append(getConfigListEntry(_("Recommentation Level"), config.plugins.LastFM.recommendedlevel))
        self.list.append(getConfigListEntry(_("show Coverart"), config.plugins.LastFM.showcoverart))
        self.list.append(getConfigListEntry(_("Timeout Statustext (Seconds)"), config.plugins.LastFM.timeoutstatustext))
        self.list.append(getConfigListEntry(_("Timeout to select a Tab (Seconds)"), config.plugins.LastFM.timeouttabselect))
        self.list.append(getConfigListEntry(_("Interval to refresh Metadata (Seconds)"), config.plugins.LastFM.metadatarefreshinterval))

        self.list.append(getConfigListEntry(_("use Screensaver"), config.plugins.LastFM.sreensaver.use))
        self.list.append(getConfigListEntry(_("wait before Screensaver"), config.plugins.LastFM.sreensaver.wait))
        self.list.append(getConfigListEntry(_("show Coverart in Screensaver"), config.plugins.LastFM.sreensaver.showcoverart))
        self.list.append(getConfigListEntry(_("do Coverartanimation in Screensaver"), config.plugins.LastFM.sreensaver.coverartanimation))
        self.list.append(getConfigListEntry(_("Speed for Coverartanimation"), config.plugins.LastFM.sreensaver.coverartspeed))
        self.list.append(getConfigListEntry(_("Interval for Coverartanimation"), config.plugins.LastFM.sreensaver.coverartinterval))
        
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
        self.close(True)

    def cancel(self):
        print "cancel"
        for x in self["config"].list:
            x[1].cancel()
        self.close(False)
