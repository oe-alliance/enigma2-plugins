from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from enigma import eServiceCenter, eTimer
from Components import Task
from Tools import Notifications

def main(session, service, **kwargs):
	session.open(ReconstructApSc, service, **kwargs)

def rApScFinishedMessage():
	finished = True
	for job in Task.job_manager.getPendingJobs():
		if job.name == _("Reconstruct AP/SC"):
			finished = False
			break
	if finished:
		tasks = '\n'.join(rApScTasks)
		Notifications.AddNotification(MessageBox, _("Reconstruct AP/SC is finished !\n\n%s")%tasks, type=MessageBox.TYPE_INFO, timeout=30)
	else:
		rApScTimer.startLongTimer(10)

rApScTasks = []
rApScTimer = eTimer()
rApScTimer.callback.append(rApScFinishedMessage)

def Plugins(**kwargs):
	return PluginDescriptor(name="ReconstructApSc", description=_("Reconstruct AP/SC ..."), where=PluginDescriptor.WHERE_MOVIELIST, fnc=main)

class ReconstructApSc(ChoiceBox):
	def __init__(self, session, service):
		self.service = service
		serviceHandler = eServiceCenter.getInstance()
		self.offline = serviceHandler.offlineOperations(self.service)
		path = self.service.getPath()
		info = serviceHandler.info(self.service)
		if not info:
			self.name = path
		else:
			self.name = info.getName(self.service)
		if self.offline is None:
			tlist = [(_("Cannot reconstruct this item"),  "CALLFUNC", self.confirmed0),]
		else:
			tlist = [
				(_("Don't reconstruct"), "CALLFUNC", self.confirmed0),
				(_("Reconstruct the .ap and .sc files of the selected movie"), "CALLFUNC", self.confirmed1),
				# not yet #  (_("Reconstruct all missing .ap and .sc files in this directory"), "CALLFUNC", self.confirmed2),
			]
		ChoiceBox.__init__(self, session, _("What would you like to reconstruct?  (\"%s\")") % (self.name), list=tlist, selection=0)
		self.skinName = "ChoiceBox"

	def confirmed0(self, arg):
		self.close()

	def confirmed1(self, arg):
		global rApScTasks
		if not rApScTimer.isActive():
			rApScTimer.startLongTimer(10)
			rApScTasks = []
		rApScTasks.append(str(len(rApScTasks)+1) + '. ' + self.name)
		job = Task.Job(_("Reconstruct AP/SC"))
		task = Task.PythonTask(job, self.name)
		task.work = self.offline.reindex
		Task.job_manager.AddJob(job)
		self.close()
