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
from Components.config import ConfigYesNo, NoSave

# Plugin internal
from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ControllerBase import ControllerBase

# Plugin specific
import os


# Constants
CRASHLOG_DIR = '/media/hdd'

SUBJECT = _("Found CrashLog(s)")
BODY    = _("Crashlog(s) are attached")


class CrashLog(ControllerBase):
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		ControllerBase.__init__(self)
		self.crashlogs = []

		# Default configuration
		self.setOption( 'delete_logs', NoSave(ConfigYesNo( default=False )), _("Delete crashlog(s)") )

	def run(self, callback, errback):
		# At the end a plugin has to call one of the functions: callback or errback
		# Callback should return with at least one of the parameter: Header, Body, Attachment
		# If empty or none is returned, nothing will be sent
		self.crashlogs = []
		text = "Found crashlogs, see attachment(s)\n"
		for file in os.listdir( CRASHLOG_DIR ):
			if file.startswith("enigma2_crash_") and file.endswith(".log"):
				crashlog = os.path.join( CRASHLOG_DIR, file )
				self.crashlogs.append(crashlog)
		if self.crashlogs:
			callback( SUBJECT, BODY, self.crashlogs )
		else:
			callback()

	# Callback functions
	def callback(self):
		# Called after all services succeded
		if self.getValue('delete_logs'):
			# Delete crashlogs
			for crashlog in self.crashlogs[:]:
				if os.path.exists( crashlog ):
					os.remove( crashlog )
				self.crashlogs.remove( crashlog )
		else:
			# Rename crashlogs to avoid resending it
			for crashlog in self.crashlogs[:]:
				if os.path.exists( crashlog ):
					# Adapted from autosubmit - instead of .sent we will use .pushed
					currfilename = str(os.path.basename(crashlog))
					newfilename = "/media/hdd/" + currfilename + ".pushed"
					os.rename(crashlog, newfilename)
				self.crashlogs.remove( crashlog )

	def errback(self):
		# Called after all services has returned, but at least one has failed
		self.crashlogs = []
