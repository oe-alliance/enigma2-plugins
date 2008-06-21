Version = '$Header$';

from enigma import  eListboxPythonMultiContent, gFont
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigInteger,ConfigYesNo,ConfigText
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Button import Button
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText

from Components.ActionMap import ActionMap
from Plugins.Extensions.WebInterface import addInterfaceConfig

class WebIfConfigScreen(ConfigListScreen,Screen):
    skin = """
        <screen position="100,100" size="550,400" title="Webinterface: Main Setup" >
            <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
            
            <widget name="key_red" position="0,360" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18"/> 
            <widget name="key_yellow" position="140,360" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18"/> 
            <widget name="key_green" position="280,360" size="140,40" valign="center" halign="center" zPosition="4"  foregroundColor="white" font="Regular;18"/>
            
            <ePixmap name="red"    position="0,360"   zPosition="2" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
            <ePixmap name="green"  position="140,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
            <ePixmap name="yellow" position="280,360" zPosition="2" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" /> 
        </screen>"""
    def __init__(self, session, args = 0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("start Webinterface"), config.plugins.Webinterface.enable))
        self.list.append(getConfigListEntry(_("enable /hdd"), config.plugins.Webinterface.includehdd))
        self.list.append(getConfigListEntry(_("autowrite timer"), config.plugins.Webinterface.autowritetimer))
        self.list.append(getConfigListEntry(_("load movie-length"), config.plugins.Webinterface.loadmovielength))
        
        for i in range(0, config.plugins.Webinterface.interfacecount.value):
            c = config.plugins.Webinterface.interfaces[i]
            
        ConfigListScreen.__init__(self, self.list)
        self["key_red"] = Button(_("Cancel"))
        self["key_yellow"] = Button(_("Interfaces"))
        self["key_green"] = Button(_("Ok"))
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "yellow": self.openIfacesConfig,
            "green": self.save,
            "red": self.cancel,
            "save": self.save,
            "cancel": self.cancel,
            "ok": self.save,
        }, -2)
        
    def openIfacesConfig(self):
        print "yellow"
        self.session.open(WebIfInterfaceListConfigScreen)
        
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

class WebIfInterfaceListConfigScreen(Screen):
    skin = """
        <screen position="100,100" size="550,400" title="Webinterface: list of configured Interfaces" >
            <widget name="adress" position="5,0" size="150,50"   font="Regular;20" halign="left"/>
            <widget name="port" position="160,0" size="50,50"   font="Regular;20" halign="left"/>
            <widget name="auth" position="215,0" size="200,50"   font="Regular;20" halign="left"/>
            <widget name="disabled" position="420,0" size="130,50"   font="Regular;20" halign="left"/>
            <widget name="ifacelist" position="0,50" size="550,300"  scrollbarMode="showOnDemand"/>
            
            <widget name="key_red" position="0,350" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	        <widget name="key_yellow" position="280,350" size="140,40"  zPosition="5" valign="center" halign="center" backgroundColor="yellow" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
    	    
            <ePixmap name="red"    position="0,350"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
    	    <ePixmap name="yellow" position="280,350" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />	
        </screen>"""
    def __init__(self, session):
        
        Screen.__init__(self, session)
        self["adress"] = Button(_("Adress"))
        self["port"] = Button(_("Port"))
        self["auth"] = Button(_("use Authorization"))
        self["disabled"] = Button(_("disabled"))
        self["key_red"] = Button(_("add"))
        self["key_yellow"] = Button(_("change"))
        self["ifacelist"] = WebIfInterfaceList([])
        self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"],
            {
             "ok"	:	self.keyGreen,
             "back"	:	self.close,
             "red"	:	self.keyRed,
             "green"	:	self.keyGreen,
             "yellow"	:	self.keyYellow,
             "up"	:	self.up,
             "down"	:	self.down,
             "left"	:	self.left,
             "right"	:	self.right,
             }, -1)
        self.updateList()
        
    def updateList(self):
        ifaceguilist = []
        for i in range(0, config.plugins.Webinterface.interfacecount.value):
            c= config.plugins.Webinterface.interfaces[i]
            res = [ i ] #550,400
            res.append(MultiContentEntryText(pos=(5, 0), size=(150, 25), font=0, text=c.adress.value))
            res.append(MultiContentEntryText(pos=(160, 0),size=(50, 25), font=0,text=str(c.port.value)))
            
            if c.useauth.value:
                res.append(MultiContentEntryText(pos=(215, 0),size=(200, 25), font=0,text=_("yes"),color=0x0000FF00))
            else:
                res.append(MultiContentEntryText(pos=(215, 0),size=(200, 25), font=0,text=_("no"),color=0x00FF0000))
                
            if c.disabled.value:
                res.append(MultiContentEntryText(pos=(420, 0),size=(130, 25), font=0,text=_("yes"),color=0x0000FF00))
            else:
                res.append(MultiContentEntryText(pos=(420, 0),size=(130, 25), font=0,text=_("no"),color=0x00FF0000))
            ifaceguilist.append(res)
        ifaceguilist.sort()
        self["ifacelist"].l.setList(ifaceguilist)

    
    def keyRed(self):
        print "KEYRED"
        self.session.openWithCallback(self.updateList,WebIfInterfaceConfigScreen,None)
        
    def keyGreen(self):
        print "KEYGREEN"
        
    def keyYellow(self):
        x = self["ifacelist"].getCurrent()[0]
        print "current list index",x
        self.session.openWithCallback(self.updateList,WebIfInterfaceConfigScreen,int(x))

    def up(self):
        self["ifacelist"].up()

    def down(self):
        self["ifacelist"].down()

    def left(self):
        self["ifacelist"].pageUp()

    def right(self):
        self["ifacelist"].pageDown()


