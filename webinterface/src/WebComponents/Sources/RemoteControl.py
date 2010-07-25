from enigma import eActionMap
#from struct import pack
from Components.Sources.Source import Source
from Tools.HardwareInfo import HardwareInfo

class RemoteControl(Source):
	# Flags
	FLAG_MAKE = 0
	FLAG_BREAK = 1
	FLAG_REPEAT = 2
	FLAG_LONG = 3
	FLAG_ASCII = 4
	
	#Device Types
	TYPE_STANDARD = "dreambox remote control (native)"
	TYPE_ADVANCED = "dreambox advanced remote control (native)"
	TYPE_KEYBOARD = "dreambox ir keyboard"
		
	def __init__(self, session):
		self.cmd = None
		self.session = session
		Source.__init__(self)
		self.res = ( False, "Missing or wrong argument" )
		self.eam = eActionMap.getInstance()

	def handleCommand(self, cmd):
		self.cmd = cmd
		self.res = self.sendEvent()

	def sendEvent(self):
		if len(self.cmd) == 0 or self.cmd is None:
			print "[RemoteControl.py] cmd is empty or None"
			return self.res
		
		if not "command" in self.cmd:
			print "[RemoteControl.py] Obligatory parameter 'command' is missing!"
			return ( False, "Obligatory parameter 'command' is missing!" )
		
		key = int(self.cmd["command"])			
		
		if key <= 0:			
			print "[RemoteControl.py] command <= 0 (%s)" % key
			return ( False, "the command was not > 0" )
		
		#type can be "long" or "ascii", everything else will result in FLAG_MAKE
		type = None 
		if "type" in self.cmd:
			if self.cmd["type"] != "" and self.cmd["type"] != None:
				type = self.cmd["type"];
		
		#if type is set, set the flag accordingly
		flag = self.FLAG_MAKE
		if type != None:
			if type == "long":
				#Doesn't work yet (WHY?)
				#TODO Fix long key press
				flag = self.FLAG_LONG
			elif type == "ascii":
				flag = self.FLAG_ASCII
				
		self.eam.keyPressed(self.TYPE_ADVANCED, key, flag)		
		
		print "[RemoteControl.py] command was was sent (%s)" % key
		return ( True, "RC command '" + str(key) + "' has been issued" ) 

	result = property(lambda self: self.res)
