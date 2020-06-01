from __future__ import print_function
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eListbox, gFont

from Plugins.Plugin import PluginDescriptor
from os import path as os_path, listdir as os_listdir
from StreamPlayer import StreamPlayer
from Tools.Import import my_import

###############################################################################
myname = "NETcaster"
myversion = "0.2"
streamingtargetfile = "/tmp/streaming.mpg"
valid_types = ("MP3")
#
streamplayer = None
plugin_path = ""

###############################################################################
def main(session,**kwargs):
    session.open(NETcasterScreenBrowser)
    global streamplayer
    streamplayer = StreamPlayer(session)

def Plugins(path,**kwargs):
    global plugin_path
    plugin_path = path
    return PluginDescriptor(
        name=myname,
        description="play Network and Internet Streams",
        where = PluginDescriptor.WHERE_EXTENSIONSMENU,
        icon = "NETcaster.png",
        fnc = main
        )

###############################################################################
class NETcasterScreenBrowser(Screen):
    skin = """
        <screen position="80,73" size="560,440" title="SHOUTcaster" >
        <widget name="streamlist" position="0,0" size="560,360" scrollbarMode="showOnDemand" />
        <widget name="metadata"     position="0,360" size="560,40" transparent="1" valign="left" halign="center" zPosition="5"  foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" font="Regular;21" />
        <ePixmap name="red"    position="0,400"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
        <ePixmap name="green"  position="140,400" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
        <ePixmap name="yellow" position="280,400" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
        <ePixmap name="blue"   position="420,400" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
        <widget name="pixred"     position="0,400" size="140,40" transparent="1" valign="center" halign="center" zPosition="5"  foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" font="Regular;21" />
        <widget name="pixgreen"     position="140,400" size="140,40" transparent="1" valign="center" halign="center" zPosition="5"  foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" font="Regular;21"/>
        <widget name="pixyellow" position="280,400" size="140,40" transparent="1" valign="center" halign="center" zPosition="5"  foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" font="Regular;21" />
        <widget name="pixblue"     position="420,400" size="140,40" transparent="1" valign="center" halign="center" zPosition="5"  foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" font="Regular;21" />
        </screen>"""

    streamlist = []
    currentPlugin = None
    def __init__(self, session, args = 0):
        self.skin = NETcasterScreenBrowser.skin
        self.session = session
        Screen.__init__(self, session)
        self["streamlist"] = StreamMenu([])
        self["metadata"] = Label("")
        self["pixred"] = Label("")
        self["pixgreen"] = Label(_("Play"))
        self["pixyellow"] = Label("")
        self["pixblue"] = Label(_("Select"))
        self["actions"] = ActionMap(["WizardActions", "DirectionActions", "MenuActions", "ShortcutActions", "GlobalActions", "HelpActions"],
            {
             "ok": self.ok,
             "back": self.exit,
             "red": self.stream_stop,
             "green": self.stream_start,
             "yellow": self.yellow,
             "blue": self.selectPlugin,
             "menu": self.showMainMenu,
             "info": self.showAbout,
             "displayHelp": self.showHelp,
             }, -1)

        self.onClose.append(self.exit)
        self.getInterfaceList()
        for plugin in self.pluginlist:
            if plugin.nameshort == "Favorites":
                self.setCurrentPlugin(plugin)
        self.onShown.append(self.updateTitle)

        self.onClose.append(self.disconnectFromMetadataUpdates)

    def connectToMetadataUpdates(self):
        global streamplayer
        if streamplayer is not None:
             streamplayer.metadatachangelisteners.append(self.onMetadataChanged)
             streamplayer.onStop.append(self._onStop)

    def disconnectFromMetadataUpdates(self):
        global streamplayer
        try:
             streamplayer.metadatachangelisteners.remove(self.onMetadataChanged)
        except Exception as e:
            pass
        try:
             streamplayer.onStop.remove(self._onStop)
        except Exception as e:
            pass

    def onMetadataChanged(self, title):
        try:
             self["metadata"].setText(title)
        except Exception as e:
            self.disconnectFromMetadataUpdates()

    def getInterfaceList(self):
        self.pluginlist = []
        global plugin_path, myname
        interfacepath = plugin_path+"/interface"
        for iface in os_listdir(interfacepath):
            if iface.endswith(".py") and not iface.startswith("_"):
                pluginp = '.'.join(["Plugins", "Extensions", myname, "interface", iface.replace(".py", "")])
                plugin = my_import(pluginp)
                self.pluginlist.append(plugin.Interface(self.session, cbListLoaded=self.onStreamlistLoaded))

    def updateTitle(self):
		try:
			self.setTitle("%s (%s)"%(myname, self.currentPlugin.nameshort))
		except:	
			pass

    def selectPlugin(self):
        glist=[]
        for i in self.pluginlist:
            glist.append((i.name, i))
        self.session.openWithCallback(self.selectedPlugin, ChoiceBox, _("select Plugin"), glist)

    def selectedPlugin(self, splugin):
        if splugin is not None:
            self.setCurrentPlugin(splugin[1])
            self.updateTitle()

    def setCurrentPlugin(self, plugin):
        self.currentPlugin = plugin
        plugin.getList()

    def ok(self):
        if self.shown is False:
            self.show()

    def exit(self):
        global streamplayer
        streamplayer.exit()
        self.close()

    def yellow(self):
        pass

    def _onStop(self):
        self["pixred"].setText("")
        self.setTitle("%s (%s)"%(myname, self.currentPlugin.nameshort))

    def stream_stop(self):
        global streamplayer
        if streamplayer.is_playing:
            print("[", myname, "] stream_startstop -> stop")
            streamplayer.stop()
            self.disconnectFromMetadataUpdates()
            self._onStop()

    def stream_start(self):
        global streamplayer
        if self["streamlist"].l.getCurrentSelection() is not None:
            stream = self["streamlist"].l.getCurrentSelection()[0]
            self.connectToMetadataUpdates()
            streamplayer.play(stream)
            self["pixred"].setText(_("Stop"))
            self.setTitle("%s"%(stream.getName()))

    def onStreamlistLoaded(self, list):
       self["streamlist"].buildList(list)

    def showMainMenu(self):
        menu = []
        if self["streamlist"].l.getCurrentSelection() is not None:
             selectedStream = self["streamlist"].l.getCurrentSelection()[0]
        else:
             selectedStream = None
        # generic menuitems
        for p in self.pluginlist:
            for i in p.getMenuItems(selectedStream, generic=True):
                menu.append((i[0], i[1]))

        # non generic menuitems
        if self.currentPlugin is not None:
            for i in self.currentPlugin.getMenuItems(selectedStream):
                menu.append((i[0], i[1]))

        # std menuitems
        menu.append((_("hide"), self.hide))
        menu.append((_("info"), self.showAbout));
        menu.append((_("help"), self.showHelp));
        self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Menu"), list=menu)

    def menuCallback(self, choice):
        if choice is not None:
            choice[1]()

    def showAbout(self):
        self.session.open(MessageBox, _("%s Enigma2 Plugin V%s (Patched)" % (myname, myversion)), MessageBox.TYPE_INFO)

    def showHelp(self):
        self.session.open(NETcasterScreenHelp)



