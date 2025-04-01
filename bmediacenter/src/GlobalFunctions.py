from re import sub
from Tools.Directories import fileExists
from _ctypes import dlopen, dlsym, call_function


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
		except Exception as e:
			pass

	def showStillpicture(self, pic):
		try:
			call_function(self.showSinglePic, (pic, ))
		except:
			pass

	def finishStillPicture(self):
		try:
			call_function(self.finishShowSinglePic, ())
		except:
			pass


def shortname(movie, showing=None):
	movielist = movie.split('/')
	for n in movielist:
		if n != "":
			movie = n
	movie = movie.upper()
	movieback = movie
	movie = sub(r"\W720P(.*[^.]+).", "", movie)
	movie = sub(r"\W1080I(.*[^.]+).", "", movie)
	movie = sub(r"\W1080P(.*[^.]+).", "", movie)
	movie = sub(r"\W[(].*?[)](.*[^.]+).", "", movie)
	movie = sub(r"\W[[].*?[]](.*[^.]+).", "", movie)
	movie = sub(r"\W[0-9]{4}", "", movie)
	if not showing:
		movie = sub(r"\WDVDRIP(.*[^.]+).", "", movie)
		movie = sub(r"\WAC3D(.*[^.]+).", "", movie)
		movie = sub(r"\WAC3(.*[^.]+).", "", movie)
		movie = sub(r"\WX264(.*[^.]+).", "", movie)
		movie = sub(r"\WXVID(.*[^.]+).", "", movie)
		movie = sub(r"\WBLURAY(.*[^.]+).", "", movie)
		movie = sub(r"\WGERMAN(.*[^.]+).", "", movie)
		movie = sub(r"\WCD[0-9]{2}", "", movie)
		movie = sub(r"\WCD[0-9]", "", movie)
		movie = sub(r"\WDVD[0-9]{2}", "", movie)
		movie = sub(r"\WDVD[0-9]", "", movie)
		movie = sub(r"\WDISC[0-9]{2}", "", movie)
		movie = sub(r"\WDISC[0-9]", "", movie)
		movie = sub(r"\W[0-9]{2}DISC", "", movie)
		movie = sub(r"\W[0-9]DISC", "", movie)
#		movie = sub("\WS[0-9]{2}","",movie)
#		movie = sub("\WE[0-9]{2}","",movie)
		movie = sub(r"\WSEASON[0-9]{2}", "", movie)
		movie = sub(r"\WSEASON[0-9]", "", movie)

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
