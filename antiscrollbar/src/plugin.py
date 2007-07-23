# (c) 2006 3c5x9, dream@3c5x9.de
# This Software is Free, use it where you want, when you want for whatever you want and modify it if you want. but don't remove my copyright!

from Screens.Screen import Screen
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Input import Input
from Plugins.Plugin import PluginDescriptor
#############
from enigma import ePoint, eSize
#############
from ConfigParser import ConfigParser, DEFAULTSECT, DuplicateSectionError

###############################################################################        
myname = "AntiScrollbar"     
myversion = "0.1"
###############################################################################        
class AntiScrollMain(Screen):
    step = 5    
    def __init__(self, session, args = 0):
        config = AntiScrollConfig()
        try:
          profil = config.getLastProfile()
          self.size = [profil["sizex"],profil["sizey"]]
          self.position = [profil["posx"],profil["posy"]]             
        except Exception:
          config.setProfile("standard",[200,200],[200,200])
          config = AntiScrollConfig()          
          profil = config.getProfile("standard")
          
        self.size = [profil["sizex"],profil["sizey"]]
        self.position = [profil["posx"],profil["posy"]]           
        ss  ="<screen position=\"%i,%i\" size=\"%i,%i\" title=\"%s\"  flags=\"wfNoBorder\" >" %(profil["posx"],profil["posy"],profil["sizex"],profil["sizey"],myname)
        ss +="<widget name=\"label\" position=\"0,0\" size=\"%i,%i\"  backgroundColor=\"black\"  />" %(profil["sizex"],profil["sizey"])
        ss +="</screen>"
        self.skin = ss
        self.session = session
        Screen.__init__(self, session)
        self.menu = args
        self["label"] = Label()
        self["actions"] = ActionMap(["WizardActions", "DirectionActions","MenuActions","NumberActions"], 
            {
             "ok": 	self.go,
             "back": 	self.close,
             "menu": 	self.openmenu,
             "down": 	self.down,
             "up": 	self.up,
             "left":	self.left,
             "right":	self.right,
             "2":	self.key2,
             "8":	self.key8,
             "4":	self.key4,
             "6":	self.key6,
             }, -1)


    def go(self):
      pass
    def openmenu(self):
      self.session.open(AntiScrollMenu,callback=self.menuCallback,size=self.size,position=self.position)
    def menuCallback(self,size,position):
      self.size = size
      self.position = position
      self.move(self.position[0],self.position[1])
      self.resize(self.size[0],self.size[1])
       
    def key2(self):
      self.size= [self.size[0],self.size[1]-self.step]
      self.resize(self.size[0],self.size[1])
    def key8(self):
      self.size= [self.size[0],self.size[1]+self.step]
      self.resize(self.size[0],self.size[1])
    def key4(self):
      self.size= [self.size[0]-self.step,self.size[1]]
      self.resize(self.size[0],self.size[1])
    def key6(self):
      self.size= [self.size[0]+self.step,self.size[1]]
      self.resize(self.size[0],self.size[1])
    
    def down(self):
      self.position = [self.position[0],self.position[1]+self.step]
      self.move(self.position[0],self.position[1])
    def up(self):
      self.position = [self.position[0],self.position[1]-self.step]
      self.move(self.position[0],self.position[1])
    def left(self):
      self.position = [self.position[0]-self.step,self.position[1]]
      self.move(self.position[0],self.position[1])
    def right(self):
      self.position = [self.position[0]+self.step,self.position[1]]
      self.move(self.position[0],self.position[1])
    
    def move(self, x, y):
      print "["+myname+"] moving to", str(x) + ":" + str(y)
      self.instance.move(ePoint(x, y))
          
    def resize(self, w, h):
      print "["+myname+"] resizing to", str(w) + "x" + str(h)
      self.instance.resize(eSize(*(w, h)))
      self["label"].instance.resize(eSize(*(w, h)))
