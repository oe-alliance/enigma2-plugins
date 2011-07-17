from enigma import eDVBVolumecontrol #this is not nice
from Components.Sources.Source import Source
from GlobalActions import globalActionMap
from Components.VolumeControl import VolumeControl

class Volume(Source):
	def __init__(self, session, command_default="state"):
		self.cmd = command_default
		Source.__init__(self)
		global globalActionMap # hackalert :)
		self.actionmap = globalActionMap
		self.volctrl = eDVBVolumecontrol.getInstance() # this is not nice
		self.vol = ( True, "State", self.volctrl.getVolume(), self.volctrl.isMuted() )

	def handleCommand(self, cmd):
		self.cmd = cmd
		self.vol = self.handleVolume()

	def handleVolume(self):
		list = []
		if self.cmd == "state":
			list.extend((True, "State"))
		elif self.cmd == "up":
			self.actionmap.actions["volumeUp"]()
			list.extend((True, "Volume changed"))
		elif self.cmd == "down":
			self.actionmap.actions["volumeDown"]()
			list.extend((True, "Volume changed"))
		elif self.cmd == "mute":
			self.actionmap.actions["volumeMute"]()
			list.extend((True, "Mute toggled"))
		elif self.cmd.startswith("set"):
			try:
				targetvol = int(self.cmd[3:])
				if targetvol > 100:
					targetvol = 100
				if targetvol < 0:
					targetvol = 0

				self.volctrl.setVolume(targetvol, targetvol)

				list.extend((True, "Volume set to %i" % targetvol))
			except ValueError: # if cmd was set12NotInt
				list.extend((False, "Wrong parameter format 'set=%s'. Use set=set15 " % self.cmd))
		else:
			list.extend((False, "Unknown Volume command %s" % self.cmd))

		list.extend((self.volctrl.getVolume(), self.volctrl.isMuted()))

		return list

	volume = property(lambda self: self.vol)

