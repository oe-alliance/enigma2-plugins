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

import os
import sys
import traceback
from time import localtime, strftime

# Config
from Components.config import config

# XML
from xml.etree.cElementTree import Element, SubElement, Comment
from Tools.XMLTools import stringToXML

# Tools
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.BoundFunction import boundFunction

# Plugin internal
from . import _
from Modules import Modules
from ConfigFile import ConfigFile
from ServiceBase import ServiceBase
from ControllerBase import ControllerBase


# Constants
SERVICE = "Service"
CONTROLLER = "Controller"
OPTION = "Option"

SERVICE_PATH = os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions/PushService/Services/")
CONTROLLER_PATH = os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions/PushService/Controller/")


class PushServiceBase(Modules, ConfigFile):

	def __init__(self, path=""):
		Modules.__init__(self)
		ConfigFile.__init__(self)
		
		self.services = []
		self.controllers = []
		
		self.pushcallbacks = {}
		self.pusherrbacks = {}
		
		# Read module files from subfolders
		self.servicemodules = self.loadModules(SERVICE_PATH, ServiceBase)
		self.controllermodules = self.loadModules(CONTROLLER_PATH, ControllerBase)


	######################################
	# Setter / Getter
	def getServices(self):
		return self.services or []

	def getService(self, idx):
		if idx < len(self.services):
			return self.services[idx]
		else:
			return None

	def getAvlServices(self):
		slist = []
		if self.servicemodules:
			serviceclasses = [service.getClass() for service in self.services] if self.services else []
			for name, module in self.servicemodules.iteritems():
				if module.forceSingle():
					# We have to check if there is already a plugin instance
					if name in serviceclasses:
						# A service instance already exists
						continue
				slist.append((name, module))
			slist.sort()
		return slist

	def getServiceInstances(self):
		return [(service.getNameId(), service) for service in self.getServices()]

	def addService(self, module):
		id = None
		service = module and self.instantiateModule(module)
		if service:
			service.setEnable(True)
			self.services.append(service)
			self.services.sort(key=lambda x: (x.getUniqueID()))
			id = service.getUniqueID()
		return id

	def removeService(self, service):
		if service in self.services:
			self.services.remove(service)

	def getControllers(self):
		return self.controllers or []

	def getController(self, idx):
		if idx < len(self.controllers):
			return self.controllers[idx]
		else:
			return None

	def getAvlControllers(self):
		plist = []
		if self.controllermodules:
			controllerclasses = [controller.getClass() for controller in self.controllers] if self.controllers else []
			for name, module in self.controllermodules.iteritems():
				if module.forceSingle():
					# We have to check if there is already a controller instance
					if name in controllerclasses:
						# A controller instance already exists
						continue
				plist.append((name, module))
			plist.sort()
		return plist

	def getControllerInstances(self):
		return [(controller.getNameId(), controller) for controller in self.getControllers()]

	def addController(self, module):
		id = None
		controller = module and self.instantiateModule(module)
		if controller:
			controller.setEnable(True)
			self.controllers.append(controller)
			self.controllers.sort(key=lambda x: (x.getUniqueID()))
			id = controller.getUniqueID()
		return id

	def removeController(self, controller):
		if controller in self.controllers:
			self.controllers.remove(controller)


	######################################
	# Config
	def copyto(self, destination):
		destination.services = self.services
		destination.controllers = self.controllers
		destination.servicemodules = self.servicemodules
		destination.controllermodules = self.controllermodules

	def copyfrom(self, source):
		self.services = source.services
		self.controllers = source.controllers
		self.servicemodules = source.servicemodules
		self.controllermodules = source.controllermodules

	def load(self):
		# Read xml config file
		root = self.readXML()
		if root:
			services = []
			controllers = []
			
			# Reset the unique id counters
			ServiceBase.resetUniqueID()
			ControllerBase.resetUniqueID()
			# Parse Config
			def parse(root, typ, modules):
				instances = []
				if root:
					for element in root.findall(typ):
						name = element.get("name", "")
						enable = element.get("enable", "True")
						if name:
							module = modules.get(name, None)
							instance = self.instantiateModule(module)
							if instance:
								instance.setEnable(eval(enable))
								
								# Set instance options
								options = []
								for option in element.findall(OPTION):
									key = option.get("key", "")
									value = option.text
									if key and value:
										options.append((key, value))
								
								if options:
									instance.setOptions(options)
								
								# Append to active controller list
								instances.append(instance)
				return instances
			services = parse(root, SERVICE, self.servicemodules)
			controllers = parse(root, CONTROLLER, self.controllermodules)
			
			self.services = services
			self.controllers = controllers
		else:
			self.services = []
			self.controllers = []

	def save(self):
		# Generate List in RAM
		root = None
		services = self.services
		controllers = self.controllers
		
		# Build Header
		from plugin import NAME, VERSION
		root = Element(NAME)
		root.set('version', VERSION)
		root.append(Comment(_("Don't edit this manually unless you really know what you are doing")))
		
		# Build Body
		def build(root, instances, typ):
			for instance in instances:
				# Add module
				element = SubElement(root, typ, name=stringToXML(instance.getName()), enable=stringToXML(instance.getStringEnable()))
				# Add options
				options = instance.getStringOptions()
				if options:
					for key, value, description in options:
						SubElement(element, OPTION, key=stringToXML(key)).text = stringToXML(value)
			return root
		
		if services:
			root = build(root, services, SERVICE)
		if controllers:
			root = build(root, controllers, CONTROLLER)
		
		self.writeXML(root)


	######################################
	# Controller handling
	def begin(self):
		# Loop over all Services
		for service in self.getServices():
			if service.getEnable():
				service.begin()
		# Loop over all Controllers
		for controller in self.getControllers():
			if controller.getEnable():
				controller.begin()

	def end(self):
		# Loop over all Services
		for service in self.getServices():
			if service.getEnable():
				service.end()
		# Loop over all Controllers
		for controller in self.getControllers():
			if controller.getEnable():
				controller.end()

	def run(self):
		print _("PushService started: ") + strftime(_("%d.%m.%Y %H:%M"), localtime())
		
		controllers = self.controllers
		self.pushcallbacks = {}
		self.pusherrbacks = {}
		
		# Loop over all Controllers
		if controllers:
			for controller in controllers:
				if controller.getEnable():
					print _("PushService running: ") + str(controller.getName())
					
					try:
						# Run controller
						ret = controller.run(
								boundFunction(self.runcallback, controller),
								boundFunction(self.runcallback, controller))
					except Exception, e:
						print _("PushService controller run() exception")
						exc_type, exc_value, exc_traceback = sys.exc_info()
						traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

	def runcallback(self, controller, *args):
		services = self.services
		subject, body, attachments = "", "", []
		
		# Parse return value(s)
		if args:
			if len(args) == 3:
				subject, body, attachments = args
			elif len(args) == 2:
				# No attachments given
				subject, body = args
			else:
				# Only header returned
				subject = args
			
			if subject:
				# Push notification
				self.push(controller, subject, body, attachments)

	def runerrback(self, controller, *args):
		print _("controller %s returned error(s)") % controller.getName()
		for arg in args:
			if isinstance(arg, Exception):
				print str(arg.type), str(arg.value)
			elif arg:
				print str(arg)

	def push(self, controller, subject, text="", attachments=[]):
		print "push"
		services = self.services
		if not services:
			# Fallback to PopUp
			module = self.servicemodules.get("PopUp", None)
			popup = self.instantiateModule(module)
			# Missing but not necessary: popup.begin() -> popup.push(...) -> popup.end()
			services = [popup]
		if services:
			for service in services:
				if service and service.getEnable():
					try:
						service.push(
								boundFunction(self.pushcallback, service, controller),
								boundFunction(self.pusherrback, service, controller),
								controller.getName(),
								subject, text, attachments)
					except Exception, e:
						print _("PushService Service push() exception")
						exc_type, exc_value, exc_traceback = sys.exc_info()
						traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stdout)

	def pushcallback(self, service, controller, *args):
		print "pushcallback"
		key = (service, controller)
		if key not in self.pushcallbacks:
			self.pushcallbacks[key] = list(args)
		else:
			self.pushcallbacks[key].extend(list(args))
		self.pushcheckbacks(key)

	def pusherrback(self, service, controller, *args):
		print "pusherrback"
		print _("Service %s returned error(s)") % service.getName()
		for arg in args:
			if isinstance(arg, Exception):
				print str(arg.type), str(arg.value)
			elif arg:
				print str(arg)
		key = (service, controller)
		if key not in self.pusherrbacks:
			self.pusherrbacks[key] = list(args)
		else:
			self.pusherrbacks[key].extend(list(args))
		self.pushcheckbacks(key)

	def pushcheckbacks(self, key):
		print "pushcheckbacks"
		callparam = self.pushcallbacks.get(key, [])
		cntcall = len(callparam)
		errparam = self.pusherrbacks.get(key, [])
		cnterr = len(errparam)
		cntservices = len([service for service in self.services if service.getEnable()])
		
		# Check if all services already called and returned
		if (cntservices == (cntcall + cnterr)):
			service, controller = key
			if controller:
				# Check if no error is logged
				if (cnterr == 0):
					print "controller.callback()"
					controller.callback()
				else:
					controller.errback()
					print "controller.errback()"
