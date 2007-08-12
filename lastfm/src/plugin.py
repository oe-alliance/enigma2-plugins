from enigma import eTimer, loadPic
from Screens.Screen import Screen
from Screens.HelpMenu import HelpableScreen
from Components.Pixmap import Pixmap, MovingPixmap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText
from Plugins.Plugin import PluginDescriptor

from StreamPlayer import StreamPlayer
from LastFMConfig import LastFMConfigScreen
from LastFM import LastFM, lastfm_event_register
from httpclient import getFile
from os import remove as os_remove
from random import randrange

###############################################################################        
plugin_path = ""

###############################################################################        

config.plugins.LastFM = ConfigSubsection()
config.plugins.LastFM.showcoverart = ConfigYesNo(default = True)
config.plugins.LastFM.username = ConfigText("user",fixed_size=False)
config.plugins.LastFM.password = ConfigText("passwd",fixed_size=False)
config.plugins.LastFM.timeoutstatustext = ConfigInteger(3,limits = (0, 10))
config.plugins.LastFM.timeouttabselect = ConfigInteger(2,limits = (0, 10))
config.plugins.LastFM.metadatarefreshinterval = ConfigInteger(1,limits = (0, 100))
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
            
            <widget name="info_artist" position="70,0" size="284,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="duration" position="354,0" size="60,30" valign=\"center\" halign=\"right\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="info_album" position="70,40" size="344,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="info_track" position="70,80" size="344,30" valign=\"center\" halign=\"left\" zPosition=\"2\"  foregroundColor=\"white\" font=\"Regular;18\" />          
            <widget name="info_cover" position="414,0" size="116,116" />          
            
            <widget name="tablist" position="0,120" size="150,260" scrollbarMode="showOnDemand" backgroundColor="#55cccccc"/>            
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
        self.streamplayer.onStateChanged.append(self.onStreamplayerStateChanged)
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
        self["duration"] = Label("-00:00")
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
             "green": self.skipTrack,
             "yellow": self.love,
             "blue": self.banTrack ,
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
        
    def onStreamplayerStateChanged(self,reason):
        if reason is self.streamplayer.STATE_PLAYLISTENDS:
            self.loadPlaylist()
        else:
            pass
    def onConnectSuccessful(self,text):
        self.setInfoLabel("login successful")      
    
    def onConnectFailed(self,text):
        self.setInfoLabel("login failed! "+text,timeout=False)

    def onTrackSkiped(self,reason):
        self.setInfoLabel("Track skiped")

    def onTrackLoved(self,reason):
        self.setInfoLabel("Track loved")
    
    def onTrackBanned(self,reason):
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
        self.loadPlaylist() 
        
    def onMetadataLoaded(self,metadata):
        self.updateGUI()
        self.guiupdatetimer.start(config.plugins.LastFM.metadatarefreshinterval.value*1000)
    
    def onPlaylistLoaded(self,reason):
        self.streamplayer.setPlaylist(self.playlist)
        self.streamplayer.play()

    def skipTrack(self):
        self.streamplayer.skip()
        self.updateGUI()
        
    def banTrack(self):
        self.ban()
        self.streamplayer.skip()
        self.updateGUI()
        
    def action_TabChanged(self):
        self.tabchangetimer.stop()
        self.tabchangetimer.start(config.plugins.LastFM.timeouttabselect.value*1000)
        
    def guiupdatetimerFired(self):
        self.updateGUI()
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
        self.session.openWithCallback(self.updateGUI, LastFMSaveScreen,self.streamplayer)
           
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
        self.streamplayer.stop(force=True)
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
            self.streamplayer.stop(force=True)
            self.setInfoLabel("stream stopped")
        else:
            self.setInfoLabel("starting stream",timeout=True)
            self.loadPlaylist()
            self.updateGUI() #forcing guiupdate, so we dont wait till guiupdatetimer fired
            self.guiupdatetimer.start(config.plugins.LastFM.metadatarefreshinterval.value*1000)

    def setInfoLabel(self,text,timeout=True):
        self.infolabelcleartimer.stop() 
        self["infolabel"].setText(text)
        if timeout is True:
            self.infolabelcleartimer.start(config.plugins.LastFM.timeoutstatustext.value*1000)
            
    def clearInfoLabel(self):
        self["infolabel"].setText("")
        
    def updateGUI(self):
        if self.streamplayer.is_playing is True:
            self["duration"].setText(self.streamplayer.getRemaining())
        else:
            self["duration"].setText("00:00")
            
        
        if self.streamplayer.is_playing is True:
            self["button_red"].setText(_("stop"))
        else:
            self["button_red"].setText(_("play"))            
        
        if self.streamplayer.is_playing is not True or self.shown is not True:
            return None
            
        if self.streamplayer.is_playing is True:
            self.setTitle("Last.FM: "+self.streamplayer.getMetadata("station"))
        else:
            self.setTitle("Last.FM")

        if self.streamplayer.is_playing is True:
            self["info_artist"].setText(self.streamplayer.getMetadata("creator"))
        else:
            self["info_artist"].setText("N/A")

        if self.streamplayer.is_playing is True:
            self["info_album"].setText(self.streamplayer.getMetadata("album"))
        else:
            self["info_album"].setText("N/A")

        if self.streamplayer.is_playing is True:
            self["info_track"].setText(self.streamplayer.getMetadata("title"))
        else:
            self["info_track"].setText("N/A")
        
        if self.streamplayer.getMetadata("image").startswith("http") and config.plugins.LastFM.showcoverart.value:
            self.imageconverter.convert(self.streamplayer.getMetadata("image"))
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
        
        creator = self.streamplayer.getMetadata("creator")
        if creator != "no creator" and creator != "N/A":
            x= {}
            x["_display"] = "Tracks similar to "+self.streamplayer.getMetadata("creator")
            x["stationurl"] = self.getSimilarArtistsURL(artist=creator)
            tags.append(x)
            
            x= {}
            x["_display"] = "Tracks liked by Fans of "+self.streamplayer.getMetadata("creator")
            x["stationurl"] = self.getArtistsLikedByFans(artist=creator)
            tags.append(x)

            x= {}
            x["_display"] = "Group of "+self.streamplayer.getMetadata("creator")
            x["stationurl"] = self.getArtistGroup(artist=creator)
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
    lastcreator=""
    def __init__(self,session,streamplayer):
        self.skin = """<screen position="0,0" size="720,576" flags="wfNoBorder" title="LastFMSaveScreen" >
                <widget name="cover" position="50,50" size="%i,%i" />          
              </screen>"""%(self.coverartsize[0],self.coverartsize[1])
    
        Screen.__init__(self,session)
        self.imageconverter = ImageConverter(self.coverartsize[0],self.coverartsize[1],self.setCoverArt)
        self.session = session
        self.streamplayer = streamplayer
        self["cover"] = MovingPixmap()
        self["actions"] = ActionMap(["InfobarChannelSelection","WizardActions", "DirectionActions","MenuActions","ShortcutActions","GlobalActions","HelpActions"], 
            {
             "ok": self.action_exit,
             "back": self.action_exit,
             }, -1)
        
        self.onLayoutFinish.append(self.update)
        self.updatetimer = eTimer()
        self.updatetimer.timeout.get().append(self.update)
        self.updatetimer.start(1000)
            
        if config.plugins.LastFM.sreensaver.coverartanimation.value:
            self.startmovingtimer = eTimer()
            self.startmovingtimer.timeout.get().append(self.movePixmap)
            self.startmovingtimer.start(config.plugins.LastFM.sreensaver.coverartinterval.value*1000)
        
    def action_ok(self):
        pass
    
    def action_exit(self):
        self.close()
        
    def setCoverArt(self,pixmap=None):
        if pixmap is None:
            self["cover"].instance.setPixmapFromFile(self.noCoverArtPNG)            
        else:
            self["cover"].instance.setPixmap(pixmap.__deref__())        
    
    def update(self):
        if self.streamplayer.getMetadata("creator") == self.lastcreator:
            pass
        else:
            self.lastcreator = self.streamplayer.getMetadata("creator")
            if config.plugins.LastFM.sreensaver.showcoverart.value is not True:
                pass#do nothing
            elif self.streamplayer.getMetadata("image").startswith("http") and config.plugins.LastFM.showcoverart.value:
                self.imageconverter.convert(self.streamplayer.getMetadata("image"))
            else:
                self.setCoverArt()
        self.updatetimer.start(1000)
        
    def movePixmap(self):
        self.startmovingtimer.stop() 
        newX = randrange(720-self.coverartsize[0]-1)
        newY = randrange(576-self.coverartsize[1]-1)
        self["cover"].moveTo(newX, newY, time = config.plugins.LastFM.sreensaver.coverartspeed.value)
        self["cover"].startMoving()
        self.startmovingtimer.start(config.plugins.LastFM.sreensaver.coverartinterval.value*1000)

class ImageConverter:
    
    lastURL = ""

    def __init__(self,width,height,callBack):
        self.callBack = callBack
        self.width = width
        self.height = height
        self.targetfile= "/tmp/coverart"+str(randrange(5000))
    
        
    def convert(self,sourceURL):
        if self.lastURL != sourceURL:
            extension = sourceURL.split(".")[-1]
            self.tmpfile = self.targetfile+"."+extension
            getFile(self.tmpfile,sourceURL,callback=self.onImageLoaded)
            self.lastURL = sourceURL

    def onImageLoaded(self,dummy):
            self.currPic = loadPic(self.tmpfile, self.width, self.height, 0,1, 0,1)
            os_remove(self.tmpfile)
            self.callBack(pixmap=self.currPic)
            