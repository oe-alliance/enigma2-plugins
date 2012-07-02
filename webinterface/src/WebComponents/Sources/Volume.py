from enigma import eDVBVolumecontrol #this is not nice
from Components.Sources.Source import Source
from GlobalActions import globalActionMap
from Components.VolumeControl import VolumeControl

class Volume(Source):
	def __init__(self, session):
		Source.__init__(self)
		global globalActionMap # hackalert :)
		self.actionmap = globalActionMap
		self.volctrl = eDVBVolumecontrol.getInstance() # this is not nice
		self.vol = ( True, "State", self.volctrl.getVolume(), self.volctrl.isMuted() )

	def handleCommand(self, cmd):
		l = []
		if cmd == "state":
			l.extend((True, "State"))
		elif cmd == "up":
			self.actionmap.actions["volumeUp"]()
			l.extend((True, "Volume changed"))
		elif cmd == "down":
			self.actionmap.actions["volumeDown"]()
			l.extend((True, "Volume changed"))
		elif cmd == "mute":
			self.actionmap.actions["volumeMute"]()
			l.extend((True, "Mute toggled"))
		elif cmd.startswith("set"):
			try:
				targetvol = int(cmd[3:])
				if targetvol > 100:
					targetvol = 100
				if targetvol < 0:
					targetvol = 0

				self.volctrl.setVolume(targetvol, targetvol)

				l.extend((True, "Volume set to %i" % targetvol))
			except ValueError: # if cmd was set12NotInt
				l.extend((False, "Wrong parameter format 'set=%s'. Use set=set15 " % cmd))
		else:
			l.extend((False, "Unknown Volume command %s" % cmd))

		l.extend((self.volctrl.getVolume(), self.volctrl.isMuted()))

		self.vol = l

	volume = property(lambda self: self.vol)

