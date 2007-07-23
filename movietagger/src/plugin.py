# this is free software. use it for whatever you what or modify it. 
# but dont remove these three lines and dont publish only .pyc-files of these files!
# 3c5x9, 3c5x9@gmx.de

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MovieList import MovieList
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Components.MultiContent import MultiContentEntryText
from enigma import eListboxPythonMultiContent, eListbox, eServiceCenter

from Tools.Directories import *

class MovieTagger(Screen):
	skin = """
		<screen position="100,100" size="550,400" title="Movie Tagger" >
			<widget name="moviename" position="10,10" size="530,50"   font="Regular;25"/>
			<widget name="cTaglist" position="10,60" size="220,280"  scrollbarMode="showOnDemand"/>
			<widget name="aTaglist" position="240,60" size="300,280"  scrollbarMode="showOnDemand"/>
			<widget name="buttonred" position="6,350" size="130,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        	<widget name="buttongreen" position="142,350" size="130,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        	<widget name="buttonyellow" position="278,350" size="130,40" backgroundColor="yellow" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/> 
        	<widget name="buttonblue" position="414,350" size="130,40" backgroundColor="blue" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;18"/>
		</screen>"""
	currList = None
	pretagfile = "/etc/enigma2/movietags"
    
	def __init__(self, session, service):
		self.session = session
		self.service = service
		self.serviceHandler = eServiceCenter.getInstance()
		self.info = self.serviceHandler.info(self.service)
		
		self.skin = MovieTagger.skin
		Screen.__init__(self, session)
		self["moviename"] = Label(self.info.getName(self.service))
		self["buttonred"] = Label(_("red"))
		self["buttongreen"] = Label(_("green"))
		self["buttonyellow"] = Label(_("yellow"))
		self["buttonblue"] = Label(_("blue"))
		self["cTaglist"] = MenuList([])
		self["aTaglist"] = TagMenuList([])
		self["actions"] = ActionMap(["WizardActions","MenuActions","ShortcutActions"], 
            {
             "back": 	self.close,
             "red": 	self.keyRed,
             "green": 	self.keyGreen,
             "yellow": 	self.keyYellow,
             "blue": 	self.keyBlue,
             "up": 		self.up,
             "down": 	self.down,
             "left": 	self.left,
             "right": 	self.right,
             }, -1)
		self.loadPreTags()
		self.updateCurrentTagList()
		self.updateAllTagList()
		self.currList =self["aTaglist"]
		self.onLayoutFinish.append(self.keyBlue)
		
	def loadPreTags(self):
		if pathExists(self.pretagfile):
			fp = open(self.pretagfile,"r")
			t = fp.read()
			fp.close()
			self.pretags = t.replace("\n"," ").strip().split(" ")
			self.pretags.sort()
			print "pretags loaded ", self.pretags
			
	def updateCurrentTagList(self):
		print "updating cTagList"
		self.serviceHandler = eServiceCenter.getInstance()
		self.info = self.serviceHandler.info(self.service)
		self.tags = self.info.getInfoString(self.service, iServiceInformation.sTags).split(' ')
		self.tags.sort()
		self["cTaglist"].l.setList(self.tags)

	def updateAllTagList(self):
		root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD))
		ml = MovieList(root)
		ml.load(root,None)
		xtmp = []
		xtmp.extend(ml.tags)
		self.usedTags = xtmp
		
		e = []+self.pretags
		for i in ml.tags:
			try:
				self.pretags.index(i)
			except ValueError:
				e.append(i)
		
		taglist = []
		for i in e:
				res = [ i ]
				res.append(MultiContentEntryText(pos=(5, 0), size=(500, 25), font=0, text=i))
				if self.isUsedTag(i):
					res.append(MultiContentEntryText(pos=(220, 0),size=(61, 86), font=1,text="X",color=0x00FFFF00))
				if self.isUserTag(i) :
					res.append(MultiContentEntryText(pos=(240, 0),size=(61, 86), font=1,text="X",color=0x00FF0000))#red
				if self.isPreTag(i):
					res.append(MultiContentEntryText(pos=(260, 0),size=(61, 86), font=1,text="X",color=0x000000FF))#blue
				
				taglist.append(res)
			
		taglist.sort()
		self["aTaglist"].l.setList(taglist)		
	
	def addTag(self,tagname):
		try:
			self.tags.index(tagname)
		except ValueError:
			self.tags.append(tagname)
			if len(self.tags) >1:
				self.setTags(" ".join(self.tags))
			else:
				self.setTags(tagname)
		self.updateCurrentTagList()
		self.updateAllTagList()
		

	def removeTag(self,tagname):
		newtags = []
		for i in self.tags:
			if i is not tagname:
				newtags.append(i)
		self.setTags(" ".join(newtags))
		self.updateCurrentTagList()
		self.updateAllTagList()
		
		
	def setTags(self,tagstring,service=False,userNotice=True):
		if service is False:
			serviceRef = self.service
		else:
			serviceRef = service
			
		service_name =serviceRef.toString().split(":")[-1]
		filename = service_name+".meta"
		metadata = self.readMETAData(filename)
		if metadata is not False:
			metadata.append(tagstring.strip())
			return  self.writeMETAData(filename,metadata)
		else:
			if userNotice is True:
				self.session.open(MessageBox,_("cant write movietags, because no meta-file found!"), MessageBox.TYPE_ERROR)
			return  False
		 
	
	def readMETAData(self,filename):
		if pathExists(filename):
			fp = open(filename,"r")
			data = []
			data.append(fp.readline())
			data.append(fp.readline())
			data.append(fp.readline())
			data.append(fp.readline())
			fp.close()
			return data 
		else:
			return False
	def writeMETAData(self,filename,metadata):
		if pathExists(filename):
			fp = open(filename,"w")
			fp.write(metadata[0])
			fp.write(metadata[1])
			fp.write(metadata[2])
			fp.write(metadata[3])
			fp.write(metadata[4])
			fp.close()
			return True
		else:
			return False
	
	def clearAllTags(self,yesno):
		if yesno is True:
			self.serviceHandler = eServiceCenter.getInstance()
			root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD))
			list = self.serviceHandler.list(root)
			tags = set()		
			if list is None:
				pass
			else:
				while 1:
					serviceref = list.getNext()
					if not serviceref.valid():
						break
					if serviceref.flags & eServiceReference.mustDescent:
						continue
					self.setTags("",service=serviceref,userNotice=False)
		self.updateCurrentTagList()
		self.updateAllTagList()
				
	def isUsedTag(self,tag):
		try:
			self.usedTags.index(tag)
			return True
		except ValueError:
			return False
	
	def isPreTag(self,tag):
		try:
			self.pretags.index(tag)
			return True
		except ValueError:
			return False

	def isUserTag(self,tag):
		if self.isPreTag(tag) is False and self.isUsedTag(tag) is True:
			return True
		else:
			return False
	
	def keyRed(self):
		if self.currList is self["cTaglist"]:
			self.removeTag(self["cTaglist"].getCurrent())
			
		elif self.currList is self["aTaglist"]:
			print "adding Tag",self["aTaglist"].getCurrent()[0]
			self.addTag(self["aTaglist"].getCurrent()[0])
			
	def keyGreen(self):
		if self.currList is self["cTaglist"]:
			self.session.openWithCallback(self.newTagEntered,InputBox, title=_("Whitepace will be replaced by Underscore"),windowTitle = _("enter the new Tag"))
		
	def keyYellow(self):
		if  self.currList is self["aTaglist"]:
			self.session.openWithCallback(self.clearAllTags,MessageBox,_("clear all Tags?\n\nThis will delete ALL tags in ALL recodings!\nAre you sure?"), MessageBox.TYPE_YESNO)

	def keyBlue(self):
		if self.currList is self["aTaglist"] or self.currList is None:
			self["aTaglist"].selectionEnabled(0)
			self["cTaglist"].selectionEnabled(1)
			self["buttonred"].setText(_("remove Tag"))
			self["buttongreen"].setText(_("add new Tag"))
			self["buttonyellow"].setText("")        
			self["buttonblue"].setText(_("toggle List"))
			self.currList = self["cTaglist"]
		else:
			self["aTaglist"].selectionEnabled(1)
			self["cTaglist"].selectionEnabled(0)
			self["buttonred"].setText(_("add Tag"))
			self["buttongreen"].setText("")
			self["buttonyellow"].setText("clear all Tags")        
			self["buttonblue"].setText(_("toggle List"))
			self.currList = self["aTaglist"]
			
	def up(self):
		self.currList.up()
	
	def down(self):
		self.currList.down()
	
	def left(self):
		self.currList.pageUp()
	
	def right(self):
		self.currList.pageDown()
	
	def newTagEntered(self,newTag):
		if newTag >=0:
			self.addTag(newTag.strip().replace(" ","_"))

class TagMenuList(MenuList, HTMLComponent, GUIComponent):
    def __init__(self, list):
        MenuList.__init__(self,list)
        GUIComponent.__init__(self)
        self.l = eListboxPythonMultiContent()
        self.list = list
        self.l.setList(list)
        self.l.setFont(0, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 25))
        
    GUI_WIDGET = eListbox

    def postWidgetCreate(self, instance):
        instance.setContent(self.l)
        instance.setItemHeight(25)
		
def main(session, service, **kwargs):
	try:
		session.open(MovieTagger, service)
	except Exception,e:
		print "dont send this chrashlog to DMM, if you see this text in a chrashlog :-)"
		raise e
	
def Plugins(path,**kwargs):
 	return PluginDescriptor(name="Movie Tagger", description=_("Movie Tagger..."), where = PluginDescriptor.WHERE_MOVIELIST, fnc=main)
