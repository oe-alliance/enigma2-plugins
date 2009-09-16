from Components.Sources.Source import Source
from Screens.MessageBox import MessageBox
from os import system, path

class Message(Source):
	PRINT = 0
	ANSWER = 1
	yesnoFile = "/tmp/yesno"

	def __init__(self, session, func=PRINT):
		self.cmd = []
		self.session = session

		self.func = func
		Source.__init__(self)
		error = "unknown command (%s)" % func
		self.res = (False, error)

	def handleCommand(self, cmd):
		self.cmd = cmd
		if self.func is self.PRINT:
			self.res = self.printMessage(cmd)
		elif self.func is self.ANSWER:
			self.res = self.getYesNoAnswer(cmd)

	def printMessage(self, param):
		print "printMessage"

		if self.cmd['text'] == "" or self.cmd['text'] is None:
			return ( False, "No Messagetext given" )
		else:
			mtext = self.cmd['text']

		try:
			typeint = int(self.cmd['type'])
		except (ValueError, TypeError), e:
			return ( False, "type %s is not a number" % self.cmd['type'] )

		if typeint == MessageBox.TYPE_YESNO:
			#dont know how to give the result to the webif back
			mtype = MessageBox.TYPE_YESNO
		elif typeint == MessageBox.TYPE_INFO:
			mtype = MessageBox.TYPE_INFO
		elif typeint == MessageBox.TYPE_WARNING:
			mtype = MessageBox.TYPE_WARNING
		elif typeint == MessageBox.TYPE_ERROR:
			mtype = MessageBox.TYPE_ERROR
		else:
			return ( False, "Unsupported Messagetype %s" % self.cmd['type'] )

		try:
			mtimeout = int(self.cmd['timeout'])
		except (ValueError, TypeError), e:
			mtimeout = -1

		if typeint == MessageBox.TYPE_YESNO:
			self.session.openWithCallback(self.yesNoAnswer, MessageBox, mtext, type=mtype, timeout=mtimeout)
		else:
			self.session.open(MessageBox, mtext, type=mtype , timeout=mtimeout)

		return ( True, "Message sent successfully!" )

	def yesNoAnswer(self, confirmed):
		print "yesNoAnswer", confirmed
		#self.session.messageboxanswer = confirmed

		yesnoFile = self.yesnoFile

		cmdstr = "/bin/echo -n yes > %s" % yesnoFile
		if not confirmed:
			cmdstr = "/bin/echo -n no > %s" % yesnoFile

		system(cmdstr)

	def getYesNoAnswer(self, param):
		print "getYesNoAnswer"#,self.session.messageboxanswer
		yesnoFile = self.yesnoFile
		if path.exists(yesnoFile) == True:
			file = open(yesnoFile, "r")
			lines = file.readlines()
			file.close()
			cmdstr = "rm %s" % yesnoFile
			system(cmdstr)
			print "Answer: (%s)" % lines[0]
			if lines[0] == "yes":
				return ( True, "Answer is YES!" )
			else:
				return ( True, "Answer is NO!" )
		else:
			return ( False, "No answer in time" )

	result = property(lambda self: self.res)