class WebIfInterfaceList(MenuList):
    def __init__(self, list, enableWrapAround = False):
        MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
        self.l.setFont(0, gFont("Regular", 20))
        #self.l.setFont(1, gFont("Regular", 25))

    def postWidgetCreate(self, instance):
        MenuList.postWidgetCreate(self, instance)
        instance.setItemHeight(25)
    
        
class WebIfInterfaceConfigScreen(Screen, ConfigListScreen):
    skin = """
        <screen name="Interface Config" position="80,148" size="560,280" title="Webinterface: edit Interface">
            <widget name="config" position="10,10" size="520,210" scrollbarMode="showOnDemand" />
            <ePixmap name="red"    position="0,240"   zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
            <ePixmap name="green"  position="140,240" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />            
            <ePixmap name="blue"   position="420,240" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
            
            <widget name="key_red" position="0,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <widget name="key_green" position="140,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
            <widget name="key_blue" position="420,240" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
        </screen>"""
    
    def __init__(self, session, ifacenum):
        Screen.__init__(self, session)
        self["actions"] = ActionMap(["SetupActions", "ColorActions"],
        {
            "green": self.keySave,
            "red": self.keyCancel,
            "blue": self.keyDelete,
            "cancel": self.keyCancel
        }, -2)

        self["key_red"] = Button(_("Cancel"))
        self["key_green"] = Button(_("OK"))
        #self["key_yellow"] = Button("")
        self["key_blue"] = Button(_("Delete"))

        if ifacenum is None:
            i = addInterfaceConfig()
        else:
            i = ifacenum
        cfglist = []
        try:
            current = config.plugins.Webinterface.interfaces[i]
        except IndexError,e:
            print "[WebIf] iface config %i not found, adding it and setting default values"%i
            addInterfaceConfig()
            current = config.plugins.Webinterface.interfaces[ifacenum]
            
        cfglist.append(getConfigListEntry(_("disabled"), current.disabled))
        cfglist.append(getConfigListEntry(_("Adress"), current.adress))
        cfglist.append(getConfigListEntry(_("Port"), current.port))
        cfglist.append(getConfigListEntry(_("use Authorization"), current.useauth))
        ConfigListScreen.__init__(self, cfglist, session)
        self.ifacenum = i

    def keySave(self):
        config.plugins.Webinterface.interfacecount.save()
        for x in self["config"].list:
            if isinstance(x[1].value, str):
                x[1].value = x[1].value.strip()
            x[1].save()
        self.close()
        config.save()

    def cancelConfirm(self, result):
        if result:
            config.plugins.Webinterface.interfacecount.cancel()
        self.callback = None
        ConfigListScreen.cancelConfirm(self, result)

    def keyDelete(self):
        self.session.openWithCallback(self.deleteConfirm, MessageBox, _("Really delete this Interface?"))

    def deleteConfirm(self, result):
        if not result:
            return
        del(config.plugins.Webinterface.interfaces[self.ifacenum])
        config.plugins.Webinterface.interfaces.save()
        config.plugins.Webinterface.interfacecount.value = config.plugins.Webinterface.interfacecount.value - 1;
        config.plugins.Webinterface.interfacecount.save()
        config.save()
        self.close()
        
