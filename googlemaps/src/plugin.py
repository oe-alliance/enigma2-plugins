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
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.config import config, ConfigSubList, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText

from Plugins.Extensions.GoogleMaps.KMLlib import RootFolder,KmlFolder,KmlPlace
from Plugins.Extensions.GoogleMaps.WebPixmap import WebPixmap

config.plugins.GoogleMaps = ConfigSubsection()
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

class GoogleMapsMainScreen(Screen):
    raw_skin =  """
            <screen position="0,0" size="{screen.size}" title="GoogleMaps" flags="wfNoBorder">
    <widget name="bg" position="0,0" size="{screen.size}" backgroundColor="white" zPosition="0"/>
    <widget name="pic1" position="{pixmap1.pos}" size="{pixmap.size}" zPosition="1"  />
    <widget name="pic2" position="{pixmap2.pos}" size="{pixmap.size}" zPosition="1"/>
    <widget name="pic3" position="{pixmap3.pos}" size="{pixmap.size}" zPosition="1"/>
    <widget name="pic4" position="{pixmap4.pos}" size="{pixmap.size}" zPosition="1"/>
    <widget name="pic5" position="{pixmap5.pos}" size="{pixmap.size}" zPosition="1"/>
    <widget name="pic6" position="{pixmap6.pos}" size="{pixmap.size}" zPosition="1"/>
    <widget name="pic7" position="{pixmap7.pos}" size="{pixmap.size}" zPosition="1"/>
    <widget name="pic8" position="{pixmap8.pos}" size="{pixmap.size}" zPosition="1"/>
    <widget name="pic9" position="{pixmap9.pos}" size="{pixmap.size}" zPosition="1"/>
    
    <widget name="infopanel" position="{infopanel.pos}" size="{infopanel.size}" zPosition="0"  backgroundColor="blue"/>
    <widget name="posx" position="{posx.pos}" size="{posx.size}" font="{font}" zPosition="1" />
    <widget name="posy" position="{posy.pos}" size="{posy.size}" font="{font}" zPosition="1" />
    <widget name="posz" position="{posz.pos}" size="{posz.size}" font="{font}" zPosition="1" />
    <widget name="placeslist" position="{placeslist.pos}" size="{placeslist.size}" zPosition="1"/>

            </screen>
            """
    def __init__(self, session):
        self.session = session
        size_w = getDesktop(0).size().width()    
        size_h = getDesktop(0).size().height()        
        print "DESKTOPsize is",size_w,size_h
        p_h = size_h/3
                
        infopanel_width = size_w - (p_h*3)
        infopanel_height = size_h
        label_height = 30
        font = "Regular;21"
        self.dict = {
                
                'font': font,
                
                'screen.size': "%i,%i"%(size_w,size_h),
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
                'placeslist.size': '%i,%i'%(infopanel_width,infopanel_height-(label_height*3)),
                
                }
        #print self.dict
        
        self.skin = applySkinVars(GoogleMapsMainScreen.raw_skin,self.dict)
        Screen.__init__(self, session)
        self["infopanel"] = Label()
        self["posx"] = Label("")
        self["posy"] = Label("")
        self["posz"] = Label("")
        self["placeslist"] = MenuList([])
        
        self["bg"] = Label()
        self["pic1"] = WebPixmap()
        self["pic2"] = WebPixmap()
        self["pic3"] = WebPixmap()
        self["pic4"] = WebPixmap()
        self["pic5"] = WebPixmap()
        self["pic6"] = WebPixmap()
        self["pic7"] = WebPixmap()
        self["pic8"] = WebPixmap()
        self["pic9"] = WebPixmap()
        self["setupActions"] = ActionMap(["OkCancelActions", "NumberActions","DirectionActions"],
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
             }, -1)
        self.onLayoutFinish.append(self.onLayoutFinished)
    
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
           
    def getURL(self,x,y,z):
        url = "http://khm1.google.com/kh?v=32&hl=de&x=%i&y=%i&z=%i"%(x,y,z)
        return url
   
    def getMapURL(self,x,y,z):
        url = "http://mt1.google.com/mt?v=w2t.99&hl=de&x=%i&y=%i&z=%i&s=G"%(x,y,z)
        return url   
        
def menu(menuid, **kwargs):
    #starting from main menu
    if menuid == "mainmenu":
        return [(_("Google Maps"), main, "googlemaps", 46)]
    return []

def main(session,**kwargs):
    session.openWithCallback(mainCB,GoogleMapsMainScreen)    

def mainCB():
    print "mainCB"
    config.plugins.GoogleMaps.position.x.save()    
    config.plugins.GoogleMaps.position.y.save()    
    config.plugins.GoogleMaps.position.z.save()    
    
def Plugins(path,**kwargs):
    return [PluginDescriptor(
        name="Google Maps", 
        description="browse google maps", 
        where = PluginDescriptor.WHERE_MENU,
        fnc = menu
        )]