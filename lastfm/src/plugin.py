#from enigma import *
from enigma import eTimer
from enigma import eConsoleAppContainer

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen , HelpMenu              

from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigSubsection, ConfigSlider,ConfigInteger,ConfigYesNo, ConfigText
from Components.HelpMenuList import HelpMenuList

from Tools import Notifications

from Plugins.Plugin import PluginDescriptor


from StreamPlayer import StreamPlayer
from LastFMConfig import LastFMConfigScreen
from LastFM import LastFM

import os
###############################################################################        
myname = "Last.FM"     
myversion = "0.1"

plugin_path = ""

###############################################################################        

config.plugins.LastFM = ConfigSubsection()
config.plugins.LastFM.showcoverart = ConfigYesNo(default = False)
config.plugins.LastFM.username = ConfigText("user",fixed_size=False)
config.plugins.LastFM.password = ConfigText("passwd",fixed_size=False)
config.plugins.LastFM.timeoutstatustext = ConfigInteger(3,limits = (0, 10))
config.plugins.LastFM.timeouttabselect = ConfigInteger(2,limits = (0, 10))
config.plugins.LastFM.metadatarefreshinterval = ConfigInteger(5,limits = (0, 100))
config.plugins.LastFM.recommendedlevel = ConfigInteger(3,limits = (0, 100))

###############################################################################        
def main(session,**kwargs):
    session.open(LastFMScreenMain)    
        
def Plugins(path,**kwargs):
    global plugin_path
    plugin_path = path
    return PluginDescriptor(
        name=myname, 
        description="the social music revolution", 
        where = PluginDescriptor.WHERE_PLUGINMENU,
        fnc = main
        )
