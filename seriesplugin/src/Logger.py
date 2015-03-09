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

import os, sys, traceback

from Components.config import config

from Screens.MessageBox import MessageBox

#import requests


def splog(*args):
	strargs = ""
	for arg in args:
		if strargs: strargs += " "
		strargs += str(arg)
	
	if config.plugins.seriesplugin.debug_prints.value:
		print strargs
	
	if config.plugins.seriesplugin.write_log.value:
		strargs += "\n"
		
		# Append to file
		f = None
		try:
			f = open(config.plugins.seriesplugin.log_file.value, 'a')
			f.write(strargs)
			if sys.exc_info()[0]:
				print "Unexpected error:", sys.exc_info()[0]
				traceback.print_exc(file=f)
		except Exception as e:
			print "SeriesPlugin splog exception " + str(e)
		finally:
			if f:
				f.close()
	
	if sys.exc_info()[0]:
		print "Unexpected error:", sys.exc_info()[0]
		traceback.print_exc(file=sys.stdout)
	
	sys.exc_clear()

