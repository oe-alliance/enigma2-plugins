from Screens.Screen import Screen
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ActionMap import ActionMap
       
class LastFMConfigScreen(ConfigListScreen,Screen):
    skin = """
        <screen position="center,center" size="600,400" title="Last.FM Setup" >
        
        <widget name="config" position="10,0" size="580,320" scrollbarMode="showOnDemand" />
        
        <widget name="buttonred" position="10,350" size="140,40" valign=\"center\" halign=\"center\" zPosition=\"2\" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" font=\"Regular;18\" />          
        <widget name="buttongreen" position="150,350" size="140,40" valign=\"center\" halign=\"center\" zPosition=\"2\" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" font=\"Regular;18\"/>            
        <ePixmap pixmap="skin_default/buttons/red.png" position="10,350" zPosition="1" size="140,40" transparent="1" alphatest="on" />
        <ePixmap pixmap="skin_default/buttons/green.png" position="150,350" zPosition="1" size="140,40" transparent="1" alphatest="on" />

        </screen>"""
    def __init__(self, session, args = 0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("Last.FM Username"), config.plugins.LastFM.username))
        self.list.append(getConfigListEntry(_("Password"), config.plugins.LastFM.password))
        self.list.append(getConfigListEntry(_("Send now playing Audio Tracks"), config.plugins.LastFM.sendSubmissions))
        self.list.append(getConfigListEntry(_("Use LastFM Proxy"), config.plugins.LastFM.useproxy))
        self.list.append(getConfigListEntry(_("LastFM Proxy port"), config.plugins.LastFM.proxyport))
        self.list.append(getConfigListEntry(_("Recommendation level"), config.plugins.LastFM.recommendedlevel))
        self.list.append(getConfigListEntry(_("Show Coverart"), config.plugins.LastFM.showcoverart))
        self.list.append(getConfigListEntry(_("Timeout Statustext (seconds)"), config.plugins.LastFM.timeoutstatustext))
        self.list.append(getConfigListEntry(_("Timeout to select a Tab (seconds)"), config.plugins.LastFM.timeouttabselect))
        self.list.append(getConfigListEntry(_("Interval to refresh Metadata (seconds)"), config.plugins.LastFM.metadatarefreshinterval))

        self.list.append(getConfigListEntry(_("Use Screensaver"), config.plugins.LastFM.sreensaver.use))
        self.list.append(getConfigListEntry(_("Wait before Screensaver"), config.plugins.LastFM.sreensaver.wait))
        self.list.append(getConfigListEntry(_("Show Coverart in Screensaver"), config.plugins.LastFM.sreensaver.showcoverart))
        self.list.append(getConfigListEntry(_("Show Coverart Animation in Screensaver"), config.plugins.LastFM.sreensaver.coverartanimation))
        self.list.append(getConfigListEntry(_("Speed for Coverart Animation"), config.plugins.LastFM.sreensaver.coverartspeed))
        self.list.append(getConfigListEntry(_("Interval for Coverart Animation"), config.plugins.LastFM.sreensaver.coverartinterval))
        
        ConfigListScreen.__init__(self, self.list)
        self["buttonred"] = Label(_("Cancel"))
        self["buttongreen"] = Label(_("OK"))
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