###############################################################################
class NETcasterScreenHelp(Screen):
    skin = """
        <screen position="103,73" size="500,400" title="NETcaster Help" >
            <widget name="help" position="0,0" size="500,400" font="Regular;18"/>
        </screen>"""

    def __init__(self, session, args = 0):
        self.skin = NETcasterScreenHelp.skin
        Screen.__init__(self, session)
        global plugin_path
        readme = plugin_path+"/readme.txt"
        if os_path.exists(readme):
            fp = open(readme)
            text = fp.read()
            fp.close()
        else:
            text = "sorry, cant load helptext from file "+readme
        self["help"] = ScrollLabel(text)
        self["actions"] = ActionMap(["WizardActions", "DirectionActions", "MenuActions"],
            {
             "ok": self.close,
             "back": self.close,
             "up": self["help"].pageUp,
             "down": self["help"].pageDown
             }, -1)

###############################################################################
class StreamMenu(MenuList):
    def __init__(self, list, enableWrapAround = False):
        MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
        self.l.setFont(0, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 18))

    def postWidgetCreate(self, instance):
        MenuList.postWidgetCreate(self, instance)
        instance.setItemHeight(50)

    def buildList(self, listnew):
        list=[]
        for stream in listnew:
            res = [ stream ]
            res.append(MultiContentEntryText(pos=(5, 5), size=(500, 25), font=0, text=stream.getName()))
            res.append(MultiContentEntryText(pos=(5, 26), size=(500, 24), font=1, text=stream.getDescription()))
            list.append(res)
        self.l.setList(list)
        self.moveToIndex(0)

###############################################################################
class NETcasterScreenStreamDelete(Screen):
    def __init__(self, session):
        self.session = session
        self.config = NETcasterConfig()
        streams = self.config.getStreams()
        streamlist = []
        for stream in streams:
            streamlist.append((_(stream.getName()), stream.getName()))
        self.session.openWithCallback(self.stream2deleteSelected, ChoiceBox, _("select stream to delete"), streamlist)

    def stream2deleteSelected(self, selectedstreamname):
        if selectedstreamname is not None:
            self.stream2delete = selectedstreamname[1]
            self.session.openWithCallback(self.userIsSure, MessageBox, _("are you shure to delete the stream?\n\n%s" % self.stream2delete), MessageBox.TYPE_YESNO)

    def userIsSure(self, answer):
        if answer is None:
            self.cancelWizzard()
        if answer is False:
            self.cancelWizzard()
        else:
            self.config.deleteStreamWithName(self.stream2delete)

###############################################################################
