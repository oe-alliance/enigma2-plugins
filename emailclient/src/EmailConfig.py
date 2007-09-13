from Screens.Screen import Screen
from Components.config import config, getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.ActionMap import ActionMap
       
class EmailConfigScreen(ConfigListScreen,Screen):
    skin = """
        <screen position="100,100" size="550,400" title="Email Setup" >
        <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
        <widget name="buttonred" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        <widget name="buttongreen" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        <widget name="info" position="240,360" size="100,40" halign="right" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        </screen>"""
    def __init__(self, session, args = 0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("Username"), config.plugins.emailimap.username))
        self.list.append(getConfigListEntry(_("Password"), config.plugins.emailimap.password))
        self.list.append(getConfigListEntry(_("IMAP Server"), config.plugins.emailimap.server))
        self.list.append(getConfigListEntry(_("IMAP Port"), config.plugins.emailimap.port))
        self.list.append(getConfigListEntry(_("max of Headers to load"), config.plugins.emailimap.maxheadertoload))
        
        ConfigListScreen.__init__(self, self.list)
        self["buttonred"] = Label(_("cancel"))
        self["buttongreen"] = Label(_("ok"))
        self["info"] = Label('by 3c5x9')
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
