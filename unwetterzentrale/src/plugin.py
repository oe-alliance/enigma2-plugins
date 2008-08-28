# -*- coding: utf-8 -*-
#
# Wetter Infos von
# www.unwetterzentrale.de und www.uwz.at
#
# Author: barabas
#

import xml.sax.saxutils as util
import urllib, os, sys, string

from Plugins.Plugin import PluginDescriptor
from twisted.web.client import getPage
from twisted.internet import reactor
from Screens.Screen import Screen
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Sources.List import List
from Components.MenuList import MenuList
from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap, MovingPixmap
from enigma import eTimer, loadPic, getExif
from re import sub, split, search, match, findall


def getAspect():
	val = AVSwitch().getAspectRatioSetting()
	return val/2
	
###############################################################################  

class PictureView(Screen):
		skin = """
			<screen position="0,0" size="720,576" flags="wfNoBorder" title="UWZ" >
				<eLabel position="0,0" zPosition="1" size="720,576" backgroundColor="black" />
				<ePixmap position="635,540" zPosition="2" size="36,20" pixmap="skin_default/buttons/key_info.png" alphatest="on" />
				<widget name="picture" position="80,10" zPosition="2" size="550,550" />
			</screen>"""
			
		def __init__(self, session):
				self.skin = PictureView.skin
				Screen.__init__(self, session)
	
				self.aspect = getAspect()
				self.picfile = "/tmp/uwz.png"	
				
				self["picture"] = Pixmap()
				
				self["actions"] = ActionMap(["OkCancelActions","MovieSelectionActions"],
				{
							"cancel": self.exit,
									"ok": self.exit,
			"showEventInfo": self.HelpView,
				}, -1)

				self.getPicTimer = eTimer()
				self.getPicTimer.callback.append(self.getPic)
				self.getPicTimer.start(300, True)
				
		def getPic(self):
				self.currPic = loadPic(self.picfile, 550, 550, self.aspect, 0, 0, 1)
				self.showPic()
				
		def showPic(self):
				if self.currPic != None:
					self["picture"].instance.setPixmap(self.currPic)

		def HelpView(self):
				self.session.openWithCallback(self.getPic ,HelpPictureView)
	
		def exit(self):
				self.close()
				 

class HelpPictureView(Screen):
		skin = """
			<screen position="25,200" size="670,290" title="Warnstufen" >
				<eLabel position="0,0" zPosition="1" size="670,290" backgroundColor="black" />
				<ePixmap position="320,260" zPosition="2" size="36,20" pixmap="skin_default/arrowdown.png" alphatest="on" />
				<widget name="picture" position="-10,20" zPosition="2" size="690,225" />
			</screen>"""
				
		def __init__(self, session):
				self.skin = HelpPictureView.skin
				Screen.__init__(self, session)
				
				self["picture"] = Pixmap()
				
				self["actions"] = ActionMap(["OkCancelActions", "DirectionActions"],
				{
					"cancel": self.exit,
							"ok": self.exit,
						"left": self.prevPic,
					"right": self.nextPic
				}, -1)
				
				self.aspect = getAspect()
				self.list = []
				self.list.append(pluginpath + "/W_gruen.gif")
				self.list.append(pluginpath + "/W_gelb.gif")
				self.list.append(pluginpath + "/W_orange.gif")
				self.list.append(pluginpath + "/W_rot.gif")
				self.list.append(pluginpath + "/W_violett.gif")
				self.index = 0
					
				self.onShown.append(self.getPic)
				
		def getPic(self):
				self.currPic = loadPic(self.list[self.index], 690, 225, self.aspect, 0, 0, 1)
				self.showPic()
				
		def showPic(self):
				if self.currPic != None:
					self["picture"].instance.setPixmap(self.currPic)
	
		def nextPic(self):
				self.index += 1
				if self.index > 4:
					self.index = 0
				self.getPic()
		
		def prevPic(self):
				self.index -= 1
				if self.index < 0:
					self.index = 4
				self.getPic()
				
		def exit(self):
				self.close()
								
