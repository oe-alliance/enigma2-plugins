from struct import pack
from Components.Sources.Source import Source
from Tools.HardwareInfo import HardwareInfo

class RemoteControl(Source):
	def __init__(self, session):
		self.cmd = None
		self.session = session
		Source.__init__(self)
		self.res = ( False, "Missing or wrong argument" )

	def handleCommand(self, cmd):
		self.cmd = cmd
		self.res = self.sendEvent()

	def sendEvent(self):
		if self.cmd == "" or self.cmd is None:
			print "[RemoteControl.py] cmd is empty or None"
			return self.res

		type = int(self.cmd)
		if type <= 0:
			print "[RemoteControl.py] command <= 0 (%s)" % type
			return ( False, "the command was not > 0" )

		dataon = pack('iiHHi', 0, 0, 1, type, 1)
		dataoff = pack('iiHHi', 0, 0, 1, type, 0)

		# FIXME: input devices are dynamic so we need a better function to find out the correct input devices
		if HardwareInfo.device_name == "dm8000":
			fp = open("/dev/input/event1", 'wb')
		else:
			fp = open("/dev/input/event0", 'wb')
		fp.write(dataon)
		fp.write(dataoff)
		fp.close()

		print "[RemoteControl.py] command was was sent (%s)" % type
		return ( True, "command was was sent" )

	result = property(lambda self: self.res)