############################################################################### 
class LastFMScreenMain(Screen,HelpableScreen):
    skin = """
        <screen position="110,83" size="530,430" title="Last.FM" >
            
            <widget name="artist" position="0,0" size="70,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="album" position="0,40" size="70,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="track" position="0,80" size="70,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            
            <widget name="info_artist" position="70,0" size="344,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="info_album" position="70,40" size="344,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="info_track" position="70,80" size="344,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="info_cover" position="414,0" size="116,116" />          
            
            <widget name="tablist" position="0,120" size="150,260" scrollbarMode="showOnDemand" />            
            <widget name="streamlist" position="150,120" size="380,260" scrollbarMode="showOnDemand" />            
            
            <widget name="button_red" position="10,400" size="60,30" backgroundColor=\"red\" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="button_green" position="80,400" size="60,30" backgroundColor=\"green\" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\"/>            
            <widget name="button_yellow" position="150,400" size="60,30" backgroundColor=\"yellow\" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />            
            <widget name="button_blue" position="220,400" size="60,30" backgroundColor=\"blue\" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />            
            <widget name="infolabel" position="290,400" size="290,30" valign=\"center\" halign=\"center\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />           
        </screen>"""
         
    noCoverArtPNG = "/usr/share/enigma2/no_coverArt.png"
    
    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        self.skin = LastFMScreenMain.skin
        self.session = session
        self.lastfm = LastFM()
        self.streamplayer = StreamPlayer(session)
        self.imageconverter = ImageConverter(self.setCoverArt)
        Screen.__init__(self, session)
        self.tabs=[("personal Stations",self.loadPersonalStations)
                   ,("Global Tags",self.loadGlobalTags)
                   ,("Top Tracks",self.loadTopTracks)
                   ,("Recent Tracks",self.loadRecentTracks)
                   ,("Loved Tracks",self.loadLovedTracks)
                   ,("Banned Tracks",self.loadBannedTracks)
                   ,("Friends",self.loadFriends)
                   ,("Neighbours",self.loadNeighbours)
                   ]
        tablist =[]
        for tab in self.tabs:
            tablist.append((tab[0],tab))
        self.tablist = MenuList(tablist)
        self.tablist.onSelectionChanged.append(self.action_TabChanged)
        
        self["artist"] = Label(_("Artist")+":")
        self["album"] = Label(_("Album")+":")
        self["track"] = Label(_("Track")+":")
        
        self["info_artist"] = Label("N/A")
        self["info_album"] = Label("N/A")
        self["info_track"] = Label("N/A")
        self["info_cover"] = Pixmap()
        
        self["tablist"] = self.tablist
        self["streamlist"] = MenuList([])
        
        self["button_red"] = Label(_("play"))
        self["button_green"] = Label(_("skip"))
        self["button_yellow"] = Label(_("love"))
        self["button_blue"] = Label(_("ban"))
        self["infolabel"] = Label("")
        
        self["actions"] = ActionMap(["InfobarChannelSelection","WizardActions", "DirectionActions","MenuActions","ShortcutActions","GlobalActions","HelpActions"], 
            {
             "ok": self.action_ok,
             "back": self.action_exit,
             "red": self.action_startstop,
             "green": self.action_green,
             "yellow": self.action_yellow,
             "blue": self.action_blue ,
             "historyNext": self.action_nextTab,
             "historyBack": self.action_prevTab,
             
             "menu": self.action_menu,
             }, -1)
        self.helpList.append((self["actions"], "WizardActions", [("ok", _("switch to selected Station"))]))
        self.helpList.append((self["actions"], "WizardActions", [("back", _("quit Last.FM"))]))

        self.helpList.append((self["actions"], "MenuActions", [("menu", _("open Configuration"))]))

        self.helpList.append((self["actions"], "ShortcutActions", [("red", _("start/stop streaming"))]))
        self.helpList.append((self["actions"], "ShortcutActions", [("green", _("skip current Track"))]))
        self.helpList.append((self["actions"], "ShortcutActions", [("yellow", _("mark current Track as loved"))]))
        self.helpList.append((self["actions"], "ShortcutActions", [("blue", _("ban Track, never play again"))]))
        self.helpList.append((self["actions"], "InfobarChannelSelection", [("historyNext", _("select next Tab"))]))
        self.helpList.append((self["actions"], "InfobarChannelSelection", [("historyBack", _("select prev Tab"))]))

        self.onLayoutFinish.append(self.initLastFM)
        self.onLayoutFinish.append(self.tabchangedtimerFired)
        self.onLayoutFinish.append(self.setCoverArt)
        
        self.guiupdatetimer = eTimer()
        self.guiupdatetimer.timeout.get().append(self.updateGUI)
        
        self.tabchangetimer = eTimer()
        self.tabchangetimer.timeout.get().append(self.tabchangedtimerFired)
        
        self.infolabelcleartimer = eTimer()
        self.infolabelcleartimer.timeout.get().append(self.clearInfoLabel)
        
        
    def action_TabChanged(self):
        self.tabchangetimer.stop()
        self.tabchangetimer.start(config.plugins.LastFM.timeouttabselect.value*1000)
        
    def tabchangedtimerFired(self):
        self.tablist.getCurrent()[1][1]()
        self.tabchangetimer.stop()
        
    def action_nextTab(self):
        self.tablist.down()
            
    def action_prevTab(self):
        self.tablist.up()
        
    def showTab(self,tabnumber):
        self.currenttab=tabnumber
        print "showing tab",tabnumber
        print self.tabs[tabnumber]
                
    def action_menu(self):
        self.session.open(LastFMConfigScreen)

    def action_exit(self):
        print "action_exit"
        self.guiupdatetimer.stop()
        self.streamplayer.stop()
        self.close()

    def action_ok(self):
        print "action_ok"
        selectedTag = self["streamlist"].l.getCurrentSelection()[1]
        self.lastfm.changestation(selectedTag)
        
    def action_startstop(self):
        if self.streamplayer.is_playing:
            self.streamplayer.stop()
            self.lastfm.metadata = {}
            self.setInfoLabel("stream stopped")
        
        else:
            self.setInfoLabel("starting stream",timeout=True)
            if self.lastfm.info.has_key("stream_url"):
                self.streamplayer.play(self.lastfm.info["stream_url"])
                self.guiupdatetimer.start(config.plugins.LastFM.metadatarefreshinterval.value*1000)

    def action_green(self):
        self.lastfm.skip()
        self.setInfoLabel("Track skipped",timeout=True)
        
    def action_yellow(self):
        self.lastfm.love()
        self.setInfoLabel("Track loved",timeout=True)
        
    def action_blue(self):
        self.lastfm.ban()
        self.setInfoLabel("Track banned",timeout=True)
           
    def setInfoLabel(self,text,timeout=True):
        self.infolabelcleartimer.stop() 
        self["infolabel"].setText(text)
        if timeout is True:
            self.infolabelcleartimer.start(config.plugins.LastFM.timeoutstatustext.value*1000)
            
    def clearInfoLabel(self):
        self["infolabel"].setText("")
        
    def updateGUI(self):
        if self.streamplayer.is_playing is not True:
            return None
        print "updateGUI"
        
        if self.lastfm.state:
            self.lastfm.getmetadata()
        
        if self.streamplayer.is_playing:
            self["button_red"].setText(_("stop"))
        else:
            self["button_red"].setText(_("play"))            
            
        if self.lastfm.metadata.has_key("station"):
            self.setTitle(myname+": "+self.lastfm.metadata["station"])
        else:
            self.setTitle(myname)

        if self.lastfm.metadata.has_key("artist"):
            self["info_artist"].setText(self.lastfm.metadata["artist"])
        else:
            self["info_artist"].setText("N/A")

        if self.lastfm.metadata.has_key("album"):
            self["info_album"].setText(self.lastfm.metadata["album"])
        else:
            self["info_album"].setText("N/A")

        if self.lastfm.metadata.has_key("track"):
            self["info_track"].setText(self.lastfm.metadata["track"])
        else:
            self["info_track"].setText("N/A")
        
        if self.lastfm.metadata.has_key("albumcover_large") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(self.lastfm.metadata["albumcover_large"])
        elif self.lastfm.metadata.has_key("albumcover_medium") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(self.lastfm.metadata["albumcover_medium"])
        elif self.lastfm.metadata.has_key("albumcover_small") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(self.lastfm.metadata["albumcover_small"],self.setCoverArt)
        else:
            self.setCoverArt()
        
        if self.streamplayer.is_playing:
            self.guiupdatetimer.start(config.plugins.LastFM.metadatarefreshinterval.value*1000)
        else:
            self.setTitle(myname)
            self.setCoverArt()
            self["info_artist"].setText("N/A")
            self["info_album"].setText("N/A")
            self["info_track"].setText("N/A")
            
    def setCoverArt(self,filename=None):
        #print "coverart from file",filename
        if filename is None or os.path.isfile(filename) is False:
            self["info_cover"].instance.setPixmapFromFile(self.noCoverArtPNG)            
        else:
            self["info_cover"].instance.setPixmapFromFile(filename)
    
    def initLastFM(self):
        self.setInfoLabel("loggin into last.fm")
        (result,resulttext) = self.lastfm.connect(config.plugins.LastFM.username.value,config.plugins.LastFM.password.value)
        if result is False:
            self.setInfoLabel("login failed")
            Notifications.AddPopup("Login to Last.FM failed!", resulttext,MessageBox.TYPE_INFO, 5)        
