# -*- coding: utf-8 -*-
# for localized messages
from __init__ import _

import Components.Task
from enigma import eTimer
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from NetworkBrowser import NetworkBrowser
from Components.Network import iNetwork
from MountManager import AutoMountManager
from AutoMount import iAutoMount

plugin_path = ""
mountagaincheckpoller = None

class MountAgainCheckPoller:
	def __init__(self, session):
		self.session = session
		self.timer = eTimer()
		self.timer.callback.append(self.onTimer)
		self.timer.startLongTimer(0)

	def onTimer(self):
		self.timer.stop()
		if config.networkbrowser.automountpoll.value:
			self.mountagaincheck()
		else:
			self.timer.startLongTimer(30 * 60)

	def mountagaincheck(self):
		Components.Task.job_manager.AddJob(self.createCheckJob())

	def createCheckJob(self):
		job = Components.Task.Job(_("Network Browser"))
		isPlaying = ""
		try:
			service = self.session.nav.getCurrentlyPlayingServiceReference()
			isPlaying = service.toString()
			if not self.session.nav.RecordTimer.isRecording() and not isPlaying.startswith('1:0:0:0:0:0:0:0:0:0:'):
				print '[Networkbrowser MountAgain] Mounting network shares...'
				task = Components.Task.PythonTask(job, _("Mounting network shares..."))
				task.work = self.JobEpgCache
				task.weighting = 1
			elif self.session.nav.RecordTimer.isRecording():
				print '[Networkbrowser MountAgain] Skipping, as recording is in place.'
			elif isPlaying.startswith('1:0:0:0:0:0:0:0:0:0:'):
				print '[Networkbrowser MountAgain] Skipping, as watching a movie file is in place.'
		except:
			pass
		task = Components.Task.PythonTask(job, _("Adding schedule..."))
		task.work = self.JobSched
		task.weighting = 1
		return job

	def JobEpgCache(self):
		print '[Networkbrowser MountAgain] mounting network shares.'
		iAutoMount.getAutoMountPoints() 

	def JobSched(self):
		self.timer.startLongTimer(int(config.networkbrowser.automountpolltimer.value) * 3600)

def autostart(reason, session=None, **kwargs):
	global mountagaincheckpoller
	global _session
	if reason == 0:
		if session is not None:
			_session = session
			if mountagaincheckpoller is None:
				mountagaincheckpoller = MountAgainCheckPoller(session)
		# session.nav.RecordTimer.isRecording()

def NetworkBrowserMain(session, iface=None, **kwargs):
	session.open(NetworkBrowser, iface, plugin_path)

def MountManagerMain(session, iface=None, **kwargs):
	session.open(AutoMountManager, iface, plugin_path)

def NetworkBrowserCallFunction(iface):
	return NetworkBrowserMain

def MountManagerCallFunction(iface):
	return MountManagerMain

def RemountMain(session, iface=None, **kwargs):
	from AutoMount import iAutoMount
	iAutoMount.getAutoMountPoints() 

def RemountCallFunction(iface):
	return RemountMain

def SchedMount(session, **kwargs):
	session.open(MountAgainCheck)

def Plugins(path, **kwargs):
	global plugin_path
	plugin_path = path
	return [
		PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
		PluginDescriptor(name=_("Network Browser"), description=_("Search for network shares"), where=PluginDescriptor.WHERE_NETWORKMOUNTS, fnc={"ifaceSupported": NetworkBrowserCallFunction, "menuEntryName": lambda x: _("Network Browser"), "menuEntryDescription": lambda x: _("Search for network shares...")}),
		PluginDescriptor(name=_("Mount Manager"), description=_("Manage network shares"), where=PluginDescriptor.WHERE_NETWORKMOUNTS, fnc={"ifaceSupported": MountManagerCallFunction, "menuEntryName": lambda x: _("Mount Manager"), "menuEntryDescription": lambda x: _("Manage your network shares...")}),
		PluginDescriptor(name=_("Mount Again"), description=_("Attempt to mount shares again"), where=PluginDescriptor.WHERE_NETWORKMOUNTS, fnc={"ifaceSupported": RemountCallFunction, "menuEntryName": lambda x: _("Mount again"), "menuEntryDescription": lambda x: _("Attempt to recover lost mounts (in background)")})
	]
