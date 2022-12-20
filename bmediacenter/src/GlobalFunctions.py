from re import sub
from enigma import iServiceInformation, getDesktop
from Components.ActionMap import ActionMap
from Screens.Screen import Screen
from Screens.ServiceInfo import ServiceInfoList, ServiceInfoListEntry
from Tools.Directories import fileExists
from _ctypes import dlopen, dlsym, call_function


class MC_VideoInfoView(Screen):
	if getDesktop(0).size().width() == 1920:
		skin = """
			<screen position="80,130" size="840,480" title="View Video Info" >
				<widget name="infolist" position="5,5" size="810,460" selectionDisabled="1" />
			</screen>"""
	else:
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
		tlist = []
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
		lib = "/usr/lib/"
		if fileExists(lib + "libshowiframe.so.0.0.0"):
			self.showiframe = dlopen(lib + "libshowiframe.so.0.0.0")
		try:
			self.showSinglePic = dlsym(self.showiframe, "showSinglePic")
			self.finishShowSinglePic = dlsym(self.showiframe, "finishShowSinglePic")
		except OSError as e:
			self.showSinglePic = dlsym(self.showiframe, "_Z13showSinglePicPKc")
			self.finishShowSinglePic = dlsym(self.showiframe, "_Z19finishShowSinglePicv")

	def showStillpicture(self, pic):
		call_function(self.showSinglePic, (pic, ))

	def finishStillPicture(self):
		call_function(self.finishShowSinglePic, ())


def shortname(movie, showing=None):
	movielist = movie.split('/')
	for n in movielist:
		if n != "":
			movie = n
	movie = movie.upper()
	movieback = movie
	movie = sub("\W720P(.*[^.]+).", "", movie)
	movie = sub("\W1080I(.*[^.]+).", "", movie)
	movie = sub("\W1080P(.*[^.]+).", "", movie)
	movie = sub("\W[(].*?[)](.*[^.]+).", "", movie)
	movie = sub("\W[[].*?[]](.*[^.]+).", "", movie)
	movie = sub("\W[0-9]{4}", "", movie)
	if not showing:
		movie = sub("\WDVDRIP(.*[^.]+).", "", movie)
		movie = sub("\WAC3D(.*[^.]+).", "", movie)
		movie = sub("\WAC3(.*[^.]+).", "", movie)
		movie = sub("\WX264(.*[^.]+).", "", movie)
		movie = sub("\WXVID(.*[^.]+).", "", movie)
		movie = sub("\WBLURAY(.*[^.]+).", "", movie)
		movie = sub("\WGERMAN(.*[^.]+).", "", movie)
		movie = sub("\WCD[0-9]{2}", "", movie)
		movie = sub("\WCD[0-9]", "", movie)
		movie = sub("\WDVD[0-9]{2}", "", movie)
		movie = sub("\WDVD[0-9]", "", movie)
		movie = sub("\WDISC[0-9]{2}", "", movie)
		movie = sub("\WDISC[0-9]", "", movie)
		movie = sub("\W[0-9]{2}DISC", "", movie)
		movie = sub("\W[0-9]DISC", "", movie)
#		movie = sub("\WS[0-9]{2}","",movie)
#		movie = sub("\WE[0-9]{2}","",movie)
		movie = sub("\WSEASON[0-9]{2}", "", movie)
		movie = sub("\WSEASON[0-9]", "", movie)

	movie = sub("[0-9]{8} ", "", movie)
	movie = sub(" -", "-", movie)
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
