#######################################################################
#
#    Push Service for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

# Config
from Components.config import ConfigYesNo, ConfigText, ConfigNumber, NoSave

# Plugin internal
from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.PluginBase import PluginBase

# Plugin specific
import os
from time import time
from Plugins.SystemPlugins.SoftwareManager.SoftwareTools import iSoftwareTools


SUBJECT = _("IPKG Update Notification")
BODY    = _("There are updates available:\n%s")


class IPKGUpdateNotification(PluginBase):
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		PluginBase.__init__(self)
		
		# Default configuration
		self.setOption( 'selfcheck', NoSave(ConfigYesNo( default = False )), _("Start update check if not done yet") )

	def run(self):
		# Return Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		# Adapted from Software Manager
		if iSoftwareTools.lastDownloadDate is not None and iSoftwareTools.lastDownloadDate > ( time() - (24*60*60) ):
			# Last refresh was within one day
			updates = self.buildList()
			if updates:
				return SUBJECT, BODY % (updates)
		else:
			print "IPKGUpdateNotification run else"
			if self.getValue('selfcheck'):
				# Refresh package list
				iSoftwareTools.startSoftwareTools(self.getUpdateInfosCB)
				#TODO async

	def getUpdateInfosCB(self, retval = None):
		if retval is not None:
			if retval is True:
				if iSoftwareTools.available_updates is not 0:
					# _("There are at least ") + str(iSoftwareTools.available_updates) + _(" updates available.")
					print "Updates available."
					return self.buildList()
				else:
					# _("There are no updates available.")
					print "There are no updates available."
					pass
			elif retval is False:
				if iSoftwareTools.lastDownloadDate is None:
					if iSoftwareTools.NetworkConnectionAvailable:
						# _("Updatefeed not available.")
						print "Updatefeed not available."
						pass
					else:
						# _("No network connection available.")
						print "No network connection available."
						pass
				else:
					print "IPKGUpdateNotification getUpdates"
					# Call update
					iSoftwareTools.lastDownloadDate = time()
					iSoftwareTools.list_updating = True
					iSoftwareTools.getUpdates(self.getUpdateInfosCB)
					#TODO async

	def buildList(self):
		updates = ""
		for package in iSoftwareTools.available_updatelist:
			packagename = package[0]
			instversion = ""
			if packagename in iSoftwareTools.installed_packetlist:
				instversion = iSoftwareTools.installed_packetlist[packagename]
			updversion = ""
			for p, v, d in iSoftwareTools.available_packetlist:
				if p == packagename:
					updversion = v
					break
			updates += packagename + " :\t" + instversion + " :\t" + updversion + "\n"
		return updates