class UnwetterMain(Screen):

		skin = """
				<screen position="110,83" size="530,430" title="Unwetterzentrale" >
						<widget name="hmenu" position="5,0" zPosition="1" size="530,220" scrollbarMode="showOnDemand" />
						<widget name="thumbnail" position="185,250" zPosition="2" size="140,150" />
						<widget name="thumbland" position="435,390" zPosition="2" size="90,40"  />
						<ePixmap position="20,380" zPosition="2" size="36,20" pixmap="skin_default/buttons/key_menu.png" alphatest="on" />
						<widget name="statuslabel" position="5,410" zPosition="2" size="530,20" font="Regular;16" halign=\"left\"/>
				</screen>"""

		def __init__(self, session):
				self.loadinginprogress = False  
				self.skin = UnwetterMain.skin
				self.session = session
				Screen.__init__(self, session)       
				
				self["statuslabel"] = Label()
				self["thumbland"] = Pixmap()
				self["thumbnail"] = Pixmap()
				self["hmenu"] = MenuList([])		
				self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "MovieSelectionActions"],
				{
					"ok":	self.ok,
					"up": self.up,
					"right": self.rightDown,
					"left": self.leftUp,
					"down": self.down,
					"cancel": self.exit,
					"contextMenu": self.switchDeA,
				}, -1)
				
				self.aspect = getAspect()			
				self.menueintrag = []
				self.link = []
				self.picfile = "/tmp/uwz.png"	
				self.picweatherfile = pluginpath + "/wetterreport.jpg"
				self.reportfile = "/tmp/uwz.report"
				
				try:
						f = open(pluginpath + "/last.cfg","r")
						self.land = f.read()
						f.close
				except:
						self.land = "de"
				
				if self.land == "de":				
						self.baseurl = "http://www.unwetterzentrale.de/uwz/"
						self.menuurl = self.baseurl + "index.html"
						self.weatherreporturl = self.baseurl + "lagebericht.html"
				else:
						self.baseurl = "http://www.uwz.at/"
						self.menuurl = self.baseurl + "index.php"
						self.weatherreporturl = self.baseurl + "lagebericht.php"
										
				self.downloadMenu()

#				self.onLayoutFinish.append(self.go)	

				self.ThumbTimer = eTimer()
				self.ThumbTimer.callback.append(self.showThumb)
				self.ThumbTimer.start(1000, True)			
						
		def hauptmenu(self,output):			
				self.loadinginprogress = False
				trans = { '&szlig;' : 'ß' , '&auml;' : 'ä' , '&ouml;' : 'ö' , '&uuml;' : 'ü' , '&Auml;' : 'Ä', '&Ouml;' : 'Ö' , '&Uuml;' : 'Ü'}
				output= util.unescape(output,trans)
			
				if self.land == "de":
						startpos = string.find(output,"<!-- Anfang Navigation -->")
						endpos = string.find(output,"<!-- Ende Navigation -->")
						bereich = output[startpos:endpos]							
						a = findall(r'href=(?P<text>.*?)</a>',bereich)						
						for x in a[1:16]:
							x = x.replace('">',"#").replace('"',"")
							name = x.split("#")[1]
							link = self.baseurl + x.split("#")[0]
							self.menueintrag.append(name)
							self.link.append(link)		
				else:
						startpos = string.find(output,'<div id="mainWindow">')
						endpos = string.find(output,'<a class="menua" href="http://www.austrowetter.at"')
						bereich = output[startpos:endpos]				
						a = findall(r'<a class="menub" href=(?P<text>.*?)</a>',bereich)
						for x in a[1:13]:
							x = x.replace('">',"#").replace('"',"").replace(' style=font-weight:;',"")
							if x != '#&nbsp;':
									name = x.split("#")[1]
									link = self.baseurl + x.split("#")[0]
									self.menueintrag.append(name)
									self.link.append(link)				

				self["statuslabel"].setText("")			
				self["hmenu"].l.setList(self.menueintrag)
				self["hmenu"].instance.moveSelectionTo(0)
				self.showThumbLand()
								
		def ok(self):
				self.go()
				c = self["hmenu"].getCurrent()
				if c is not None:
					x = self.menueintrag.index(c)
					if x != 0:
						self.session.open(PictureView)		
					else:
						self.downloadWeatherReport()
								
		def go(self):
				c = self["hmenu"].getCurrent()
				if c is not None:
					x = self.menueintrag.index(c)
					# Wetterlagebericht ist Index 0
					if x != 0:
						url = self.link[x]
						self["statuslabel"].setText("Loading Data")
						self.downloadPicUrl(url)
					self.ThumbTimer.start(1500, True)
						
		def up(self):
				self["hmenu"].up()
				self.go()
								
		def down(self):
				self["hmenu"].down()
				self.go()				

		def leftUp(self):
				self["hmenu"].pageUp()
				self.go()
		
		def rightDown(self):
				self["hmenu"].pageDown()
				self.go()

		def showThumbLand(self):
				picture = ""
				if self.land == "de":
						picture = pluginpath + "/uwz.png"
				else:
						picture = pluginpath + "/uwzat.png"						
				ptr = loadPic(picture, 90, 40, self.aspect, 0, 0, 1)
				if ptr != None:
						self["thumbland"].instance.setPixmap(ptr)
						
		def showThumb(self):
				picture = ""
				if self.land == "de":
						width = 142 ; height = 150
				else:
						width = 142 ;	height = 135
				c = self["hmenu"].getCurrent()
				if c is not None:
					x = self.menueintrag.index(c)
					if x != 0:
						picture = self.picfile
					else:
						picture = self.picweatherfile	
						height = 150				
				ptr = loadPic(picture, width, height, self.aspect, 0, 0, 1)
				if ptr != None:
					self["statuslabel"].setText("")
					self["thumbnail"].show()
					self["thumbnail"].instance.setPixmap(ptr)
				else:
					self["thumbnail"].hide()
			
		def getPicUrl(self,output):
				self.loadinginprogress = False
				if self.land == "de":	
						startpos = string.find(output,"<!-- Anfang msg_Box Content -->")
						endpos = string.find(output,"<!-- Ende msg_Box Content -->")
						bereich = output[startpos:endpos]
						picurl = search(r'<img src="(?P<text>.*?)" width=',bereich)
						picurl = self.baseurl + picurl.group(1)
				else:
						picurl = search(r'<img src="showMap(?P<text>.*?)" alt=',output)
						picurl = self.baseurl + "showMap" + picurl.group(1).replace('&amp;','&')
				self.downloadPic(picurl)

		def getPic(self,output):
				self.loadinginprogress = False
				f = open(self.picfile, "wb")
				f.write(output)
				f.close			
	
		def getWeatherReport(self,output):
				self.loadinginprogress = False		
				if self.land == "de":
						trans = { '&szlig;' : 'ß' , '&auml;' : 'ä' , '&ouml;' : 'ö' , '&uuml;' : 'ü' , '&Auml;' : 'Ä', '&Ouml;' : 'Ö' , '&Uuml;' : 'Ü'}
						output= util.unescape(output,trans)
						startpos = string.find(output,'<!-- Anfang msg_Box Content -->')
						endpos = string.find(output,"<!-- Ende msg_Box Content -->")
						bereich = output[startpos:endpos]
				else:
						startpos = string.find(output,'<div class="content">')
						endpos = string.find(output,'<div class="rs_title">Unwettermeldungen</div>')
						bereich = output[startpos:endpos]
						u_bereich = bereich.decode("iso-8859-1")
						bereich = u_bereich.encode("utf-8")
						bereich = sub('<br />',"\n",bereich)

				bereich = sub('<[^>]*>',"",bereich)				
				bereich = sub('Fronten- und Isobarenkarte.*',"",bereich)
				bereich = bereich.strip()
				bereich = sub("\n\s*\n*", "\n\n", bereich)

				f = open(self.reportfile, "w")
				f.write("%s" % bereich)
				f.close
				self.session.open(Console,_("Warnlagebericht"),["cat %s" % self.reportfile])		
																			
		def downloadError(self,output):
				self.loadinginprogress = False
				self["statuslabel"].setText("Fehler beim Download")
		
		def downloadMenu(self):
				self.loadinginprogress = True
				getPage(self.menuurl).addCallback(self.hauptmenu).addErrback(self.downloadError)		

		def downloadPicUrl(self,url):
				self.loadinginprogress = True
				getPage(url).addCallback(self.getPicUrl).addErrback(self.downloadError)		

		def downloadPic(self,picurl):
				self.loadinginprogress = True
