###############################################################################
# Copyright (c) 2008 Rico Schulte, 3c5x9. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

from enigma import getDesktop,eSize
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.config import config, ConfigSubList, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, getConfigListEntry
from Components.ConfigList import ConfigListScreen

from Plugins.Extensions.GoogleMaps.KMLlib import RootFolder,KmlFolder,KmlPlace
from Plugins.Extensions.GoogleMaps.WebPixmap import WebPixmap

config.plugins.GoogleMaps = ConfigSubsection()
config.plugins.GoogleMaps.add_mainmenu_entry = ConfigYesNo(default = True)
config.plugins.GoogleMaps.save_last_position = ConfigYesNo(default = True)
config.plugins.GoogleMaps.load_map_overlay = ConfigYesNo(default = True)
config.plugins.GoogleMaps.cache_enabled = ConfigYesNo(default = False)
config.plugins.GoogleMaps.position = ConfigSubsection()
config.plugins.GoogleMaps.position.x = ConfigInteger(33)
config.plugins.GoogleMaps.position.y = ConfigInteger(21)
config.plugins.GoogleMaps.position.z = ConfigInteger(6)


def applySkinVars(skin,dict):
    for key in dict.keys():
        try:
            skin = skin.replace('{'+key+'}',dict[key])
        except Exception,e:
            print e,"@key=",key
    return skin

class GoogleMapsConfigScreen(ConfigListScreen,Screen):
    skin = """
        <screen position="100,100" size="550,400" title="Google Maps Setup" >
        <widget name="config" position="0,0" size="550,360" scrollbarMode="showOnDemand" />
        <widget name="buttonred" position="10,360" size="100,40" backgroundColor="red" valign="center" halign="center" zPosition="1"  foregroundColor="white" font="Regular;18"/> 
        <widget name="buttongreen" position="120,360" size="100,40" backgroundColor="green" valign="center" halign="center" zPosition="1"  foregroundColor="white" font="Regular;18"/> 
        <widget name="label" position="240,360" size="200,40"  valign="center" halign="center" zPosition="1"  foregroundColor="white" font="Regular;18"/> 
        </screen>"""
    def __init__(self, session, args = 0):
        self.session = session
        Screen.__init__(self, session)
        self.list = []
        self.list.append(getConfigListEntry(_("add Entry to Main Menu"), config.plugins.GoogleMaps.add_mainmenu_entry))
        self.list.append(getConfigListEntry(_("save last Map Position"), config.plugins.GoogleMaps.save_last_position))
        self.list.append(getConfigListEntry(_("load Map Overlay"), config.plugins.GoogleMaps.load_map_overlay))
        self.list.append(getConfigListEntry(_("enable caching of Images in /tmp/"), config.plugins.GoogleMaps.cache_enabled))
        
        ConfigListScreen.__init__(self, self.list)
        self["buttonred"] = Label(_("cancel"))
        self["buttongreen"] = Label(_("ok"))
        self["label"] = Label("Author: 3c5x9")
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

