from enigma import eTimer
from enigma import eConsoleAppContainer
from enigma import loadPic

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen , HelpMenu              

from Components.Pixmap import Pixmap,MovingPixmap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigSubsection, ConfigSlider,ConfigInteger,ConfigYesNo, ConfigText
from Components.HelpMenuList import HelpMenuList


from Tools import Notifications

from Plugins.Plugin import PluginDescriptor

from StreamPlayer import StreamPlayer
from LastFMConfig import LastFMConfigScreen
from LastFM import LastFM, lastfm_event_register
import httpclient
import os
import urllib

import random

###############################################################################        
plugin_path = ""

###############################################################################        

config.plugins.LastFM = ConfigSubsection()
config.plugins.LastFM.showcoverart = ConfigYesNo(default = True)
config.plugins.LastFM.username = ConfigText("user",fixed_size=False)
config.plugins.LastFM.password = ConfigText("passwd",fixed_size=False)
config.plugins.LastFM.timeoutstatustext = ConfigInteger(3,limits = (0, 10))
config.plugins.LastFM.timeouttabselect = ConfigInteger(2,limits = (0, 10))
config.plugins.LastFM.metadatarefreshinterval = ConfigInteger(5,limits = (0, 100))
config.plugins.LastFM.recommendedlevel = ConfigInteger(3,limits = (0, 100))
config.plugins.LastFM.sendSubmissions = ConfigYesNo(default = False)

config.plugins.LastFM.sreensaver = ConfigSubsection()
config.plugins.LastFM.sreensaver.use = ConfigYesNo(default = True)
config.plugins.LastFM.sreensaver.wait = ConfigInteger(30,limits = (0, 1000))
config.plugins.LastFM.sreensaver.showcoverart = ConfigYesNo(default = True)
config.plugins.LastFM.sreensaver.coverartanimation = ConfigYesNo(default = True)
config.plugins.LastFM.sreensaver.coverartspeed = ConfigInteger(10,limits = (0, 100))
config.plugins.LastFM.sreensaver.coverartinterval = ConfigInteger(10,limits = (0, 100))

###############################################################################        
def main(session,**kwargs):
    session.open(LastFMScreenMain)    
        
def startScrobbler(reason, **kwargs):
    if "session" in kwargs and config.plugins.LastFM.sendSubmissions.value:
        from scrobbler import EventListener
        evl = EventListener(kwargs["session"])
        evl.startListenToEvents()
        
def Plugins(path,**kwargs):
    global plugin_path
    plugin_path = path
    return [PluginDescriptor(
        name="Last.FM", 
        description="the social music revolution", 
        where = PluginDescriptor.WHERE_PLUGINMENU,
        fnc = main
        ),
        PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = startScrobbler)
        ]
