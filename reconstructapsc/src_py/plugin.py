from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from enigma import eServiceCenter

def main(session, service, **kwargs):
	session.open(ReconstructApSc, service, **kwargs)

def Plugins(**kwargs):
	return PluginDescriptor(name="ReconstructApSc", description=_("Reconstruct AP/SC ..."), where = PluginDescriptor.WHERE_MOVIELIST, fnc=main)

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
		ChoiceBox.__init__(self, session, _("What would you like to reconstruct?  (\"%s\")") % (self.name), list = tlist, selection = 0)
		self.skinName = "ChoiceBox"

	def confirmed0(self, arg):
		self.close()

	def confirmed1(self, arg):
		from Components import Task
		job = Task.Job(_("Reconstruct AP/SC"))
		task = Task.PythonTask(job, _("Reconstruct AP/SC"))
		task.work = self.offline.reindex
		Task.job_manager.AddJob(job)
		self.close()
