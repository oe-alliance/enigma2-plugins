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

import os, sys, traceback

# Plugin framework
import imp, inspect

# Plugin internal
from . import _
from ModuleBase import ModuleBase
from ServiceBase import ServiceBase
from ControllerBase import ControllerBase


class Modules(object):

	def __init__(self):
		pass

	#######################################################
	# Module functions
	def loadModules(self, path, base):
		modules = {}
		
		if not os.path.exists(path):
			return
		
		# Import all subfolders to allow relative imports
		for root, dirs, files in os.walk(path):
			if root not in sys.path:
				sys.path.append(root)
		
		# Import PushService modules
		files = [fname[:-3] for fname in os.listdir(path) if fname.endswith(".py")]
		for name in files:
			module = None
			
			if name == "__init__":
				continue
			
			try:
				fp, pathname, description = imp.find_module(name, [path])
			except Exception, e:
				print _("PushService Find module exception: ") + str(e)
				fp = None
			
			if not fp:
				print _("PushService No module found: ") + str(name)
				continue
			
			try:
				module = imp.load_module( name, fp, pathname, description)
			except Exception, e:
				print _("PushService Load exception: ") + str(e)
			finally:
				# Since we may exit via an exception, close fp explicitly.
				if fp: fp.close()
			
			if not module:
				print _("PushService No module available: ") + str(name)
				continue
			
			# Continue only if the attribute is available
			if not hasattr(module, name):
				print _("PushService Warning attribute not available: ") + str(name)
				continue
			
			# Continue only if attr is a class
			attr = getattr(module, name)
			if not inspect.isclass(attr):
				print _("PushService Warning no class definition: ") + str(name)
				continue
			
			# Continue only if the class is a subclass of the corresponding base class
			if not issubclass( attr, base):
				print _("PushService Warning no subclass of base: ") + str(name)
				continue
			
			# Add module to the module list
			modules[name] = attr
		return modules

	def instantiateModule(self, module):
		if module and callable(module):
			# Create instance
			try:
				return module()
			except Exception, e:
				print _("PushService Instantiate exception: ") + str(module) + "\n" + str(e)
				if sys.exc_info()[0]:
					print _("Unexpected error: "), sys.exc_info()[0]
					traceback.print_exc(file=sys.stdout)
		else:
			print _("PushService Module is not callable")
			return None
