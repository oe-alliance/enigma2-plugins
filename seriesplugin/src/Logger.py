# -*- coding: utf-8 -*-
#######################################################################
#
#    Series Plugin for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=TBD
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

from . import _

import logging

import os, sys, traceback

from Components.config import config

from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox


log = None


class Logger(object):
	def __init__(self):
		self.local_log = ""
		self.local_log_enabled = False
		
		self.instance = logging.getLogger("SeriesPlugin")
		self.instance.setLevel(logging.DEBUG)
		
		self.reinit()
	
	def reinit(self):
		self.instance.handlers = [] 
		
		if config.plugins.seriesplugin.debug_prints.value:
			shandler = logging.StreamHandler(sys.stdout)
			shandler.setLevel(logging.DEBUG)

			sformatter = logging.Formatter('[%(name)s] %(levelname)s - %(message)s')
			shandler.setFormatter(sformatter)

			self.instance.addHandler(shandler)
			self.instance.setLevel(logging.DEBUG)
			
		if config.plugins.seriesplugin.write_log.value:
			fhandler = logging.FileHandler(config.plugins.seriesplugin.log_file.value)
			fhandler.setLevel(logging.DEBUG)

			fformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
			fhandler.setFormatter(fformatter)

			self.instance.addHandler(fhandler)
			self.instance.setLevel(logging.DEBUG)

	def start(self):
		# Start a temporary log, which will be removed after reading.
		# Debug is not included
		self.local_log = ""
		self.local_log_enabled = True

	def append(self, strargs):
		if self.local_log_enabled:
			self.local_log += "&#13;&#10;" + strargs
	
	def get(self):
		self.local_log_enabled = False
		return self.local_log

	def shutdown(self):
		if self.instance:
			self.instance.shutdown()

	def success(self, *args):
		strargs = " ".join( [ str(arg) for arg in args ] )
		
		self.append(strargs)
		
		if self.instance:
			self.instance.info(strargs)
		
		elif config.plugins.seriesplugin.debug_prints.value:
			print strargs
		
		if int(config.plugins.seriesplugin.popups_success_timeout.value) != 0:
			AddPopup(
					strargs,
					MessageBox.TYPE_INFO,
					int(config.plugins.seriesplugin.popups_success_timeout.value),
					'SP_PopUp_ID_Success_'+strargs
				)

	def info(self, *args):
		strargs = " ".join( [ str(arg) for arg in args ] )
		
		self.append(strargs)
		
		if self.instance:
			self.instance.info(strargs)
		
		elif config.plugins.seriesplugin.debug_prints.value:
			print strargs

	def debug(self, *args):
		strargs = " ".join( [ str(arg) for arg in args ] )
		
		if self.instance:
			self.instance.debug(strargs)
		
		elif config.plugins.seriesplugin.debug_prints.value:
			print strargs
		
		if sys.exc_info()[0]:
			self.instance.debug( str(sys.exc_info()[0]) )
			self.instance.debug( str(traceback.format_exc()) )
			sys.exc_clear()

	def warning(self, *args):
		strargs = " ".join( [ str(arg) for arg in args ] )
		
		self.append(strargs)
		
		if self.instance:
			self.instance.warning(strargs)
		
		elif config.plugins.seriesplugin.debug_prints.value:
			print strargs
		
		if int(config.plugins.seriesplugin.popups_warning_timeout.value) != 0:
			AddPopup(
					strargs,
					MessageBox.TYPE_WARNING,
					int(config.plugins.seriesplugin.popups_warning_timeout.value),
					'SP_PopUp_ID_Warning_'+strargs
				)

	def error(self, *args):
		strargs = " ".join( [ str(arg) for arg in args ] )
		
		self.append(strargs)
		
		if self.instance:
			self.instance.error(strargs)
		
		elif config.plugins.seriesplugin.debug_prints.value:
			print strargs

		AddPopup(
					strargs,
					MessageBox.TYPE_ERROR,
					-1,
					'SP_PopUp_ID_Error_'+strargs
				)
		
	def exception(self, *args):
		strargs = " ".join( [ str(arg) for arg in args ] )
		
		self.append(strargs)
		
		if self.instance:
			self.instance.exception(strargs)
		
		elif config.plugins.seriesplugin.debug_prints.value:
			print strargs
		
		AddPopup(
					strargs,
					MessageBox.TYPE_ERROR,
					-1,
					'SP_PopUp_ID_Exception_'+strargs
				)


log = Logger()
