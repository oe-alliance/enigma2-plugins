from Components.VariableText import VariableText
from Components.config import config
from enigma import eLabel
from Renderer import Renderer
from os import path, statvfs


class vhdRendMovieDirSize(Renderer, VariableText):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
	GUI_WIDGET = eLabel

	def changed(self, what):
		if not self.suspended:
			try:
				if path.exists(config.movielist.last_videodir.value):
					stat = statvfs(config.movielist.last_videodir.value)
					free = (stat.f_bavail if stat.f_bavail != 0 else stat.f_bfree) * stat.f_bsize / 1048576
					if free >= 10240:
						fdspace = "%d GB on " % (free / 1024)
						self.text = fdspace + _(config.movielist.last_videodir.value)
					else:
						fdspace = "%d MB on " % (free)
						self.text = fdspace + _(config.movielist.last_videodir.value)
				else:
					self.text = '---'
			except:
				self.text = 'ERR'


