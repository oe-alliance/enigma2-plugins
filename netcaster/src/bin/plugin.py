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
        where = PluginDescriptor.WHERE_PLUGINMENU,
        icon = "NETcaster.png",
        fnc = main
        )
               
############################################################################### 
class NETcasterScreenBrowser(Screen):
    skin = """
        <screen position="110,73" size="530,430" title="SHOUTcaster" >
            <widget name="streamlist" position="0,0" size="530,400" scrollbarMode="showOnDemand" />            
            <widget name="pixred" position="20,400" size="100,30" backgroundColor=\"red\" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="pixgreen" position="140,400" size="100,30" backgroundColor=\"green\" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\"/>            
            <widget name="pixyellow" position="260,400" size="100,30" backgroundColor=\"yellow\" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />            
            <widget name="pixblue" position="380,400" size="100,30" backgroundColor=\"blue\" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />            
        </screen>"""
         
    streamlist = []
    currentPlugin = None
    def __init__(self, session, args = 0):
        self.skin = NETcasterScreenBrowser.skin
        self.session = session
        Screen.__init__(self, session)
        self["streamlist"] = StreamMenu([])
        self["pixred"] = Label("play")
        self["pixgreen"] = Label("%")
        self["pixyellow"] = Label("%")
        self["pixblue"] = Label("select")
        self["actions"] = ActionMap(["WizardActions", "DirectionActions","MenuActions","ShortcutActions","GlobalActions","HelpActions"], 
            {
             "ok": self.ok,
             "back": self.exit,
             "red": self.stream_startstop,
             "blue": self.selectPlugin,
             "menu": self.showMainMenu,
             "displayHelp": self.showHelp,
             }, -1)
        
        self.onClose.append(self.exit)
        self.getInterfaceList()
        
    def getInterfaceList(self):
        self.pluginlist = []
        global plugin_path,myname
        interfacepath = plugin_path+"/interface"
        for iface in os_listdir(interfacepath):
            if iface.endswith(".py") and iface != "__init__.py":
                pluginp = '.'.join(["Plugins", "Extensions", myname, "interface",iface.replace(".py","")])
                plugin = my_import(pluginp)
                self.pluginlist.append(plugin.Interface(self.session,cbListLoaded=self.onStreamlistLoaded))
    
    def selectPlugin(self):
        glist=[]
        for i in self.pluginlist:
            glist.append((i.name,i))
        self.session.openWithCallback(self.selectedPlugin,ChoiceBox,_("select Plugin"),glist)
    
    def selectedPlugin(self,splugin):
        if splugin is not None:
            self.currentPlugin = splugin[1]
            self.currentPlugin.getList()
            self.setTitle("%s (%s)"%(myname,self.currentPlugin.nameshort))
        
    def ok(self):
        if self.shown is False:
            self.show()
            
    def exit(self):
        global streamplayer 
        streamplayer.exit()       
        self.close()
    
    def stream_startstop(self):
        global streamplayer
        if streamplayer.is_playing:
            print "[",myname,"] stream_startstop -> stop"
            streamplayer.stop()
            self["pixred"].setText("start")
        else:
            if self["streamlist"].l.getCurrentSelection() is not None:
                stream = self["streamlist"].l.getCurrentSelection()[0]
                print "[",myname,"] stream_startstop ->start",stream.getURL()
                streamplayer.play(stream)
                self["pixred"].setText("stop")

    def onStreamlistLoaded(self,list):
       self["streamlist"].buildList(list)
    
    def showMainMenu(self):
        menu = []
        if self["streamlist"].l.getCurrentSelection() is not None:
             selectedStream = self["streamlist"].l.getCurrentSelection()[0]
        else:
             selectedStream = None
        # generic menuitems
        for p in self.pluginlist:
            for i in p.getMenuItems(selectedStream,generic=True):
                menu.append((i[0],i[1]))
            
        # non generic menuitems
        if self.currentPlugin is not None:
            for i in self.currentPlugin.getMenuItems(selectedStream):
                menu.append((i[0],i[1]))
        
        # std menuitems    
        menu.append((_("hide"), self.hide))
        menu.append((_("info"), self.showAbout));
        menu.append((_("help"), self.showHelp));
        self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Menu"), list=menu)
        
    def menuCallback(self,choice):
        if choice is not None:
            choice[1]()

    def showAbout(self):
        self.session.open(MessageBox,_("%s Enigma2 Plugin V%s" % (myname,myversion)), MessageBox.TYPE_INFO)

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
        self["actions"] = ActionMap(["WizardActions", "DirectionActions","MenuActions"], 
            {
             "ok": self.close,
             "back": self.close,
             "up": self["help"].pageUp,
             "down": self["help"].pageDown
             }, -1)
        
############################################################################### 
class StreamMenu(MenuList):
    def __init__(self, list, enableWrapAround = False):
        MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent())
        self.l.setFont(0, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 18))

    def postWidgetCreate(self, instance):
        MenuList.postWidgetCreate(self, instance)
        instance.setItemHeight(50)
    
    def buildList(self,listnew):
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
            streamlist.append((_(stream.getName()),stream.getName()))
        self.session.openWithCallback(self.stream2deleteSelected,ChoiceBox,_("select stream to delete"),streamlist)
        
    def stream2deleteSelected(self,selectedstreamname):
        if selectedstreamname is not None:
            self.stream2delete = selectedstreamname[1]
            self.session.openWithCallback(self.userIsSure,MessageBox,_("are you shure to delete the stream?\n\n%s" % self.stream2delete), MessageBox.TYPE_YESNO)

    def userIsSure(self,answer):
        if answer is None:
            self.cancelWizzard()
        if answer is False:
            self.cancelWizzard()
        else:
            self.config.deleteStreamWithName(self.stream2delete)
            
###############################################################################
