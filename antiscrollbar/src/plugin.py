from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.MenuList import MenuList
from Components.Input import Input
from Plugins.Plugin import PluginDescriptor
from enigma import iPlayableService
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigSubList, ConfigInteger, ConfigYesNo, ConfigText, ConfigSelection
from Components.ConfigList import ConfigListScreen
#############
from enigma import ePoint, eSize


###############################################################################
myname = "AntiScrollbar"

config.plugins.antiscrollbar = ConfigSubsection()
config.plugins.antiscrollbar.autostart = ConfigYesNo(default=True)
config.plugins.antiscrollbar.modescount = ConfigInteger(0)
config.plugins.antiscrollbar.mode = ConfigSubList()

def initConfig():
    modescount = config.plugins.antiscrollbar.modescount.value
    if modescount == 0:
        pass
    else:
        i = 0
        while i < modescount:
            print "[" + myname + ".initConfig] i is %s" % i
            config.plugins.antiscrollbar.mode.append(ConfigSubsection())
            config.plugins.antiscrollbar.mode[i].sref = ConfigText("")
            config.plugins.antiscrollbar.mode[i].sizex = ConfigInteger(0)
            config.plugins.antiscrollbar.mode[i].sizey = ConfigInteger(0)
            config.plugins.antiscrollbar.mode[i].posx = ConfigInteger(0)
            config.plugins.antiscrollbar.mode[i].posy = ConfigInteger(0)
            config.plugins.antiscrollbar.mode[i].enabled = ConfigYesNo(default=True)

            config.plugins.antiscrollbar.modescount.value = i + 1

            i += 1

initConfig()

def readConfig():
    srefs = {}
    for mode in config.plugins.antiscrollbar.mode:
        sref = mode.sref.value
        sizex = mode.sizex.value
        sizey = mode.sizey.value
        posx = mode.posx.value
        posy = mode.posy.value
        enabled = mode.enabled.value
        srefs[sref] = [sizex, sizey, posx, posy, enabled]
    return srefs

###############################################################################
class AntiScrollOverlay(Screen):
    def __init__(self, session):
        self.size = [0, 0]
        self.position = [0, 0]
        ss = "<screen position=\"0,0\" size=\"0,0\" title=\"AntiScrollOverlay\"  flags=\"wfNoBorder\" zPosition=\"-1\" backgroundColor=\"#FF000000\">"
        ss += "<widget name=\"label\" position=\"1,1\" size=\"0,0\"  backgroundColor=\"#00000000\" />"
        ss += "</screen>"
        self.skin = ss
        self.session = session
        Screen.__init__(self, session)
        self["label"] = Label()
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
                iPlayableService.evUpdatedInfo: self.evStart,
                iPlayableService.evEOF: self.hide,
            })
        self.hide()

    def evStart(self):
        service = self.session.nav.getCurrentlyPlayingServiceReference()
        if service is None:
            return
        srefs = readConfig()
        if service.toString() in srefs:
            data = srefs[service.toString()]
            if data[4]:
                self.resize(data[0], data[1])
                self.move(data[2], data[3])
                self.show()
            else:
                self.hide()
        else:
            self.hide()

    def move(self, x, y):
      self.instance.move(ePoint(x, y))

    def resize(self, w, h):
      self.instance.resize(eSize(*(w, h)))
      self["label"].instance.resize(eSize(*(w - 2, h - 2)))


#############################
class AntiScrollConfig(ConfigListScreen, Screen):
    skin = """
        <screen position="100,100" size="550,400" title="%s">
            <widget name="config" position="5,5" size="540,360" scrollbarMode="showOnDemand" zPosition="1"/>

            <widget name="key_red" position="0,360" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
            <widget name="key_green" position="140,360" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
            <widget name="key_yellow" position="280,360" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>

            <ePixmap name="red" pixmap="skin_default/buttons/red.png" position="0,360" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
            <ePixmap name="green" pixmap="skin_default/buttons/green.png" position="140,360" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
            <ePixmap name="yellow" pixmap="skin_default/buttons/yellow.png" position="280,360" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
        </screen>""" % _(myname + ": Main Setup")

    def __init__(self, session, args=0):
        Screen.__init__(self, session)
        l = [
            getConfigListEntry(_("Start on Sessionstart"), config.plugins.antiscrollbar.autostart),
        ]

        ConfigListScreen.__init__(self, l)
        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("OK"))
        self["key_yellow"] = Button(_("current Service"))
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "red": self.cancel,
            "green": self.save,
            "yellow": self.openCurrentSeviceConfig,
            "save": self.save,
            "cancel": self.cancel,
            "ok": self.save,
        }, -2)

    def openCurrentSeviceConfig(self):
        print "yellow"
        smode = False
        for mode in config.plugins.antiscrollbar.mode:
            if mode.sref.value == self.session.nav.getCurrentlyPlayingServiceReference().toString():
                smode = mode
        if smode is False:
            print "new config " * 40
            i = config.plugins.antiscrollbar.modescount.value
            config.plugins.antiscrollbar.mode.append(ConfigSubsection())
            config.plugins.antiscrollbar.mode[i].sref = ConfigText("")
            config.plugins.antiscrollbar.mode[i].sizex = ConfigInteger(200)
            config.plugins.antiscrollbar.mode[i].sizey = ConfigInteger(200)
            config.plugins.antiscrollbar.mode[i].posx = ConfigInteger(100)
            config.plugins.antiscrollbar.mode[i].posy = ConfigInteger(50)
            config.plugins.antiscrollbar.mode[i].enabled = ConfigYesNo(default=True)

            config.plugins.antiscrollbar.mode[i].save()
            config.plugins.antiscrollbar.mode[i].sref.value = self.session.nav.getCurrentlyPlayingServiceReference().toString()
            config.plugins.antiscrollbar.mode[i].save()

            config.plugins.antiscrollbar.modescount.value += 1
            config.plugins.antiscrollbar.modescount.save()
            smode = config.plugins.antiscrollbar.mode[i]
        self.session.open(CurrentSeviceConfig, smode)

    def save(self):
        print "saving"
        for x in self["config"].list:
            x[1].save()
        self.close(True, self.session)

    def cancel(self):
        print "cancel"
        for x in self["config"].list:
            x[1].cancel()
        self.close(False, self.session)

