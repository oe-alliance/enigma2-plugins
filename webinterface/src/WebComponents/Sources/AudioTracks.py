from __future__ import print_function
from Components.config import config
from Components.Sources.Source import Source
from Components.SystemInfo import SystemInfo
from Tools.ISO639 import LanguageCodes

class AudioTracks(Source):
	GET = 0
	SET = 1
	DOWNMIX = 2

	text = _("False")

	def __init__(self, session, func=GET):
		self.cmd = None
		self.session = session
		self.func = func
		Source.__init__(self)

	def handleCommand(self, cmd):
		self.cmd = cmd

	def getResult(self):
		return self.handleDownmix()

	def setAudioTrack(self):
		if self.cmd is not None:
			service = self.session.nav.getCurrentService()
			audio = service and service.audioTracks()
			try:
				cmd = int(self.cmd)
			except ValueError:
				cmd = -1

			print("COMMAND is %s" % self.cmd)
			if self.session.nav.getCurrentService().audioTracks().getNumberOfTracks() > cmd and cmd >= 0:
				audio.selectTrack(cmd)
				return _("Success")
			else:
				return _("Error")
		else:
			return _("Error")

	def handleDownmix(self):
		if SystemInfo["CanDownmixAC3"]:
			if self.cmd == "True":
				config.av.downmix_ac3.value = True
			elif self.cmd == "False":
				config.av.downmix_ac3.value = False

			text = _("AC3 Downmix enabled") if config.av.downmix_ac3.value else _("AC3 Downmix disabled")
			return config.av.downmix_ac3.value, text

		return False, _("This device does not support AC3 Downmix")

	def getAudioTracks(self):
		service = self.session.nav.getCurrentService()
		audio = service and service.audioTracks()
		n = audio and audio.getNumberOfTracks() or 0

		tracklist = []

		#check for standby
		if audio is not None and service is not None:
			currentTrack = audio.getCurrentTrack()

			if n > 0:
				print("[AudioTracks.py] got %s Audiotracks!" % (n))

				x = 0
				while x < n:
					cnt = 0
					i = audio.getTrackInfo(x)

					languages = i.getLanguage().split('/')
					description = i.getDescription()
					pid = i.getPID()
					language = ''

					for lang in languages:
						if cnt:
							language += ' / '
						if lang in LanguageCodes:
							language += LanguageCodes[lang][0]
						else:
							language += lang
						cnt += 1

					if description:
						description += " (" + language + ")"
					else:
						description = language

					if x == currentTrack:
						active = "True"
					else:
						active = "False"

					tracklist.append((description, x, pid, active))
					x += 1

		return tracklist

	result = property(getResult)
	text = property(setAudioTrack)
	list = property(getAudioTracks)
	lut = {"Description": 0, "Id": 1, "Pid": 2, "Active": 3}
