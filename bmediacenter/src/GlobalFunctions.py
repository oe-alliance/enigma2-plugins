from enigma import eRect, eServiceReference, iServiceInformation, iPlayableService
from Screens.Screen import Screen
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from Components.ActionMap import ActionMap, NumberActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Tools.Directories import resolveFilename, pathExists, fileExists, SCOPE_MEDIA
from Components.Sources.List import List
from Components.ServicePosition import ServicePositionGauge
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import *
from Components.FileList import FileList
from _ctypes import *
import os
import re
from os import path as os_path
#------------------------------------------------------------------------------------------
class MC_VideoInfoView(Screen):
	skin = """
		<screen position="80,130" size="560,320" title="View Video Info" >
			<widget name="infolist" position="5,5" size="550,310" selectionDisabled="1" />
		</screen>"""
	def __init__(self, session, fullname, name, ref):
		self.skin = MC_VideoInfoView.skin
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"cancel": self.close,
			"ok": self.close
		}, -1)
		tlist = [ ]
		self["infolist"] = ServiceInfoList(tlist)
		currPlay = self.session.nav.getCurrentService()
		if currPlay is not None:
			stitle = currPlay.info().getInfoString(iServiceInformation.sTitle)
			if stitle == "":
				stitle = currPlay.info().getName().split('/')[-1]
			tlist.append(ServiceInfoListEntry("Title: ", stitle))
			tlist.append(ServiceInfoListEntry("sNamespace: ", currPlay.info().getInfoString(iServiceInformation.sNamespace)))
			tlist.append(ServiceInfoListEntry("sProvider: ", currPlay.info().getInfoString(iServiceInformation.sProvider)))
			tlist.append(ServiceInfoListEntry("sTimeCreate: ", currPlay.info().getInfoString(iServiceInformation.sTimeCreate)))
			tlist.append(ServiceInfoListEntry("sVideoWidth: ", currPlay.info().getInfoString(iServiceInformation.sVideoWidth)))
			tlist.append(ServiceInfoListEntry("sVideoHeight: ", currPlay.info().getInfoString(iServiceInformation.sVideoHeight)))
			tlist.append(ServiceInfoListEntry("sDescription: ", currPlay.info().getInfoString(iServiceInformation.sDescription)))
class Showiframe():
	def __init__(self):
		lib="/usr/lib/"
		if fileExists(lib +"libshowiframe.so.0.0.0"):
			self.showiframe = dlopen(lib +"libshowiframe.so.0.0.0")
		try:
			self.showSinglePic = dlsym(self.showiframe, "showSinglePic")
			self.finishShowSinglePic = dlsym(self.showiframe, "finishShowSinglePic")
		except OSError, e: 
			self.showSinglePic = dlsym(self.showiframe, "_Z13showSinglePicPKc")
			self.finishShowSinglePic = dlsym(self.showiframe, "_Z19finishShowSinglePicv")
	def showStillpicture(self, pic):
		call_function(self.showSinglePic, (pic, ))
	def finishStillPicture(self):
		call_function(self.finishShowSinglePic, ())
def shortname(movie,showing = None):
	movielist = movie.split('/')
	for n in movielist:
		if n is not "":		
			movie = n
	movie = movie.upper()
	movieback = movie
	movie = re.sub("\W720P(.*[^.]+).","",movie)
	movie = re.sub("\W1080I(.*[^.]+).","",movie)
	movie = re.sub("\W1080P(.*[^.]+).","",movie)
	movie = re.sub("\W[(].*?[)](.*[^.]+).","",movie)
	movie = re.sub("\W[[].*?[]](.*[^.]+).","",movie)
	movie = re.sub("\W[0-9]{4}","",movie)
	if not showing:
		movie = re.sub("\WDVDRIP(.*[^.]+).","",movie)
		movie = re.sub("\WAC3D(.*[^.]+).","",movie)	
		movie = re.sub("\WAC3(.*[^.]+).","",movie)
		movie = re.sub("\WX264(.*[^.]+).","",movie)
		movie = re.sub("\WXVID(.*[^.]+).","",movie)
		movie = re.sub("\WBLURAY(.*[^.]+).","",movie)
		movie = re.sub("\WGERMAN(.*[^.]+).","",movie)
		movie = re.sub("\WCD[0-9]{2}","",movie)
		movie = re.sub("\WCD[0-9]","",movie)
		movie = re.sub("\WDVD[0-9]{2}","",movie)
		movie = re.sub("\WDVD[0-9]","",movie)
		movie = re.sub("\WDISC[0-9]{2}","",movie)
		movie = re.sub("\WDISC[0-9]","",movie)
		movie = re.sub("\W[0-9]{2}DISC","",movie)
		movie = re.sub("\W[0-9]DISC","",movie)
#		movie = re.sub("\WS[0-9]{2}","",movie)
#		movie = re.sub("\WE[0-9]{2}","",movie)
		movie = re.sub("\WSEASON[0-9]{2}","",movie)
		movie = re.sub("\WSEASON[0-9]","",movie)

	movie = re.sub("[0-9]{8} ","",movie)
	movie = re.sub(" -","-",movie)
	if len(movie) != 0:
		if movie[0] == '-':
			moviesplit = movie.split('-')[2:]
			movie = "".join(moviesplit)
			movie = movie[1:]
	replace_list = "rar iso img avi mkv mp4 mpg mpeg mts ogm m2ts pls trp ts vdr vob wmv AC3 AC3D BDRIP BLURAY CAM CAMRIP COMPLETE CUSTOM CUT DC Directors DL DOKU DTS DVDR DVDRIP DVDSCR DVDSCREENER EXTENDED FRENCH FiNNiSH GERMAN HD HDDVD HDDVDRip HDTV INT INTERNAL Int LD LiMiTED MULTi MULTiSUBS NORDIC NTSC PAL PL R1 R5 RECUT REMASTERED REPACK RIP SCREENER SE SEE special.edition SSE STV SUBBED SWEDISH Staffel TC TELECINE TELESYNC TS UNCUT UNRATED WS XXX iTALiAN mvcd rsvcd svcd x264"
	replacelist = replace_list.upper()
	replacelist = replacelist.split(' ')
	for n in replacelist:
		movie = movie.replace(" ", ".")
		movie = movie.replace(" " + n + " ", ".")
		movie = movie.replace("." + n + ".", ".")
		movie = movie.replace("." + n + "-", ".")
		movie = movie.replace("." + n + "_", ".")
		movie = movie.replace("-" + n + ".", ".")
		movie = movie.replace("-" + n + "-", ".")
		movie = movie.replace("-" + n + "_", ".")
		movie = movie.replace("_" + n + ".", ".")
		movie = movie.replace("_" + n + "-", ".")
		movie = movie.replace("_" + n + "_", ".")
	movie = movie.replace("..", ".")
	movie = movie.replace("..", ".")
	movie = movie.replace("..", ".")
	movie = movie.replace("..", ".")

	for n in replacelist:
		if movie.upper().endswith("." + n):
			if movie.__contains__("."):
				while not movie.endswith("."):
					movie = movie[:-1]
				movie = movie[:-1]
	movie = movie.replace(".", " ")
	movie = movie.replace("-", " ")
	movie = movie.replace("_", " ")
	movie = movie.replace(":", " ")

	if len(movie) == 0:
		movie = movieback
	return movie
