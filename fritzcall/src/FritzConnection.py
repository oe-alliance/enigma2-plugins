#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
fritzconnection.py

This is a tool to communicate with the FritzBox.
All available actions (aka commands) and corresponding parameters are
read from the xml-configuration files requested from the FritzBox. So
the available actions may change depending on the FritzBox model and
firmware.
The command-line interface allows the api-inspection.
The api can also be inspected by a terminal session:

>>> import fritzconnection as fc
>>> fc.print_api()

'print_api' takes the optional parameters:
	address = ip-address
	port = port number (should not change)
	user = the username
	password = password (to access tr64-services)

In most cases you have to provide the ip (in case you changed the
default or have multiple boxes i.e. for multiple WLAN access points).
Also you have to send the password to get the complete api.

License: MIT https://opensource.org/licenses/MIT
Source: https://bitbucket.org/kbr/fritzconnection
Author: Klaus Bremer
Modified to use async communication, content level authentication and plain xml.etree.ElementTree: DrMichael
"""
# pylint: disable=C0111,C0103,C0301,W0603,W0403,C0302,W0312

__version__ = '0.6'

import logging, re, md5

import xml.etree.ElementTree as ET
from Components.config import config
from twisted.web.client import getPage

USERAGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"

# FritzConnection defaults:
FRITZ_IP_ADDRESS = '192.168.188.1'
FRITZ_TCP_PORT = 49000
FRITZ_IGD_DESC_FILE = 'igddesc.xml'
FRITZ_TR64_DESC_FILE = 'tr64desc.xml'
FRITZ_USERNAME = 'dslf-config'


# version-access:
def get_version():
	return __version__


class FritzConnectionException(Exception): pass
class ServiceError(FritzConnectionException): pass
class ActionError(FritzConnectionException): pass


class FritzAction(object):
	"""
	Class representing an action (aka command).
	Knows how to execute itself.
	Access to any password-protected action must require HTTP digest
	authentication.
	See: http://www.broadband-forum.org/technical/download/TR-064.pdf
	"""
	logger = logging.getLogger("FritzCall.FritzAction")
	debug = logger.debug
	info = logger.info
	warn = logger.warn
	error = logger.error
	exception = logger.exception
	
	header = {'soapaction': '',
			  'content-type': 'text/xml',
			  'charset': 'utf-8'}
	envelope = """
		<?xml version="1.0" encoding="utf-8"?>
		<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
					xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">%s%s
		</s:Envelope>
		"""
	header_initchallenge_template = """
		<s:Header>
 			<h:InitChallenge
				xmlns:h="http://soap-authentication.org/digest/2001/10/"
 				s:mustUnderstand="1">
 			<UserID>%s</UserID>
 			</h:InitChallenge >
 		</s:Header>
		"""
	header_clientauth_template = """
		<s:Header>
 			<h:ClientAuth
 				xmlns:h="http://soap-authentication.org/digest/2001/10/"
 				s:mustUnderstand="1">
 			<Nonce>%s</Nonce>
 			<Auth>%s</Auth>
 			<UserID>%s</UserID>
 			<Realm>%s</Realm>
 			</h:ClientAuth>
 		</s:Header>
		"""
	body_template = """
		<s:Body>
			<u:%(action_name)s xmlns:u="%(service_type)s">%(arguments)s
			</u:%(action_name)s>
		</s:Body>
		"""
	argument_template = """
		<s:%(name)s>%(value)s</s:%(name)s>"""
	method = 'post'
	address = port = ""
	nonce = auth = realm = ""

	def __init__(self, service_type, control_url, action_parameters):
		self.service_type = service_type
		self.control_url = control_url
		self.name = ''
		self.arguments = {}
		self.password = None
		self.__dict__.update(action_parameters)

# 	@property
# 	def info(self):
# 		return [self.arguments[argument].info for argument in self.arguments]

	def _body_builder(self, kwargs):
		"""
		Helper method to construct the appropriate SOAP-body to call a
		FritzBox-Service.
		"""
		p = {
			'action_name': self.name,
			'service_type': self.service_type,
			'arguments': '',
			}
		if kwargs:
			# self.debug(repr(kwargs))
			arguments = [
				self.argument_template % {'name': k, 'value': v}
				for k, v in kwargs.items()
			]
			p['arguments'] = ''.join(arguments)
		body = self.body_template.strip() % p
		# self.debug(body)
		return body

	def execute(self, callback, **kwargs):
		"""
		Calls the FritzBox action and returns a dictionary with the arguments.
		"""
		# self.debug("")
		headers = self.header.copy()
		headers['soapaction'] = '%s#%s' % (self.service_type, self.name)
# 		headers['Authorization'] = "Digest " + md5Sid
# 		self.debug("headers: " + repr(headers))
		data = self.envelope.strip() % ( self.header_initchallenge_template % config.plugins.FritzCall.username.value,
										self._body_builder(kwargs))
		url = 'http://%s:%s%s' % (self.address, self.port, self.control_url)

		# self.debug("url: " + url + "\n" + data)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = headers,
			postdata = data).addCallback(self._okExecute, callback, **kwargs).addErrback(self._errorExecute, callback)

	def _okExecute(self, content, callback, **kwargs):
		# self.debug("")
		if self.logger.getEffectiveLevel() == logging.DEBUG:
			linkP = open("/tmp/FritzCall_okExecute.xml", "w")
			linkP.write(content)
			linkP.close()
		root = ET.fromstring(content)
		nonce = root.find(".//Nonce").text
		realm = root.find(".//Realm").text
		secret = md5.new(config.plugins.FritzCall.username.value + ":" +
					realm + ":" +
					self.password).hexdigest()
		response = md5.new(secret + ":" + nonce).hexdigest()

		# self.debug("user %s, passwort %s", config.plugins.FritzCall.username.value, self.password)
		headers = self.header.copy()
		headers['soapaction'] = '%s#%s' % (self.service_type, self.name)
		header_clientauth = self.header_clientauth_template % (
															nonce,
															response,
															config.plugins.FritzCall.username.value,
															realm)
		data = self.envelope.strip() % ( header_clientauth,
										self._body_builder(kwargs))
		url = 'http://%s:%s%s' % (self.address, self.port, self.control_url)
		# self.debug("url: " + url + "\n" + data)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = headers,
			postdata = data).addCallback(self.parse_response, callback).addErrback(self._errorExecute, callback)

	def _errorExecute(self, error, callback):
		# text = _("FRITZ!Box - Error getting status: %s") % error.getErrorMessage()
		self.error(error)
		callback(error)

	def parse_response(self, response, callback):
		"""
		Evaluates the action-call response from a FritzBox.
		The response is a xml byte-string.
		Returns a dictionary with the received arguments-value pairs.
		The values are converted according to the given data_types.
		TODO: boolean and signed integers data-types from tr64 responses
		"""
		# self.debug("")
		if self.logger.getEffectiveLevel() == logging.DEBUG:
			linkP = open("/tmp/FritzCall_parse_response.xml", "w")
			linkP.write(response)
			linkP.close()
		result = {}
		root = ET.fromstring(response)
		errorCode = root.find(".//{urn:dslforum-org:control-1-0}errorCode")
		errorDescription = root.find(".//{urn:dslforum-org:control-1-0}errorDescription")
		# self.debug("errorCode: %s, errorDescription; %s", repr(errorCode), repr(errorDescription))
		if errorCode is not None:
			if errorDescription:
				self.error("ErrorCode: %s, errorDescription: %s", repr(errorCode), repr(errorDescription))
			else:
				self.error("ErrorCode: %s, no errorDescription", repr(errorCode))
		for argument in self.arguments.values():
			# self.debug("Argument: " + argument.name)
			try:
				value = root.find('.//%s' % argument.name).text
			except AttributeError:
				# will happen by searching for in-parameters and by
				# parsing responses with status_code != 200
				continue
			if argument.data_type.startswith('ui'):
				try:
					value = int(value)
				except ValueError:
					# should not happen
					value = None
				except TypeError:
					# raised in case that value is None. Should also not happen.
					value = None
			result[argument.name] = value
		callback(result)


class FritzActionArgument(object):
	"""Attribute class for arguments."""
	name = ''
	direction = ''
	data_type = ''

	@property
	def info(self):
		return (self.name, self.direction, self.data_type)


class FritzService(object):
	"""Attribute class for service."""
	logger = logging.getLogger("FritzCall.FritzService")
	debug = logger.debug
	info = logger.info
	warn = logger.warn
	error = logger.error
	exception = logger.exception

	def __init__(self, service_type, control_url, scpd_url):
		# self.debug("")
		self.service_type = service_type
		self.control_url = control_url
		self.scpd_url = scpd_url
		self.actions = {}
		self.name = ':'.join(service_type.split(':')[-2:])

def namespace(element):
	m = re.match(r'\{.*\}', element.tag)
	return m.group(0) if m else ''

class FritzXmlParser(object):
	"""Base class for parsing fritzbox-xml-files."""
	logger = logging.getLogger("FritzCall.FritzXmlParser")
	debug = logger.debug
	info = logger.info
	warn = logger.warn
	error = logger.error
	exception = logger.exception

	def __init__(self, address, port, filename=None, service=None, callback=None):
		"""Loads and parses an xml-file from a FritzBox."""
		# self.debug("addr: %s, port: %s, filename: %s" %(address, port, repr(filename)))
		self.service = service
		self.callback = callback
		if address is None:
			source = filename
			# self.debug("source: %s", source)
			tree = ET.parse(source)
			self.root = tree.getroot()
			self.namespace = namespace(self.root)
		else:
			self.root = None
			source = 'http://{0}:{1}/{2}'.format(address, port, filename)
			# self.debug("source: %s", source)
			getPage(source,
 				method = "GET",).addCallback(self._okInit).addErrback(self._errorInit)

	def _okInit(self, source):
		# self.debug("")
		self.root = ET.fromstring(source)
		self.namespace = namespace(self.root)
		if self.service:
			self.callback(self.service, self)
		else:
			self.callback(self)

	def _errorInit(self, error):
		self.exception(error)

	def nodename(self, name):
		#self.debug("name: %s, QName: %s" %(name, ET.QName(self.root, name).text))
		"""Extends name with the xmlns-prefix to a valid nodename."""
		found = re.match('{.*({.*}).*}(.*$)', ET.QName(self.root, name).text)
		if found:
			# self.debug("result: " + found.group(1) + found.group(2))
			return found.group(1) + found.group(2)
		else:
			return ""


class FritzDescParser(FritzXmlParser):
	"""Class for parsing desc.xml-files."""
	logger = logging.getLogger("FritzCall.FritzDescParser")

	def get_modelname(self):
		"""Returns the FritzBox model name."""
		xpath = '%s/%s' % (self.nodename('device'), self.nodename('modelName'))
		# self.debug("Xpath %s found: %s" % (xpath, self.root.find(xpath).text))
#		self.debug("Model name: " + self.root.find(xpath).text)
		return self.root.find(xpath).text

	def get_services(self):
		"""Returns a list of FritzService-objects."""
		# self.debug("")
		result = []
		nodes = self.root.iterfind(".//%s/%s" % (self.nodename('serviceList'), self.nodename('service')), namespaces={'ns': self.namespace})
		for node in nodes:
			# self.debug("service")
			result.append(FritzService(
				node.find(self.nodename('serviceType')).text,
				node.find(self.nodename('controlURL')).text,
				node.find(self.nodename('SCPDURL')).text))
		# self.debug("result: " + repr(result))
		return result


class FritzSCDPParser(FritzXmlParser):
	"""Class for parsing SCDP.xml-files"""
	logger = logging.getLogger("FritzCall.FritzXmlParser")

	def __init__(self, address, port, service, filename=None, callback=None):
		"""
		Reads and parses a SCDP.xml-file from FritzBox.
		'service' is a tuple of containing:
		(serviceType, controlURL, SCPDURL)
		'service' is a FritzService object:
		"""
		self.state_variables = {}
		# self.debug("Service: " + service.name)
		self.service = service
		if filename is None:
			# access the FritzBox
			super(FritzSCDPParser, self).__init__(address, port,
												  service.scpd_url, service=service, callback=callback)
		else:
			# for testing read the xml-data from a file
			super(FritzSCDPParser, self).__init__(None, None, filename=filename, callback=callback)

	def _read_state_variables(self):
		"""
		Reads the stateVariable information from the xml-file.
		The information we like to extract are name and dataType so we
		can assign them later on to FritzActionArgument-instances.
		Returns a dictionary: key:value = name:dataType
		"""
		nodes = self.root.iterfind('.//' + self.namespace + 'stateVariable')
		for node in nodes:
			key = node.find(self.nodename('name')).text
			value = node.find(self.nodename('dataType')).text
			self.state_variables[key] = value

	def get_actions(self, action_parameters):
		"""Returns a list of FritzAction instances."""
		# self.debug("")
		self._read_state_variables()
		actions = []
		nodes = self.root.iterfind('.//' + self.namespace + 'action')
		for node in nodes:
			action = FritzAction(self.service.service_type,
								 self.service.control_url,
								 action_parameters)
			action.name = node.find(self.nodename('name')).text
			# self.debug("node: " + action.name)
			action.arguments = self._get_arguments(node)
			actions.append(action)
		return actions

	def _get_arguments(self, action_node):
		"""
		Returns a dictionary of arguments for the given action_node.
		"""
		arguments = {}
		# self.debug(r'.//' + self.namespace + ':argumentList/' + self.namespace + ':argument')
		argument_nodes = action_node.iterfind(r'.//' + self.namespace + 'argumentList/' + self.namespace + 'argument')
		for argument_node in argument_nodes:
			# self.debug("argument")
			argument = self._get_argument(argument_node)
			arguments[argument.name] = argument
		return arguments

	def _get_argument(self, argument_node):
		"""
		Returns a FritzActionArgument instance for the given argument_node.
		"""
		# self.debug("")
		argument = FritzActionArgument()
		argument.name = argument_node.find(self.nodename('name')).text
		argument.direction = argument_node.find(self.nodename('direction')).text
		rsv = argument_node.find(self.nodename('relatedStateVariable')).text
		# TODO: track malformed xml-nodes (i.e. misspelled)
		argument.data_type = self.state_variables.get(rsv, None)
		return argument


class FritzConnection(object):
	"""
	FritzBox-Interface for status-information
	"""
	logger = logging.getLogger("FritzCall.FritzConnection")
	debug = logger.debug
	info = logger.info
	warn = logger.warn
	error = logger.error
	exception = logger.exception

	def __init__(self, address=FRITZ_IP_ADDRESS,
					   port=FRITZ_TCP_PORT,
					   user=FRITZ_USERNAME,
					   password='',
					   servicesToGet=None):
		# self.debug("")
		if password and type(password) is list:
			password = password[0]
		if user and type(user) is list:
			user = user[0]
		# The keys of the dictionary are becoming FritzAction instance
		# attributes on calling the FritzSCDPParser.get_actions() method
		# in self._read_services():
		self.action_parameters = {
			'address': address,
			'port': port,
			'user': user,
			'password': password
		}
		self.address = address
		self.port = port
		self.servicesToGet = servicesToGet
		self.modelname = None
		self.services = {}
		self._read_descriptions(password)

	def _read_descriptions(self, password):
		"""
		Read and evaluate the igddesc.xml file
		and the tr64desc.xml file if a password is given.
		"""
		# self.debug("")
		descfiles = [FRITZ_IGD_DESC_FILE]
		if password:
			descfiles.append(FRITZ_TR64_DESC_FILE)
		for descfile in descfiles:
			# self.debug("descfile: %s", descfile)
			try:
				FritzDescParser(self.address, self.port, descfile, callback=self._read_descriptions_cb)
			except IOError:
				# failed to load a resource. Can happen on customized models
				# missing the igddesc.xml file.
				# It's save to ignore this error.
				self.error("IOError")
				continue

	def _read_descriptions_cb(self, parser):
		# self.debug("")
		if not self.modelname:
			self.modelname = parser.get_modelname()
		# self.debug("parser")
		services = parser.get_services()
		self._read_services(services)

	def _read_services(self, services):
		"""Get actions from services."""
		# self.debug("")
		for service in services:
			# self.debug("Service: " + service.name + " Control URL: " + service.control_url+ " SCPD URL: " + service.scpd_url)
			# self.debug("servicesToGet: " + repr(self.servicesToGet))
			if self.servicesToGet and service.name in self.servicesToGet:
				self.debug("Get service: %s", service.name)
				FritzSCDPParser(self.address, self.port, service, callback=self._read_services_cb)

	def _read_services_cb(self, service, parser):
		# self.debug("Service: " + service.name)
		actions = parser.get_actions(self.action_parameters)
		service.actions = {action.name: action for action in actions}
		self.services[service.name] = service

	# @property
	def actionnames(self):
		"""
		Returns a alphabetical sorted list of tuples with all known
		service- and action-names.
		"""
		actions = []
		for service_name in sorted(self.services.keys()):
			action_names = self.services[service_name].actions.keys()
			for action_name in sorted(action_names):
				actions.append((service_name, action_name))
		return actions

	def _get_action(self, service_name, action_name):
		"""
		Returns an action-object (an instance of FritzAction) with the
		given action_name from the given service.
		Raises a ServiceError-Exeption in case of an unknown
		service_name and an ActionError in case of an unknown
		action_name.
		"""
		# self.debug("")
		try:
			service = self.services[service_name]
		except KeyError:
			raise ServiceError('Unknown Service: ' + service_name)
		try:
			action = service.actions[action_name]
		except KeyError:
			raise ActionError('Unknown Action: ' + action_name)
		return action

	def get_action_arguments(self, service_name, action_name):
		"""
		Returns a list of tuples with all known arguments for the given
		service- and action-name combination. The tuples contain the
		argument-name, direction and data_type.
		"""
		# self.debug("")
		action = self._get_action(service_name, action_name)
		return action.info

	def call_action(self, callback, service_name, action_name, **kwargs):
		"""
		Executes the given action. Raise a KeyError on unkown actions.
		service_name can end with an identifier ':n' (with n as an
		integer) to differentiate between different services with the
		same name, like WLANConfiguration:1 or WLANConfiguration:2. In
		case the service_name does not end with an identifier the id
		':1' will get added by default.
		"""
		# self.debug("")
		if not ':' in service_name:
			service_name += ':1'
		action = self._get_action(service_name, action_name)
		action.execute(callback, **kwargs)

	def reconnect(self):
		"""
		Terminate the connection and reconnects with a new ip.
		Will raise a KeyError if this command is unknown (by any means).
		"""
		self.call_action(None, 'WANIPConnection', 'ForceTermination')
