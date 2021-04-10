from Components.VariableText import VariableText
from enigma import eLabel, eDVBVolumecontrol, eTimer
from Renderer import Renderer


class vhdRendVolumeText(Renderer, VariableText):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
		self.vol_timer = eTimer()
		self.vol_timer.callback.append(self.pollme)
	GUI_WIDGET = eLabel

	def changed(self, what):
		if not self.suspended:
			self.text = str(eDVBVolumecontrol.getInstance().getVolume())

	def pollme(self):
		self.changed(None)

	def onShow(self):
		self.suspended = False
		self.vol_timer.start(200)

	def onHide(self):
		self.suspended = True
		self.vol_timer.stop()
