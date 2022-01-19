# -*- coding: utf-8 -*-
#######################################################################
#
#    Series Plugin for Enigma-2
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

from __future__ import absolute_import
import os
import sys
import traceback

from Tools.Directories import resolveFilename, SCOPE_PLUGINS

# Plugin framework
import imp
import inspect

# Plugin internal
from . import _
from .Logger import log

# Constants
IDENTIFIER_PATH = os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Identifiers/")


class Modules(object):

	def __init__(self):
		from .IdentifierBase import IdentifierBase2
		self.modules = self.loadModules(IDENTIFIER_PATH, IdentifierBase2)
		log.debug("SP Modules:", self.modules)

	#######################################################
	# Module functions
	def loadModules(self, path, base):
		modules = {}

		if not os.path.exists(path):
			log.debug("[SP Modules]: Error: Path doesn't exist: " + path)
			return

		# Import all subfolders to allow relative imports
		for root, dirs, files in os.walk(path):
			if root not in sys.path:
				sys.path.append(root)

		# List files
		files = [fname[:-3] for fname in os.listdir(path) if fname.endswith(".py") and not fname.startswith("__")]  # FIXME pyc
		log.debug(files)
		if not files:
			files = [fname[:-4] for fname in os.listdir(path) if fname.endswith(".pyo")]
			log.debug(files)

		# Import modules
		for name in files:
			module = None

			if name == "__init__":
				continue

			try:
				fp, pathname, description = imp.find_module(name, [path])
			except Exception as e:
				log.debug("[SP Modules] Find module exception: " + str(e))
				fp = None

			if not fp:
				log.debug("[SP Modules] No module found: " + str(name))
				continue

			try:
				module = imp.load_module(name, fp, pathname, description)
			except Exception as e:
				log.debug("[SP Modules] Load exception: " + str(e))
			finally:
				# Since we may exit via an exception, close fp explicitly.
				if fp:
					fp.close()

			if not module:
				log.debug("[SP Modules] No module available: " + str(name))
				continue

			# Continue only if the attribute is available
			if not hasattr(module, name):
				log.debug("[SP Modules] Warning attribute not available: " + str(name))
				continue

			# Continue only if attr is a class
			attr = getattr(module, name)
			if not inspect.isclass(attr):
				log.debug("[SeriesService] Warning no class definition: " + str(name))
				continue

			# Continue only if the class is a subclass of the corresponding base class
			if not issubclass(attr, base):
				log.debug("[SP Modules] Warning no subclass of base: " + str(name))
				continue

			# Add module to the module list
			modules[name] = attr
		return modules

	def instantiateModuleWithName(self, name):
		if self.modules:
			module = self.modules.get(name)
			if module and callable(module):
				# Create instance
				try:
					return module()
				except Exception as e:
					log.exception("[SeriesService] Instantiate exception: " + str(module) + "\n" + str(e))
					if sys.exc_info()[0]:
						log.debug("Unexpected error: ", sys.exc_info()[0])
						traceback.print_exc(file=sys.stdout)
						return None
			else:
				log.debug("[SeriesService] Module is not callable: " + str(name))
				return None
		else:
			log.debug("[SeriesService] No modules for name: " + str(name))
			return None

	def instantiateModule(self, module):
		if module and callable(module):
			# Create instance
			try:
				return module()
			except Exception as e:
				log.exception("[SeriesService] Instantiate exception: " + str(module) + "\n" + str(e))
				if sys.exc_info()[0]:
					log.debug("Unexpected error: ", sys.exc_info()[0])
					traceback.print_exc(file=sys.stdout)
					return None
		else:
			log.debug("[SeriesService] Module is not callable: " + str(module.getClass()))
			return None
