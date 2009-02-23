from struct import pack
from Components.Sources.Source import Source

class RemoteControl( Source):
	def __init__(self,session):
		self.cmd = None
		self.session = session
		Source.__init__(self)

	def handleCommand(self, cmd):
		self.cmd = cmd

	def do_func(self):
		list = []

		if self.cmd == "" or self.cmd is None:
			print "[RemoteControl.py] cmd is empty or None"
			return [[False,"Missing or wrong argument"]]

		type = int(self.cmd)
		if type <= 0:
			print "[RemoteControl.py] command <= 0 (%s)" % type
			return [[False,"the command was not greater 0"]]

		dataon = pack('iiHHi',0,0,1,type,1)
		dataoff = pack('iiHHi',0,0,1,type,0)

		fp=open("/dev/input/event1", 'wb')
		fp.write(dataon)
		fp.write(dataoff)
		fp.close()

		print "[RemoteControl.py] command was was sent (%s)" % type
		return [[True, "command was was sent"]]

	list = property(do_func)
	lut = {"Result": 0
			,"ResultText": 1
			}
