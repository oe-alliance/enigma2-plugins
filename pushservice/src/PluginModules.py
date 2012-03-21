# Plugin framework
import os, imp, sys, traceback

# Path
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

# Plugin internal
from . import _
from PluginBase import PluginBase


# Constants
PLUGIN_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/PushService/Plugins/" )
MODULE_PREFIX = 'PushService'


class PluginModules(object):

	def __init__(self):
		self.modules = {}
		
		self.loadModules()

	#######################################################
	# Module functions
	def loadModules(self, path = PLUGIN_PATH):
		self.modules = {}
		
		if not os.path.exists(path):
			return
		
		files = [fname[:-3] for fname in os.listdir(path) if fname.endswith(".py")]
		for name in files:
			module = None
			
			try:
				fp, pathname, description = imp.find_module(name, [path])
			except Exception, e:
				print _("[PushService] Find: ") + str(e)
				fp = None
			
			if not fp:
				print _("[PushService] Load: no module")
				continue
			
			try:
				# Use a prefix to avoid namespace conflicts
				module = imp.load_module(MODULE_PREFIX+name, fp, pathname, description)
			except Exception, e:
				print _("[PushService] Load: ") + str(e)
			finally:
				# Since we may exit via an exception, close fp explicitly.
				if fp:
					fp.close()
			
			if not module:
				continue
			
			# Instantiate only if the class is available
			if not hasattr(module, name):
				print _("[PushService] Warning no class definition")
				continue
			
			# Instantiate only if the class is a subclass of PluginBase
			if not issubclass( getattr(module, name), PluginBase):
				print _("[PushService] Warning no subclass of PluginBase")
				continue
			
			# Add module to the module list
			self.modules[name] = getattr(module, name)

	def instantiatePlugin(self, name):
		plugin = self.modules.get(name)
		if plugin and callable(plugin):
			# Create plugin instance
			try:
				return plugin()
			except Exception, e:
				print _("[PushService] Instantiate: ") + name + "\n" + str(e)
				if sys.exc_info()[0]:
					print _("Unexpected error: "), sys.exc_info()[0]
					traceback.print_exc(file=sys.stdout)
		else:
			print _("[PushService] Module is not callable")
			return None
