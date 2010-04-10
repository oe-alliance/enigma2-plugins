from Components.VariableText import VariableText
from enigma import eLabel, eDVBVolumecontrol
from Renderer import Renderer


class vRendVolumeText(Renderer, VariableText):
	def __init__(self):
		Renderer.__init__(self)
		VariableText.__init__(self)
	GUI_WIDGET = eLabel

	def changed(self, what):
		self.text = str(eDVBVolumecontrol.getInstance().getVolume())