#############################
class  AntiScrollMenu(Screen):
  def __init__(self,session,callback=None,size=None,position=None,arg=0):
    self.session = session
    self.callBack = callback
    self.size= size
    self.position = position
    ss  ="<screen position=\"200,200\" size=\"300,200\" title=\"%s Menu\" >" % myname
    ss +="<widget name=\"menu\" position=\"0,0\" size=\"300,150\" scrollbarMode=\"showOnDemand\" />" 
    ss +="<widget name=\"label\" position=\"0,150\" size=\"300,50\"  font=\"Regular;18\" valign=\"center\" halign=\"center\" />"
    ss +="</screen>"
    self.skin = ss
    Screen.__init__(self,session)
    list = []
    list.append(("load Profile",self.load))
    list.append(("save Profile",self.save))
    list.append(("save new Profile",self.savenew))
    self["menu"] = MenuList(list)
    self["label"] = Label("written by 3c5x9, V"+myversion)
    self["actions"] = ActionMap(["WizardActions", "DirectionActions","MenuActions","NumberActions"],
            {
             "ok": self.go,
             "back": self.close,
             }, -1)
  def go(self):
    selection = self["menu"].getCurrent()
    selection[1]()
  
  def load(self):
    config = AntiScrollConfig()
    liste = []
    for i in config.getProfiles():
      liste.append((i,i))
    self.session.openWithCallback(self.loadProfile,ChoiceBox,_("select Profile to load"),liste)
    
  def loadProfile(self,value):
    if value is not None:
      config = AntiScrollConfig()
      profil = config.getProfile(value[1])
      if profil is not False:
        self.callBack([profil["sizex"],profil["sizey"]],[profil["posx"],profil["posy"]])
  def savenew(self):
    self.session.openWithCallback(self.profilnameEntered,InputBox, title=_("Please enter a name for the Profile"), text="Profil", maxSize=False, type=Input.TEXT)
    
  def profilnameEntered(self,value):
    if value is not None:
      config = AntiScrollConfig()
      config.setProfile(value,self.size,self.position)   
  def save(self):
    config = AntiScrollConfig()
    liste = []
    for i in config.getProfiles():
      liste.append((i,i))
    self.session.openWithCallback(self.saveProfile,ChoiceBox,_("select Profile to save"),liste)
  def saveProfile(self,value):
    if value is not None:
      config = AntiScrollConfig()
      config.setProfile(value[1],self.size,self.position)
                       
                          
##############################
class AntiScrollConfig:
    configfile = "/etc/enigma2/AntiScrollbar.conf"
    
    def __init__(self):
        self.configparser = ConfigParser()
        self.configparser.read(self.configfile)
    def setLastProfile(self,name):
        self.configparser.set(DEFAULTSECT,"lastprofile",name)
        self.writeConfig()
    def getLastProfile(self):
        last = self.configparser.get(DEFAULTSECT,"lastprofile")    
        return self.getProfile(last)
    def getProfiles(self):
        profiles=[]
        sections = self.configparser.sections()
        for section in sections:
          profiles.append(section)
        return profiles

    def getProfile(self,name):
      if self.configparser.has_section(name) is True:
        print "loading profile ",name
        l={}
        l["sizex"] = int(self.configparser.get(name, "size_x"))
        l["sizey"] = int(self.configparser.get(name, "size_y"))
        l["posx"] = int(self.configparser.get(name, "position_x"))
        l["posy"] = int(self.configparser.get(name, "position_y"))
        self.setLastProfile(name)
        return l
      else:
        print "couldnt find profil", name
        return False
    def setProfile(self,name,size,position):
        try:
          self.configparser.add_section(name)
          self.configparser.set(name, "size_x",size[0])
          self.configparser.set(name, "size_y",size[1])
          self.configparser.set(name, "position_x",position[0])
          self.configparser.set(name, "position_y",position[1])
          self.writeConfig()
          return True
        except DuplicateSectionError:
          self.deleteProfile(name)
          self.setProfile(name,size,position)
                                                                                                    
    def deleteProfile(self,name):
        self.configparser.remove_section(name)
        self.writeConfig()

    def writeConfig(self):
        fp = open(self.configfile,"w")
        self.configparser.write(fp)
        fp.close()
                            
    
     
#############################
def main(session, **kwargs):
  session.open(AntiScrollMain)
def Plugins(**kwargs):
  return [PluginDescriptor(name=myname,description="overlay for scrolling bars",where = PluginDescriptor.WHERE_PLUGINMENU,fnc = main),
          PluginDescriptor(name=myname,description="overlay for scrolling bars",where = PluginDescriptor.WHERE_EXTENSIONSMENU,fnc = main)]