#            if self.shown:
#                self.session.open(MessageBox, resulttext, MessageBox.TYPE_ERROR)
        else:
            self.setInfoLabel("login successful",timeout=True)      

    def loadPersonalStations(self):
        tags = []
        x= {}
        x["_display"] = "Personal Radio"
        x["stationurl"] = self.lastfm.getPersonalURL(config.plugins.LastFM.username.value,level=config.plugins.LastFM.recommendedlevel.value)
        tags.append(x)
        
        x= {}
        x["_display"] = "Neighbours Tracks"
        x["stationurl"] = self.lastfm.getNeighboursURL(config.plugins.LastFM.username.value)
        tags.append(x)
        
        x= {}
        x["_display"] = "Loved Tracks"
        x["stationurl"] = self.lastfm.getLovedURL(config.plugins.LastFM.username.value)
        tags.append(x)
        
        if self.lastfm.metadata.has_key("artist"):
            x= {}
            x["_display"] = "similar Tracks of current Artist"
            x["stationurl"] = self.lastfm.getSimilarArtistsURL()
            tags.append(x)
            
            x= {}
            x["_display"] = "Tracks liked by Fans of current Track"
            x["stationurl"] = self.lastfm.getArtistsLikedByFans()
            tags.append(x)

            x= {}
            x["_display"] = "Group of Artist of current Track"
            x["stationurl"] = self.lastfm.getArtistGroup()
            tags.append(x)
        

        self.buildMenuList(tags)
        
    def loadGlobalTags(self):
        self.setInfoLabel("loading Global Tags")
        tags = self.lastfm.getGlobalTags()
        self.buildMenuList(tags)

    def loadTopTracks(self):
        self.setInfoLabel("loading Top Tacks")
        tracks = self.lastfm.getTopTracks(config.plugins.LastFM.username.value)
        self.buildMenuList(tracks)

    def loadRecentTracks(self):
        self.setInfoLabel("loading recent Tracks")
        tracks = self.lastfm.getRecentTracks(config.plugins.LastFM.username.value)
        self.buildMenuList(tracks)

    def loadLovedTracks(self):
        self.setInfoLabel("loading loved Tracks")
        tracks = self.lastfm.getRecentLovedTracks(config.plugins.LastFM.username.value)
        self.buildMenuList(tracks)

    def loadBannedTracks(self):
        self.setInfoLabel("loading loved Tracks")
        tracks = self.lastfm.getRecentBannedTracks(config.plugins.LastFM.username.value)
        self.buildMenuList(tracks)
        
    def loadNeighbours(self):
        self.setInfoLabel("loading Neighbours")
        tracks = self.lastfm.getNeighbours(config.plugins.LastFM.username.value)
        self.buildMenuList(tracks)

    def loadFriends(self):
        self.setInfoLabel("loading Friends")
        tracks = self.lastfm.getFriends(config.plugins.LastFM.username.value)
        self.buildMenuList(tracks)

    def buildMenuList(self,items):
        menuliste = []
        for i in items:
            menuliste.append((i['_display'],i['stationurl']))
        self["streamlist"].l.setList(menuliste) 


class ImageConverter:
    
    targetfile= "/tmp/coverart.png"
    lastURL =""

    def __init__(self,callBack):
        self.callBack = callBack
        self.container = eConsoleAppContainer()
        self.container.appClosed.get().append(self.appClosed)
        self.container.dataAvail.get().append(self.dataAvail)
    
    def dataAvail(self,text):
        print "imageconverter:",text

    def convert(self,sourceURL):
        #print "start converting coverart",sourceURL
        try: # this is not nice... i have to implement a function to check it while activating CoverArts
            import Image
        except:
            pass
        
        if self.lastURL == sourceURL:
            pass #self.callBack(filename=self.targetfile)
        else:
            cmd = "/usr/bin/python "+plugin_path+"/imageconverter.py '"+sourceURL+"' '"+self.targetfile+"' "
            self.container.execute(cmd)
            self.lastURL = sourceURL
        
    def appClosed(self,text):
        #print "appClosed",text
        self.callBack(filename=self.targetfile)