#				self["statuslabel"].setText("Lade Bild: %s" % picurl)
				getPage(picurl).addCallback(self.getPic).addErrback(self.downloadError)
		
		def downloadWeatherReport(self):
				self.loadinginprogress = True
#				self["statuslabel"].setText("Lade Report: %s" % self.weatherreporturl)
				getPage(self.weatherreporturl).addCallback(self.getWeatherReport).addErrback(self.downloadError)
		
		def switchDeA(self):								
				self.menueintrag = []
				self.link = []
				if self.land == "de":
						self.land = "a"
						self.baseurl = "http://www.uwz.at/"
						self.menuurl = self.baseurl + "index.php"
						self.weatherreporturl = self.baseurl + "lagebericht.php"
				else:
						self.land = "de"
						self.baseurl = "http://www.unwetterzentrale.de/uwz/"
						self.menuurl = self.baseurl + "index.html"
						self.weatherreporturl = self.baseurl + "lagebericht.html"
				
				f = open(pluginpath + "/last.cfg","w")
				f.write(self.land)
				f.close
				self.downloadMenu()
				self.ThumbTimer.start(1500, True)	
				
		def exit(self):
				if self.loadinginprogress:
					reactor.callLater(1,self.exit)
				else:
					os.system("rm %s %s" % (self.picfile, self.reportfile))
					self.close()


#############################						
											        
def main(session, **kwargs):
			session.open(UnwetterMain)
								
def Plugins(path,**kwargs):
			global pluginpath
			pluginpath = path
 			return PluginDescriptor(
					name="Unwetterzentrale", 
					description="www.unwetterzentrale.de und www.uwz.at", 
					icon="uwz.png",
					where = PluginDescriptor.WHERE_PLUGINMENU,
					fnc=main)
