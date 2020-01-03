# -*- coding: utf-8 -*-
# by 3c5x9@2007
from enigma import eTimer, getDesktop
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList

from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_WRAP

from Plugins.Plugin import PluginDescriptor
import xml.dom.minidom

from twisted.web.client import getPage
from twisted.internet import reactor

###############################################################################        
class TrafficInfoMain(Screen):
    skin_SD = """
        <screen position="110,83" size="530,430" title="Verkehrsinfo" >                        
            <widget name="sectionlist" position="0,0" size="530,125" scrollbarMode="showOnDemand" />            
            <widget name="itemlist" position="0,130" size="530,125" scrollbarMode="showOnDemand" />            
            <widget name="itemdetails" position="0,260" size="530,140" font="Regular;20" halign=\"center\" valign=\"center\"/>            
            <widget name="statuslabel" position="0,400" size="530,30" halign=\"left\"/>           
        </screen>
        """
    skin_HD = """
        <screen name="TrafficInfo" position="center,60" size="1030,600" title="Verkehrsinformation">
            <widget name="sectionlist" position="100,0" size="830,205" scrollbarMode="showOnDemand" />
            <widget name="itemlist" position="100,215" size="830,275" scrollbarMode="showOnDemand" />
            <widget name="itemdetails" position="10,495" size="1010,90" font="Regular;20" halign="left" valign="center" />
            <widget name="statuslabel" position="0,587" size="730,13" halign="left" />
        </screen>
        """
    def __init__(self, session,args = 0):
        self.loadinginprogress = False
        self.session = session
        desktop = getDesktop(0)
        size = desktop.size()
        width = size.width()
        if width < 1280:
            self.skin = TrafficInfoMain.skin_SD
        else:
            self.skin = TrafficInfoMain.skin_HD
        Screen.__init__(self, session)
        self.menu = args
        self["sectionlist"] = MenuList([])
        self["itemlist"] = ItemList([])
        self["statuslabel"] = Label("")
        self["itemdetails"] = Label("")
        self["actions"] = ActionMap(["ChannelSelectBaseActions","WizardActions", "DirectionActions","MenuActions","NumberActions"], 
            {
             "ok": 	            self.go,
             "back":            self.exit,
             "nextBouquet":     self.selectSectionlist,
             "prevBouquet":     self.selectItemlist,
             "down": 	        self.down,
             "up": 	            self.up,
             "left":	        self.left,
             "right":	        self.right,
             }, -1)
        self.statuslabelcleartimer = eTimer()
        self.statuslabelcleartimer.timeout.get().append(self.clearStatusLabel)
        
        self["itemlist"].onSelectionChanged.append(self.onItemSelected)
        self.selectSectionlist()
        
        self.onShown.append(self.getSections)
        
    def exit(self):
        if self.loadinginprogress:
            reactor.callLater(1,self.exit)
        else:
            self.close()

    def selectSectionlist(self):
        self.currList = "sectionlist"
        self["sectionlist"].selectionEnabled(1)
        self["itemlist"].selectionEnabled(0)
        
    def selectItemlist(self):
        self.currList = "itemlist"
        self["sectionlist"].selectionEnabled(0)
        self["itemlist"].selectionEnabled(1)
        self["itemlist"].selectionChanged()
        
    def go(self):
        if self.currList == "sectionlist":
            self.onSectionSelected()

    def up(self):
        self[self.currList].up()
    
    def down(self):
        self[self.currList].down()
        
    def left(self):
        self[self.currList].pageUp()
    
    def right(self):
        self[self.currList].pageDown()
        
    def onSectionSelected(self):
        c = self["sectionlist"].getCurrent()
        if c is not None:
            self.setTitle("Verkehrsinfo: "+c[1].name)
            self.getItemsOfSection(c[1])
        
    def onItemSelected(self):
        if self["itemlist"].getCurrent() is not None:
            c = self["itemlist"].getCurrent()[0]
            if c is not None:
                self["itemdetails"].setText(c.text)
            
    ###########
    def clearStatusLabel(self):
        self["statuslabel"].setText("")
        
    def setStatusLabel(self,text):
        self.statuslabelcleartimer.stop()         
        self["statuslabel"].setText(text)
        self.statuslabelcleartimer.start(3000)
        
    def getSections(self):
        self.setStatusLabel("loading sections")
        self.loadinginprogress = True    
        getPage("http://wap.verkehrsinfo.de/wvindex.php3").addCallback(self.sectionsLoaded).addErrback(self.sectionsLoadingFaild)
    
    def sectionsLoadingFaild(self,raw):
        self.loadinginprogress = False
        self.setStatusLabel("loading sections failed"+raw)
        
    def sectionsLoaded(self,raw):
        self.loadinginprogress = False
        try:
            xmldoc = xml.dom.minidom.parseString( raw)
            self.sections = []
            for i in xmldoc.getElementsByTagName("a"):
                link = "/"+i.getAttribute("href")
                name = i.toxml().split(">")[1].split("<")[0]
                self.sections.append(TrafficInfoSection(name,link))
            self.onSectionsLoaded()
        except xml.parsers.expat.ExpatError,e:
            print e
            print raw
            self.setStatusLabel("loading sections failed")

    def onSectionsLoaded(self):
        self.setStatusLabel("sections loaded")
        list = []
        for i in self.sections:
            if i.name.startswith("BRD") is not True:
                list.append((i.name,i))
        list.sort()
        self["sectionlist"].l.setList(list)
        self["sectionlist"].instance.moveSelectionTo(0)

    def onItemsLoaded(self):
        list=[]
        for item in self.trafficitems:
            res = [ item ]
            res.append(MultiContentEntryText(pos=(0, 0), size=(75, 20), font=0, flags = RT_HALIGN_LEFT|RT_WRAP, text = item.street))
            res.append(MultiContentEntryText(pos=(75,0), size=(455, 20), font=1, flags = RT_HALIGN_LEFT, text = item.direction))
            list.append(res)
        self["itemlist"].l.setList(list)
        self["itemlist"].instance.moveSelectionTo(0)
        self.setStatusLabel("messages loaded")

    ##########
    def getItemsOfSection(self,section):
        print "loading section",section.name  ,section.link
        self.setStatusLabel("loading messages "+section.name)
        self.loadinginprogress = True    
        getPage("http://wap.verkehrsinfo.de"+section.link).addCallback(self.trafficitemsLoaded).addErrback(self.trafficitemsLoadingFaild)

    def trafficitemsLoadingFaild(self,raw):
        self.loadinginprogress = False
        print "loading items faild",raw
        self.setStatusLabel("loading messages faild"+raw)
        
    def trafficitemsLoaded(self,raw):
        self.loadinginprogress = False
        try:
            raw = raw.replace("&amp","")
            xmldoc = xml.dom.minidom.parseString( raw)
            self.trafficitems = []
            for item in  xmldoc.getElementsByTagName("p"):
                self.trafficitems.append(self.parseItem(item))
            self.onItemsLoaded()
        except xml.parsers.expat.ExpatError,e:
            print e
            print raw
            self.setStatusLabel("loading messages faild! Parsing Error")
        
    def parseItem(self,item):
        source=item.toxml()
        i= item.getElementsByTagName("b")
        source=source.replace(i[0].toxml(),"")
        street = i[0].toxml().replace("<b>","").replace("</b>","").replace("\n","")
        
        source=source.replace(i[1].toxml(),"")
        direction = i[1].toxml().replace("<b>","").replace("</b>","").replace("\n","")
        details = source.replace("<p>","").replace("</p>","").replace("<small>","").replace("</small>","").replace("<br/>","").replace("\n","")
        if street == "<b/>":
            street = "Info"
        return TrafficInfoItem(street,direction,details)

class ItemList(MenuList):
    def __init__(self, items, enableWrapAround = False):
        MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
        self.l.setFont(0, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 18))

    def getCurrentEntry(self):
        return self.l.getCurrentSelection()

####################
class TrafficInfoSection:
    def __init__(self, name,link):
        self.name = name.encode("utf-8")
        self.link = link.encode("utf-8")

    def __str__(self):
        return "name="+self.name+", link="+self.link

####################
class TrafficInfoItem:
    def __init__(self, street,direction,text):
        self.street = street.encode("utf-8")
        self.direction = direction.encode("utf-8")
        self.text = text.encode("utf-8")

    def __str__(self):
        return "street="+self.street+", dir="+self.direction+", text="+self.text

#############################
def main(session, **kwargs):
    session.open(TrafficInfoMain)

def Plugins(**kwargs):
  return PluginDescriptor(name="Verkehrsinfo",description="Show German traffic jams",where = PluginDescriptor.WHERE_PLUGINMENU,fnc = main,icon="plugin.png")