class GoogleMapsMainScreen(Screen,HelpableScreen):
    raw_skin =  """
            <screen position="{screen.position}" size="{screen.size}" title="GoogleMaps" flags="wfNoBorder">
    <widget  name="pic1b" position="{pixmap1.pos}" size="{pixmap.size}" zPosition="0" alphatest="blend"/>
    <widget  name="pic1" position="{pixmap1.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic1o" position="{pixmap1.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic2" position="{pixmap2.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic2o" position="{pixmap2.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic3" position="{pixmap3.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic3o" position="{pixmap3.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic4" position="{pixmap4.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic4o" position="{pixmap4.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic5" position="{pixmap5.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic5o" position="{pixmap5.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic6" position="{pixmap6.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic6o" position="{pixmap6.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic7" position="{pixmap7.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic7o" position="{pixmap7.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic8" position="{pixmap8.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic8o" position="{pixmap8.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    <widget name="pic9" position="{pixmap9.pos}" size="{pixmap.size}" zPosition="1" alphatest="blend"/>
    <widget name="pic9o" position="{pixmap9.pos}" size="{pixmap.size}" zPosition="2" alphatest="blend"/>
    
    <widget name="infopanel" position="{infopanel.pos}" size="{infopanel.size}" zPosition="0"  backgroundColor="blue"/>
    <widget name="posx" position="{posx.pos}" size="{posx.size}" font="{font}" zPosition="1" />
    <widget name="posy" position="{posy.pos}" size="{posy.size}" font="{font}" zPosition="1" />
    <widget name="posz" position="{posz.pos}" size="{posz.size}" font="{font}" zPosition="1" />
    <widget name="placeslist" position="{placeslist.pos}" size="{placeslist.size}" zPosition="1"/>
    <widget name="buttonmenu" position="{buttonmenu.pos}" size="{buttonmenu.size}" font="{font}" halign="center" valign="center"  zPosition="1"/>        
    <widget name="buttonhelp" position="{buttonhelp.pos}" size="{buttonhelp.size}" font="{font}" halign="center" valign="center"  zPosition="1"/>

            </screen>
            """
    def __init__(self, session):
        self.session = session
        size_w = getDesktop(0).size().width()*0.9    
        size_h = getDesktop(0).size().height()*0.9
        pos_w = (getDesktop(0).size().width()-size_w)/2
        pos_h = (getDesktop(0).size().height()-size_h)/2        
        p_h = size_h/3
                
        infopanel_width = size_w - (p_h*3)
        infopanel_height = size_h
        label_height = 30
        font = "Regular;21"
        self.dict = {
                
                'font': font,
                
                'screen.size': "%i,%i"%(size_w,size_h),
                'screen.position': "%i,%i"%(pos_w,pos_h),
                'pixmap.size': '%i,%i'%(p_h,p_h),
                
                'pixmap1.pos': '0,0',
                'pixmap2.pos': '%i,0'%(p_h),
                'pixmap3.pos': '%i,0'%(p_h*2),
                
                'pixmap4.pos': '0,%i'%(p_h),
                'pixmap5.pos': '%i,%i'%(p_h,p_h),
                'pixmap6.pos': '%i,%i'%(p_h*2,p_h),
                
                'pixmap7.pos': '0,%i'%(p_h*2),
                'pixmap8.pos': '%i,%i'%(p_h,p_h*2),
                'pixmap9.pos': '%i,%i'%(p_h*2,p_h*2),
                
                'infopanel.pos': '%i,0'%(p_h*3),
                'infopanel.size': '%i,%i'%(infopanel_width,infopanel_height),
                
                'posx.pos': '%i,0'%(p_h*3),
                'posx.size': '%i,%i'%(infopanel_width,label_height),
                
                'posy.pos': '%i,%i'%(p_h*3,label_height),
                'posy.size': '%i,%i'%(infopanel_width,label_height),
                
                'posz.pos': '%i,%i'%(p_h*3,label_height*2),
                'posz.size': '%i,%i'%(infopanel_width,label_height),
                
                'placeslist.pos': '%i,%i'%(p_h*3,label_height*3),
                'placeslist.size': '%i,%i'%(infopanel_width,infopanel_height-(label_height*4)),

                'buttonmenu.pos': '%i,%i'%(p_h*3,infopanel_height-(label_height*4)+(label_height*3)),
                'buttonmenu.size': '%i,%i'%(infopanel_width/2,label_height),
                
                'buttonhelp.pos': '%i,%i'%(p_h*3+(infopanel_width/2),infopanel_height-(label_height*4)+(label_height*3)),
                'buttonhelp.size': '%i,%i'%(infopanel_width/2,label_height),
                
                }
        
        self.skin = applySkinVars(GoogleMapsMainScreen.raw_skin,self.dict)
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
    
        self["infopanel"] = Label()
        self["posx"] = Label("")
        self["posy"] = Label("")
        self["posz"] = Label("")
        self["placeslist"] = MenuList([])
        self["buttonmenu"] = Label(_("Menu"))
        self["buttonhelp"] = Label(_("Help"))
        
        self["pic1b"] = WebPixmap()
        self["pic1"] = WebPixmap()
        self["pic2"] = WebPixmap()
        self["pic3"] = WebPixmap()
        self["pic4"] = WebPixmap()
        self["pic5"] = WebPixmap()
        self["pic6"] = WebPixmap()
        self["pic7"] = WebPixmap()
        self["pic8"] = WebPixmap()
        self["pic9"] = WebPixmap()
        
        self["pic1o"] = WebPixmap()
        self["pic2o"] = WebPixmap()
        self["pic3o"] = WebPixmap()
        self["pic4o"] = WebPixmap()
        self["pic5o"] = WebPixmap()
        self["pic6o"] = WebPixmap()
        self["pic7o"] = WebPixmap()
        self["pic8o"] = WebPixmap()
        self["pic9o"] = WebPixmap()
        
        self["actionmap"] = ActionMap(["OkCancelActions", "NumberActions","DirectionActions","MenuActions","InfobarChannelSelection"],
            {
             "cancel": self.close,
             "ok": self.keyOk,
             "1": self.key1,
             "2": self.key2,
             "3": self.key3,
             "4": self.key4,
             "5": self.key5,
             "6": self.key6,
             "7": self.key7,
             "8": self.key8,
             "9": self.key9,
             "0": self.key0,
             "menu": self.keymenu,
             "historyNext": self.toggleMapOverlay,
             
             }, -1)
        
        self.helpList.append((self["actionmap"], "OkCancelActions", [("cancel", _("quit Google Maps"))]))
        self.helpList.append((self["actionmap"], "DirectionActions", [("up", _("navigate thru Placemarks"))]))
        self.helpList.append((self["actionmap"], "DirectionActions", [("down", _("navigate thru Placemarks"))]))
        self.helpList.append((self["actionmap"], "DirectionActions", [("left", _("navigate thru Placemarks"))]))
        self.helpList.append((self["actionmap"], "DirectionActions", [("right", _("navigate thru Placemarks"))]))
        self.helpList.append((self["actionmap"], "OkCancelActions", [("ok", _("show selected Placemark"))]))
        self.helpList.append((self["actionmap"], "NumberActions", [("1",'move north-west')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("2",'move north')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("3",'move north-east')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("4",'move west')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("6",'move east')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("7",'move south-west')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("8",'move south')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("9",'move south-east')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("5",'zoom in')]))
        self.helpList.append((self["actionmap"], "NumberActions", [("0",'zoom out')]))
        self.helpList.append((self["actionmap"], "InfobarChannelSelection", [("historyNext",'show/unshow Map Overlay')]))
        
        self.onLayoutFinish.append(self.onLayoutFinished)

    def getRandomNumber(self):
        """ returning a real random number """
        return 4 # fairly choosen by using a dice
    
    def buildMenuRoot(self):
        list = []
        root = RootFolder()
        for i in root.getFiles("/usr/lib/enigma2/python/Plugins/Extensions/GoogleMaps/"):
            l = lambda name,filepath: self.openFolderRoot(name,filepath)
            list.append((i[0],i[1],l))
        self["placeslist"].setList(list)

    def openFolderRoot(self,name,filepath):
        print "openFolderRoot",name,filepath
        root = RootFolder()
        folderx = root.getFolderFromFile(filepath)
        list = []
        l = lambda name,filepath: self.buildMenuRoot()
        list.append(("..",filepath,l))
        for folderx in folderx.getFolders():
            l = lambda name,folder: self.openFolder(name,folder)
            list.append(("+ "+folderx.name,folderx,l))
        
        for placex in folderx.getPlacemarks():
            l = lambda name,place: self.showPlace(name,place)
            list.append((""+placex.name,placex,l))
        
        self["placeslist"].setList(list)
    
    def openFolder(self,name,foldery):
        print  "open Folder",name,foldery
        list = []
        if foldery.parent is None:
            l = lambda name,folder: self.buildMenuRoot()
            list.append(("..",None,l))
        else:
            l = lambda name,folder: self.openFolder(name,folder)
            list.append(("..",foldery.parent,l))
            
        for folderx in foldery.getFolders():
            l = lambda name,folder: self.openFolder(name,folder)
            list.append(("+ "+folderx.name,folderx,l))
        
        for placex in foldery.getPlacemarks():
            l = lambda name,place: self.showPlace(name,place)
            list.append((""+placex.name,placex,l))
        
        self["placeslist"].setList(list)
       
    def showPlace(self,name,place):
        #print "show Place",name,place 
        x,y,z = place.getTile(self.z)
        self.setNewXYZ(x,y,z)  
    
    def onLayoutFinished(self):  
        self.buildMenuRoot()
        self.setNewXYZ(config.plugins.GoogleMaps.position.x.value,
                       config.plugins.GoogleMaps.position.y.value,
                       config.plugins.GoogleMaps.position.z.value)
        
    #################
    def toggleMapOverlay(self):
        if config.plugins.GoogleMaps.load_map_overlay.value is True:
            config.plugins.GoogleMaps.load_map_overlay.value = False
        else:
            config.plugins.GoogleMaps.load_map_overlay.value = True
        self.setNewXYZ(config.plugins.GoogleMaps.position.x.value,
                       config.plugins.GoogleMaps.position.y.value,
                       config.plugins.GoogleMaps.position.z.value)
        
    def keymenu(self):
        self.session.openWithCallback(self.menuCB,GoogleMapsConfigScreen)
    
    def menuCB(self,dummy):
        self.setNewXYZ(config.plugins.GoogleMaps.position.x.value,
                       config.plugins.GoogleMaps.position.y.value,
                       config.plugins.GoogleMaps.position.z.value)
        
    def keyOk(self):
        listentry = self["placeslist"].getCurrent()
        if listentry is not None:
            if listentry[1] is not None:
                listentry[2](listentry[0],listentry[1])

    def key1(self):  
        # northwest
        self.setNewXYZ(self.x-1,self.y-1,self.z)
    
    def key3(self):  
        # northeast
        self.setNewXYZ(self.x+1,self.y-1,self.z)
    
    def key7(self):  
        # southwest
        self.setNewXYZ(self.x-1,self.y+1,self.z)
    
    def key9(self):  
        # southeast
        self.setNewXYZ(self.x+1,self.y+1,self.z)
    
    #################
    def key2(self):
        # north
        self.setNewXYZ(self.x,self.y-1,self.z)
        
    def key8(self):
        # south
        self.setNewXYZ(self.x,self.y+1,self.z)
        
    def key4(self):
        # west
        self.setNewXYZ(self.x-1,self.y,self.z)
        
    def key6(self):
        # east
        self.setNewXYZ(self.x+1,self.y,self.z)
        
    #################
    def key5(self):
        #zoom in
        self.setNewXYZ(self.x*2,self.y*2+1,self.z+1)        
    
    def key0(self):
        #zoom out
        self.setNewXYZ(self.x/2,self.y/2,self.z-1)        
       
    #################
    def setNewXYZ(self,x,y,z):
        print x,y,z
        if z<0 or z>=30:
            return
        self.x = x
        self.y = y
        self.z = z
        if config.plugins.GoogleMaps.save_last_position.value:
            config.plugins.GoogleMaps.position.x.value = x    
            config.plugins.GoogleMaps.position.y.value = y 
            config.plugins.GoogleMaps.position.z.value = z 
        
        self["posx"].setText(_('Pos.')+" X: "+str(x))
        self["posy"].setText(_('Pos.')+" Y: "+str(y))
        self["posz"].setText(_('Zoom')+" : "+str(z))
        
        self["pic1"].load(self.getURL(x-1,y-1,z))
        self["pic2"].load(self.getURL(x,y-1,z))
        self["pic3"].load(self.getURL(x+1,y-1,z))
        self["pic4"].load(self.getURL(x-1,y,z))
        self["pic5"].load(self.getURL(x,y,z))
        self["pic6"].load(self.getURL(x+1,y,z))
        self["pic7"].load(self.getURL(x-1,y+1,z))
        self["pic8"].load(self.getURL(x,y+1,z))
        self["pic9"].load(self.getURL(x+1,y+1,z))

        if config.plugins.GoogleMaps.load_map_overlay.value:
            self["pic1o"].show()
            self["pic2o"].show()
            self["pic3o"].show()
            self["pic4o"].show()
            self["pic5o"].show()
            self["pic6o"].show()
            self["pic7o"].show()
            self["pic8o"].show()
            self["pic9o"].show()
            self["pic1o"].load(self.getMapURL(x-1,y-1,z))
            self["pic2o"].load(self.getMapURL(x,y-1,z))
            self["pic3o"].load(self.getMapURL(x+1,y-1,z))
            self["pic4o"].load(self.getMapURL(x-1,y,z))
            self["pic5o"].load(self.getMapURL(x,y,z))
            self["pic6o"].load(self.getMapURL(x+1,y,z))
            self["pic7o"].load(self.getMapURL(x-1,y+1,z))
            self["pic8o"].load(self.getMapURL(x,y+1,z))
            self["pic9o"].load(self.getMapURL(x+1,y+1,z))
        else:
            self["pic1o"].hide()
            self["pic2o"].hide()
            self["pic3o"].hide()
            self["pic4o"].hide()
            self["pic5o"].hide()
            self["pic6o"].hide()
            self["pic7o"].hide()
            self["pic8o"].hide()
            self["pic9o"].hide()

    def getURL(self,x,y,z):
        url = "http://khm1.google.com/kh?v=32&hl=de&x=%i&y=%i&z=%i"%(x,y,z)
        return url
   
    def getMapURL(self,x,y,z):
        url = "http://mt1.google.com/mt?v=w2t.99&hl=de&x=%i&y=%i&z=%i&s=G"%(x,y,z)
        return url   
        
