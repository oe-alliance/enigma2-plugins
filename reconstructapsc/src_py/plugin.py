from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
import Screens.Standby
from Components.ActionMap import ActionMap
from enigma import eTimer, eServiceCenter, iServiceInformation, eConsoleAppContainer, eEnv
from os import access, chmod, X_OK

recons_path = eEnv.resolve("${libdir}/enigma2/python/Plugins/Extensions/ReconstructApSc/bin/reconstruct_apsc")

def main(session, service, **kwargs):
	# Hack to make sure it is executable
	if not access(recons_path, X_OK):
		chmod(recons_path, 493)
	session.open(ReconstructApSc, service, **kwargs)

def Plugins(**kwargs):
	return PluginDescriptor(name="ReconstructApSc", description=_("Reconstruct AP/SC ..."), where = PluginDescriptor.WHERE_MOVIELIST, fnc=main)


class ReconstructApSc(ChoiceBox):
	def __init__(self, session, service):
		self.service = service
		serviceHandler = eServiceCenter.getInstance()
		path = self.service.getPath()
		info = serviceHandler.info(self.service)
		if not info:
			self.name = path
		else:
			self.name = info.getName(self.service)
		tlist = [
			(_("Don't reconstruct"), "CALLFUNC", self.confirmed0),
			(_("Reconstruct the .ap and .sc files of the selected movie"), "CALLFUNC", self.confirmed1),
			(_("Reconstruct all missing .ap and .sc files in this directory"), "CALLFUNC", self.confirmed2),
			(_("Check any running reconstruct process"), "CALLFUNC", self.confirmed3),
		]
		ChoiceBox.__init__(self, session, _("What would you like to reconstruct?  (\"%s\")") % (self.name), list = tlist, selection = 0)
		self.skinName = "ChoiceBox"

	def confirmed0(self, arg):
		self.close()

	def confirmed1(self, arg):
		ReconstructApScSpawn(self.session, self, [recons_path, self.service.getPath()], self.name, _("movie"))

	def confirmed2(self, arg):
		dir = self.dirName(self.service.getPath())
		ReconstructApScSpawn(self.session, self, [recons_path, "-d", dir], dir, _("directory"))

	def confirmed3(self, arg):
		output = global_recons_queue.checkOutput()
		if output == False:
			mess = "There is no running reconstruction process"
		else:
			mess = "Current reconstruction process output:\n%s" % output
		self.session.openWithCallback(self.close, MessageBox, mess, MessageBox.TYPE_INFO)

	def dirName(self, str):
		return '/'.join(str.split('/')[:-1]) + '/'


class ReconstructApScQueue:
	def __init__(self):
		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.runDone)
		self.container.dataAvail.append(self.collOutput)
		self.queue = []
		self.output = ""
		self.running = False

	def enqueue(self, cb, cmd):
		self.queue.append((cb, cmd))
		if not self.running:
			self.runNext()
			return True
		else:
			return False

	def collOutput(self, data):
		self.output += data

	def checkOutput(self):
		if not self.running:
			return False
		else:
			return self.output

	def runNext(self):
		self.output = ""
		if not self.queue:
			self.running = False
		else:
			self.running = True
			self.container.execute(*self.queue[0][1])

	def runDone(self, retval):
		cb = self.queue[0][0]
		self.queue = self.queue[1:]
		cb(retval, self.output)
		self.runNext()

global_recons_errors = [_("The %s \"%s\" is successfully processed:\n%s"),
		      _("Processing failed for the %s \"%s\":\n%s")]

global_recons_queue = ReconstructApScQueue()

global_recons_block = False

class ReconstructApScSpawn:
	def __init__(self, session, parent, clist, name, typename):
		global global_recons_queue
		global global_recons_block
		self.session = session
		self.parent = parent
		self.name = name
		self.typename = typename
		self.clist = [clist[0]] + clist
		self.mess = ""
		self.dialog = False
		self.waitTimer = eTimer()
		self.waitTimer.callback.append(self.doWaitAck)
		if global_recons_queue.enqueue(self.doAck, self.clist):
			mess = _("The %s \"%s\" is processed in the background.") % (self.typename, self.name)
		else:
			mess = _("Another movie or directory is currently processed.\nThe %s \"%s\" will be processed in the background after it.") % (self.typename, self.name)
		global_recons_block = True
		self.dialog = self.session.openWithCallback(self.endc, MessageBox, mess, MessageBox.TYPE_INFO)

	def doAck(self, retval, output):
		global global_recons_errors
		self.mess = global_recons_errors[retval] % (self.typename, self.name, output)
		self.doWaitAck()

	def doWaitAck(self):
		global global_recons_block
		if Screens.Standby.inStandby or not self.session.in_exec or (global_recons_block and not self.dialog):
			self.waitTimer.start(2000, True)
		else:
			global_recons_block = True
			self.session.openWithCallback(self.endw, MessageBox, self.mess, MessageBox.TYPE_INFO)

	def endw(self, arg = 0):
		global global_recons_block
		global_recons_block = False
		if self.session.current_dialog == self.dialog:
			self.session.current_dialog.close(True)
			self.endc(arg)

	def endc(self, arg = 0):
		global global_recons_block
		global_recons_block = False
		self.dialog = False
		self.parent.close()
