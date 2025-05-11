from __future__ import print_function
from enigma import eActionMap
from Components.Sources.Source import Source
from Components.config import config


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
		self.res = (False, _("Missing or wrong argument"))
		self.eam = eActionMap.getInstance()

		#Advanced remote or standard?

		if config.misc.rcused.value == 0:
			self.remotetype = self.TYPE_ADVANCED
		else:
			self.remotetype = self.TYPE_STANDARD

		print("[RemoteControl.__init__] Configured RCU-Type is '%s'" % (self.remotetype))

	def handleCommand(self, cmd):
		self.cmd = cmd
		self.res = self.sendEvent()

	def sendEvent(self):
		if not self.cmd:
			print("[RemoteControl.sendEvent] cmd is empty or None")
			return self.res

		key = self.cmd.get("command", None)
		if key is None:
			print("[RemoteControl.sendEvent] Obligatory parameter 'command' is missing!")
			return (False, _("Obligatory parameter 'command' is missing!"))

		key = int(key)

		if key <= 0:
			print("[RemoteControl.sendEvent] command <= 0 (%s)" % key)
			return (False, _("the command was not > 0"))

		#type can be "long" or "ascii", everything else will result in FLAG_MAKE
		type = self.cmd.get('type', '')
		flag = self.FLAG_MAKE
		if type == "long":
			#Doesn't work yet (WHY?)
			#TODO Fix long key press
			flag = self.FLAG_LONG
		elif type == "ascii":
			flag = self.FLAG_ASCII

		remotetype = self.cmd.get("rcu", None)

		if remotetype == "standard":
			remotetype = self.TYPE_STANDARD
		elif remotetype == "advanced":
			remotetype = self.TYPE_ADVANCED
		elif remotetype == "keyboard":
			remotetype == self.TYPE_KEYBOARD
		else:
			remotetype = self.remotetype

		#If type=="long" we need to press send FLAG_MAKE first
		if (flag == self.FLAG_LONG):
			self.eam.keyPressed(remotetype, key, self.FLAG_MAKE)

		#press the key with the desired flag
		self.eam.keyPressed(remotetype, key, flag)
		#Release the key
		self.eam.keyPressed(remotetype, key, self.FLAG_BREAK)

		print("[RemoteControl.sendEvent] command was was sent (key: %s, flag: %s)" % (key, flag))
		return (True, _("RC command '%s' has been issued") % str(key))

	result = property(lambda self: self.res)