class CurrentSeviceConfig(Screen):
    step = 5
    def __init__(self, session, mode):
        print "editing " + mode.sref.value
        self.mode = mode
        self.size = [mode.sizex.value, mode.sizey.value]
        self.enabled = mode.enabled.value
        self.position = [mode.posx.value, mode.posy.value]
        ss = "<screen position=\"%i,%i\" size=\"%i,%i\" title=\"%s\"  flags=\"wfNoBorder\" >" % (mode.posx.value, mode.posy.value, mode.sizex.value, mode.sizey.value, myname)
        ss += "<widget name=\"label\" position=\"0,0\" size=\"%i,%i\"  backgroundColor=\"black\"  />" % (mode.sizex.value, mode.sizey.value)
        ss += "</screen>"
        self.skin = ss
        self.session = session
        Screen.__init__(self, session)

        self["label"] = Label()
        if self.enabled is not True:
            self["label"].setText("disabled")
        else:
            self["label"].setText("")

        self["actions"] = ActionMap(["WizardActions", "DirectionActions", "MenuActions", "NumberActions"],
            {
             "ok": self.go,
             "back": self.cancel,
             "down": self.down,
             "up": self.up,
             "left": self.left,
             "right": self.right,
             "2": self.key2,
             "8": self.key8,
             "4": self.key4,
             "6": self.key6,
             "0": self.key0,
                 }, -1)

    def go(self):
      self.mode.posx.value = self.position[0]
      self.mode.posy.value = self.position[1]
      self.mode.sizex.value = self.size[0]
      self.mode.sizey.value = self.size[1]
      self.mode.enabled.value = self.enabled
      self.mode.save()
      self.close()

    def cancel(self):
       self.close()

    def key0(self):
        if self.enabled:
            self.enabled = False
            self["label"].setText("disabled")
        else:
            self.enabled = True
            self["label"].setText("")

    def key2(self):
      self.size = [self.size[0], self.size[1] - self.step]
      self.resize(self.size[0], self.size[1])

    def key8(self):
      self.size = [self.size[0], self.size[1] + self.step]
      self.resize(self.size[0], self.size[1])

    def key4(self):
      self.size = [self.size[0] - self.step, self.size[1]]
      self.resize(self.size[0], self.size[1])

    def key6(self):
      self.size = [self.size[0] + self.step, self.size[1]]
      self.resize(self.size[0], self.size[1])

    def down(self):
      self.position = [self.position[0], self.position[1] + self.step]
      self.move(self.position[0], self.position[1])

    def up(self):
      self.position = [self.position[0], self.position[1] - self.step]
      self.move(self.position[0], self.position[1])

    def left(self):
      self.position = [self.position[0] - self.step, self.position[1]]
      self.move(self.position[0], self.position[1])

    def right(self):
      self.position = [self.position[0] + self.step, self.position[1]]
      self.move(self.position[0], self.position[1])

    def move(self, x, y):
      self.instance.move(ePoint(x, y))


    def resize(self, w, h):
      self.instance.resize(eSize(*(w, h)))
      self["label"].instance.resize(eSize(*(w, h)))

#############################

activebar = None


def main(session, **kwargs):
    global activebar
    try:
        if activebar.show:
            activebar.hide()
        session.openWithCallback(mainCB, AntiScrollConfig)
    except:
        session.openWithCallback(mainCB, AntiScrollConfig)

def mainCB(saved, session):
    global activebar, doshow
    if not activebar:
        activebar = session.instantiateDialog(AntiScrollOverlay)
    activebar.evStart()

def autostart(session, **kwargs):
    global activebar
    if config.plugins.antiscrollbar.autostart.value:
        activebar = session.instantiateDialog(AntiScrollOverlay)

def Plugins(**kwargs):
  return [PluginDescriptor(name=myname, description="overlay for scrolling bars", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main, icon="plugin.png"),
          PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=autostart)]
