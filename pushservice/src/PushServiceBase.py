import os

# Config
from Components.config import *

# XML
from xml.etree.cElementTree import Element, SubElement, Comment
from Tools.XMLTools import stringToXML

# Plugin internal
from . import _
from PushMail import PushMail
from PluginModules import PluginModules
from PushServiceConfigFile import PushServiceConfigFile
from PluginBase import PluginBase


# Constants
PLUGIN = "Plugin"
OPTION = "Option"


class PushServiceBase(PushMail, PluginModules, PushServiceConfigFile):

	def __init__(self, path=""):
		PushMail.__init__(self)
		PluginModules.__init__(self)
		PushServiceConfigFile.__init__(self)


	######################################
	# Plugin handling
	def begin(self, plugins):
		# Loop over all Plugins
		if plugins:
			for plugin in self.plugins:
				if plugin.getEnable():
					plugin.begin()

	def end(self, plugins):
		# Loop over all Plugins
		if plugins:
			for plugin in self.plugins:
				if plugin.getEnable():
					plugin.end()

	def run(self, plugins, send=True):
		response = ""
		print _("PushService started: ") + strftime( _("%d.%m.%Y %H:%M"), localtime() )
		
		# Loop over all Plugins
		if plugins:
			for plugin in plugins:
				if plugin.getEnable():
					print _("PushService running: ") + str( plugin.getName() )
					subject, text, attachments = "", "", []
					
					try:
						# Run plugin
						ret = plugin.run()
					except Exception, e:
						print _("PushService run exception ") + str(e)
						if sys.exc_info()[0]:
							print _("Unexpected error: "), sys.exc_info()[0]
							traceback.print_exc(file=sys.stdout)
						ret = None
					
					# Parse return value(s)
					if ret:
						if len(ret) == 3:
							subject, text, attachments = ret
						elif len(ret) == 2:
							# No attachment given
							subject, text = ret
							attachments = []
						else:
							# Header and Body will contain the same
							subject = text = ret
							attachments = []
						
						# Prepare resonse text
						if subject:	response += "[ " + subject + " ]\n\n"
						if text:		response += text + "\n\n\n"
						
						if send and subject:
							# Push mail
							self.push(subject, text, attachments, plugin.success, plugin.error)
		return response or "Nothing to send"


	######################################
	# Config
	def load(self):
		path = config.pushservice.xmlpath.value
		# Read xml config file
		root = self.readXML( path )
		if root:
			# Reset the unique id counter
			PluginBase.resetUniqueID()
			return self.parseConfig( root )
		else:
			return []

	def save(self, plugins):
		path = config.pushservice.xmlpath.value
		root = self.buildConfig( plugins )
		self.writeXML( root, path )


	######################################
	# Internal
	def parseConfig(self, root):
		plugins = []
		
		#if version != CURRENT_CONFIG_VERSION:
		#	parseConfigOld(configuration, list, uniqueTimerId)
		#	return
		
		if root:
			from xml.etree.cElementTree import tostring
			for element in root.findall(PLUGIN):
				name = element.get("name", "")
				enable = element.get("enable", "True")
				if name:
					plugin = self.instantiatePlugin(name)
					if plugin:
						plugin.setEnable(eval(enable))
						
						# Set plugin options
						options = []
						for option in element.findall(OPTION):
							key = option.get("key", "")
							value = option.text
							if key and value:
								options.append((key, value))
						
						if options:
							plugin.setOptions(options)
						
						print "PLUGIN APPEND"
						
						# Append to active plugin list
						plugins.append(plugin)
		return plugins

	def buildConfig(self, plugins):
		# Generate List in RAM
		from plugin import NAME, VERSION
		
		# Header
		root = Element('PushService')
		root.set('version', VERSION)
		root.append(Comment(_("Don't edit this manually unless you really know what you are doing")))
		
		# Body
		if plugins:
			for plugin in plugins:
				# Add plugin
				element = SubElement(root, PLUGIN, name=stringToXML(plugin.getName()), enable=stringToXML(plugin.getStringEnable()))
				
				# Add options
				options = plugin.getStringOptions()
				if options:
					for key, value, description in options:
						SubElement( element, OPTION, key = stringToXML(key) ).text = stringToXML(value)
		
		return root
