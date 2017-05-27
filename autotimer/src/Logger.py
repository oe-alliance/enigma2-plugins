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

localLog = False
log = ""
logger = None

def initLog():
	global logger
	logger = logger or logging.getLogger("AT")
	logger.setLevel(logging.DEBUG)

	logger.handlers = [] 

	if config.plugins.autotimer.log_shell.value:
		shandler = logging.StreamHandler(sys.stdout)
		shandler.setLevel(logging.DEBUG)

		sformatter = logging.Formatter('%(name)s %(levelname)s - %(message)s')
		shandler.setFormatter(sformatter)

		logger.addHandler(shandler)
		logger.setLevel(logging.DEBUG)
		
	if config.plugins.autotimer.log_write.value:
		fhandler = logging.FileHandler(config.plugins.autotimer.log_file.value)
		fhandler.setLevel(logging.DEBUG)

		fformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
		fhandler.setFormatter(fformatter)

		logger.addHandler(fhandler)
		logger.setLevel(logging.DEBUG)

def shutdownLog():
	global logger
	if logger:
		logger.shutdown()

def startLog():
	global log, localLog
	log = ""
	localLog = True

def getLog():
	global log, localLog
	localLog = False
	return log

def doDebug(*args):
	strargs = " ".join( [ str(arg) for arg in args ] )

	global logger
	if logger:
		logger.debug(strargs)

	elif config.plugins.autotimer.log_shell.value:
		print strargs

def doLog(*args):
	strargs = " ".join( [ str(arg) for arg in args ] )

	global log, localLog
	if localLog:
		log += "&#13;&#10;" + strargs

	global logger
	if logger:
		logger.info(strargs)

	elif config.plugins.autotimer.log_shell.value:
		print strargs

initLog()