##################################

def start_from_mainmenu(menuid, **kwargs):
    #starting from main menu
    if menuid == "mainmenu":
        return [(_("Google Maps"), start_from_pluginmenu, "googlemaps", 46)]
    return []

originalservice = None
mysession = None

def start_from_pluginmenu(session,**kwargs):
    global originalservice,mysession
    mysession = session
    originalservice = session.nav.getCurrentlyPlayingServiceReference()
    #session.nav.stopService()
    session.openWithCallback(mainCB,GoogleMapsMainScreen)    

def mainCB():
    global originalservice,mysession
    #mysession.nav.playService(originalservice)
    config.plugins.GoogleMaps.position.x.save()    
    config.plugins.GoogleMaps.position.y.save()    
    config.plugins.GoogleMaps.position.z.save()    
    
def Plugins(path,**kwargs):
    pname = "Google Maps"
    pdesc = "browse google maps"
    desc_mainmenu  = PluginDescriptor(name=pname, description=pdesc,  where = PluginDescriptor.WHERE_MENU, fnc = start_from_mainmenu)
    desc_pluginmenu = PluginDescriptor(name=pname, description=pdesc,  where = PluginDescriptor.WHERE_PLUGINMENU, fnc = start_from_pluginmenu, icon="plugin.png")
    list = []
    list.append(desc_pluginmenu)
    if config.plugins.GoogleMaps.add_mainmenu_entry.value:
        list.append(desc_mainmenu)
    return list