############################################################################### 
class LastFMScreenMain(Screen,HelpableScreen,LastFM):
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
        self.skin = LastFMScreenMain.skin
        Screen.__init__(self, session)
        HelpableScreen.__init__(self)
        LastFM.__init__(self)
        self.session = session
        self.streamplayer = StreamPlayer(session)
        self.streamplayer.onStateChanged.append(self.updateGUI)
        self.imageconverter = ImageConverter(116,116,self.setCoverArt)
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
        
        self["actions"] = ActionMap(["InfobarChannelSelection","WizardActions", "DirectionActions","MenuActions","ShortcutActions","GlobalActions","HelpActions","NumberActions"], 
            {
             "ok": self.action_ok,
             "back": self.action_exit,
             "red": self.action_startstop,
             "green": self.skip,
             "yellow": self.love,
             "blue": self.ban ,
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
        self.guiupdatetimer.timeout.get().append(self.guiupdatetimerFired)
        self.guiupdatetimer.start(config.plugins.LastFM.metadatarefreshinterval.value*1000)
        
        self.tabchangetimer = eTimer()
        self.tabchangetimer.timeout.get().append(self.tabchangedtimerFired)
        
        self.infolabelcleartimer = eTimer()
        self.infolabelcleartimer.timeout.get().append(self.clearInfoLabel)

        self.screensavertimer = eTimer()
        self.screensavertimer.timeout.get().append(self.startScreensaver)
        self.onShown.append(self.startScreensaverTimer)

    def initLastFM(self):
        self.setInfoLabel("loggin into last.fm")
        self.connect(config.plugins.LastFM.username.value,config.plugins.LastFM.password.value)
    
    def onConnectSuccessful(self,text):
        self.setInfoLabel("login successful")      
    
    def onConnectFailed(self,text):
        self.setInfoLabel("login failed! "+text,timeout=False)

    def onTrackSkiped(self,reason):
        self.setInfoLabel("Track skiped")

    def onTrackLoved(self,reason):
        self.setInfoLabel("Track loved")
    
    def onTrackBaned(self,reason):
        self.setInfoLabel("Track baned")
    
    def onCommandFailed(self,reason):
        self.setInfoLabel(reason)

    def onGlobalTagsLoaded(self,tags):
        self.setInfoLabel("Global Tags loaded")
        self.buildMenuList(tags)

    def onTopTracksLoaded(self,tracks):
        self.setInfoLabel("Top Tracks loaded")
        self.buildMenuList(tracks)

    def onRecentTracksLoaded(self,tracks):
        self.setInfoLabel("recent Tracks loaded")
        self.buildMenuList(tracks)
        
    def onRecentBannedTracksLoaded(self,tracks):
        self.setInfoLabel("banned Tracks loaded")
        self.buildMenuList(tracks)

    def onRecentLovedTracksLoaded(self,tracks):
        self.setInfoLabel("loved Tracks loaded")
        self.buildMenuList(tracks)

    def onNeighboursLoaded(self,user):
        self.setInfoLabel("Neighbours loaded")
        self.buildMenuList(user)

    def onFriendsLoaded(self,user):
        self.setInfoLabel("Friends loaded")
        self.buildMenuList(user)
    
    def onStationChanged(self,reason):
        self.setInfoLabel(reason)    
        
    def onMetadataLoaded(self,metadata):
        self.updateGUI()
        self.guiupdatetimer.start(config.plugins.LastFM.metadatarefreshinterval.value*1000)

    def action_TabChanged(self):
        self.tabchangetimer.stop()
        self.tabchangetimer.start(config.plugins.LastFM.timeouttabselect.value*1000)
        
    def guiupdatetimerFired(self):
        if self.streamplayer.is_playing:
            self.getMetadata()
        self.guiupdatetimer.start(config.plugins.LastFM.metadatarefreshinterval.value*1000)
        
    def tabchangedtimerFired(self):
        self.tablist.getCurrent()[1][1]()
        self.tabchangetimer.stop()

    def startScreensaverTimer(self):
        if config.plugins.LastFM.sreensaver.use.value:
            self.screensavertimer.start(config.plugins.LastFM.sreensaver.wait.value*1000)

    def resetScreensaverTimer(self):
        self.screensavertimer.stop()
        self.screensavertimer.start(config.plugins.LastFM.sreensaver.wait.value*1000)
        
    def startScreensaver(self):
        self.screensavertimer.stop()
        self.session.openWithCallback(self.updateGUI, LastFMSaveScreen,self.metadata)
           
    def action_nextTab(self):
        self.tablist.down()
        self.resetScreensaverTimer()
        
    def action_prevTab(self):
        self.tablist.up()
        self.resetScreensaverTimer()

    def action_menu(self):
        self.session.open(LastFMConfigScreen)
        self.resetScreensaverTimer()

    def action_exit(self):
        self.screensavertimer.stop()
        self.guiupdatetimer.stop()
        self.streamplayer.stop()
        self.streamplayer.onStateChanged=[]
        
        self.close()

    def action_ok(self):
        x = self["streamlist"].l.getCurrentSelection()
        if x is None:
            pass
        elif len(x) >1:
            self.changeStation(x[1])
            self.resetScreensaverTimer()

    def action_startstop(self):
        self.resetScreensaverTimer()
        if self.streamplayer.is_playing:
            self.streamplayer.stop()
            self.metadata = {}
            self.setInfoLabel("stream stopped")
        
        else:
            self.setInfoLabel("starting stream",timeout=True)
            if self.info.has_key("stream_url"):
                self.streamplayer.play(self.info["stream_url"])
                self.guiupdatetimer.start(config.plugins.LastFM.metadatarefreshinterval.value*1000)

    def setInfoLabel(self,text,timeout=True):
        self.infolabelcleartimer.stop() 
        self["infolabel"].setText(text)
        if timeout is True:
            self.infolabelcleartimer.start(config.plugins.LastFM.timeoutstatustext.value*1000)
            
    def clearInfoLabel(self):
        self["infolabel"].setText("")
        
    def updateGUI(self):
        print "updateGUI"
        if self.streamplayer.is_playing is True:
            self["button_red"].setText(_("stop"))
        else:
            self["button_red"].setText(_("play"))            
        
        if self.streamplayer.is_playing is not True or self.shown is not True:
            return None
            
        if self.metadata.has_key("station"):
            self.setTitle("Last.FM: "+self.metadata["station"])
        else:
            self.setTitle("Last.FM")

        if self.metadata.has_key("artist"):
            self["info_artist"].setText(self.metadata["artist"])
        else:
            self["info_artist"].setText("N/A")

        if self.metadata.has_key("album"):
            self["info_album"].setText(self.metadata["album"])
        else:
            self["info_album"].setText("N/A")

        if self.metadata.has_key("track"):
            self["info_track"].setText(self.metadata["track"])
        else:
            self["info_track"].setText("N/A")
        
        if self.metadata.has_key("albumcover_large") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(self.metadata["albumcover_large"])
        elif self.metadata.has_key("albumcover_medium") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(self.metadata["albumcover_medium"])
        elif self.metadata.has_key("albumcover_small") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(self.metadata["albumcover_small"],self.setCoverArt)
        else:
            self.setCoverArt()
        
        if self.streamplayer.is_playing is not True:
            self.setTitle(myname)
            self.setCoverArt()
            self["info_artist"].setText("N/A")
            self["info_album"].setText("N/A")
            self["info_track"].setText("N/A")
        
    def setCoverArt(self,pixmap=None):
        if pixmap is None:
            self["info_cover"].instance.setPixmapFromFile(self.noCoverArtPNG)            
        else:
            self["info_cover"].instance.setPixmap(pixmap.__deref__())
    

    def loadPersonalStations(self):
        tags = []
        x= {}
        x["_display"] = "Personal Radio"
        x["stationurl"] = self.getPersonalURL(config.plugins.LastFM.username.value,level=config.plugins.LastFM.recommendedlevel.value)
        tags.append(x)
        
        x= {}
        x["_display"] = "Neighbours Tracks"
        x["stationurl"] = self.getNeighboursURL(config.plugins.LastFM.username.value)
        tags.append(x)
        
        x= {}
        x["_display"] = "Loved Tracks"
        x["stationurl"] = self.getLovedURL(config.plugins.LastFM.username.value)
        tags.append(x)
        
        if self.metadata.has_key("artist"):
            x= {}
            x["_display"] = "similar Tracks of current Artist"
            x["stationurl"] = self.getSimilarArtistsURL()
            tags.append(x)
            
            x= {}
            x["_display"] = "Tracks liked by Fans of current Track"
            x["stationurl"] = self.getArtistsLikedByFans()
            tags.append(x)

            x= {}
            x["_display"] = "Group of Artist of current Track"
            x["stationurl"] = self.getArtistGroup()
            tags.append(x)
        
        self.buildMenuList(tags)
        
    def loadGlobalTags(self):
        self.setInfoLabel("loading Global Tags")
        tags = self.getGlobalTags()

    def loadTopTracks(self):
        self.setInfoLabel("loading Top Tacks")
        tracks = self.getTopTracks(config.plugins.LastFM.username.value)

    def loadRecentTracks(self):
        self.setInfoLabel("loading recent Tracks")
        tracks = self.getRecentTracks(config.plugins.LastFM.username.value)

    def loadLovedTracks(self):
        self.setInfoLabel("loading loved Tracks")
        tracks = self.getRecentLovedTracks(config.plugins.LastFM.username.value)

    def loadBannedTracks(self):
        self.setInfoLabel("loading loved Tracks")
        tracks = self.getRecentBannedTracks(config.plugins.LastFM.username.value)
        
    def loadNeighbours(self):
        self.setInfoLabel("loading Neighbours")
        tracks = self.getNeighbours(config.plugins.LastFM.username.value)

    def loadFriends(self):
        self.setInfoLabel("loading Friends")
        tracks = self.getFriends(config.plugins.LastFM.username.value)

    def buildMenuList(self,items):
        menuliste = []
        for i in items:
            menuliste.append((i['_display'],i['stationurl']))
        self["streamlist"].l.setList(menuliste) 

class LastFMSaveScreen(Screen):
    skin = """<screen position="0,0" size="720,576" flags="wfNoBorder" title="LastFMSaveScreen" >
                <widget name="cover" position="50,50" size="200,200" />          
              </screen>"""
    noCoverArtPNG = "/usr/share/enigma2/no_coverArt.png"
    coverartsize= [200,200]
    def __init__(self,session,initialMetadata):
        self.skin = """<screen position="0,0" size="720,576" flags="wfNoBorder" title="LastFMSaveScreen" >
                <widget name="cover" position="50,50" size="%i,%i" />          
              </screen>"""%(self.coverartsize[0],self.coverartsize[1])
    
        Screen.__init__(self,session)
        self.imageconverter = ImageConverter(self.coverartsize[0],self.coverartsize[1],self.setCoverArt)
        self.session = session
        self.initialMetadata = initialMetadata
        self["cover"] = MovingPixmap()
        self["actions"] = ActionMap(["InfobarChannelSelection","WizardActions", "DirectionActions","MenuActions","ShortcutActions","GlobalActions","HelpActions"], 
            {
             "ok": self.action_exit,
             "back": self.action_exit,
             }, -1)
        
        self.onLayoutFinish.append(self.update)
        self.onLayoutFinish.append(self.registerToMetadataUpdates)
        
        if config.plugins.LastFM.sreensaver.coverartanimation.value:
            self.startmovingtimer = eTimer()
            self.startmovingtimer.timeout.get().append(self.movePixmap)
            self.startmovingtimer.start(config.plugins.LastFM.sreensaver.coverartinterval.value*1000)
        
    def action_ok(self):
        pass
    
    def action_exit(self):
        lastfm_event_register.removeOnMetadataChanged(self.update)
        self.close()
        
    def setCoverArt(self,pixmap=None):
        if pixmap is None:
            self["cover"].instance.setPixmapFromFile(self.noCoverArtPNG)            
        else:
            self["cover"].instance.setPixmap(pixmap.__deref__())
            
    def registerToMetadataUpdates(self):
        lastfm_event_register.addOnMetadataChanged(self.update)#added here, to make shure that is called after onLayoutFinished
        
    
    def update(self,metadata=None):
        
        if metadata is None:
            metadata = self.initialMetadata
            
        if config.plugins.LastFM.sreensaver.showcoverart.value is not True:
            pass#do nothing
        elif metadata.has_key("albumcover_large") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(metadata["albumcover_large"])
        elif metadata.has_key("albumcover_medium") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(metadata["albumcover_medium"])
        elif metadata.has_key("albumcover_small") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(metadata["albumcover_small"],self.setCoverArt)
        else:
            self.setCoverArt()

    def movePixmap(self):
        self.startmovingtimer.stop() 
        newX = random.randrange(720-self.coverartsize[0]-1)
        newY = random.randrange(576-self.coverartsize[1]-1)
        self["cover"].moveTo(newX, newY, time = config.plugins.LastFM.sreensaver.coverartspeed.value)
        self["cover"].startMoving()
        self.startmovingtimer.start(config.plugins.LastFM.sreensaver.coverartinterval.value*1000)

class ImageConverter:
    
    lastURL = ""

    def __init__(self,width,height,callBack):
        self.callBack = callBack
        self.width = width
        self.height = height
        self.targetfile= "/tmp/coverart"+str(random.randrange(5000))
    
        
    def convert(self,sourceURL):
        if self.lastURL != sourceURL:
            extension = sourceURL.split(".")[-1]
            self.tmpfile = self.targetfile+"."+extension
            httpclient.getFile(self.tmpfile,sourceURL,callback=self.onImageLoaded)
            self.lastURL = sourceURL

    def onImageLoaded(self,dummy):
            self.currPic = loadPic(self.tmpfile, self.width, self.height, 0,1, 0,1)
            os.remove(self.tmpfile)
            self.callBack(pixmap=self.currPic)
            