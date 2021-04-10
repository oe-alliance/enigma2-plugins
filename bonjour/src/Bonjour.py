# -*- coding: utf-8 -*-
from __future__ import print_function
from enigma import eConsoleAppContainer, eTimer
from xml.etree.cElementTree import parse as cet_parse
from xml.etree.ElementTree import ParseError
from os import path, listdir
from os import remove as os_remove, fsync

import six


class Bonjour:
	AVAHI_SERVICES_DIR = '/etc/avahi/services/'
	AVAHI_START_SCRIPT = '/etc/init.d/avahi-daemon'

	def __init__(self):
		self.services = []
		self.files = {}
		self.reloadConfig()

	def __createServiceConfig(self, service):
		lines = [
				'<?xml version="1.0" standalone="no"?><!--*-nxml-*-->\n',
				'<!DOCTYPE service-group SYSTEM "avahi-service.dtd">\n',
				'<!-- This file has been created by enigma2-plugin-extensions-bonjour -->\n',
				'<service-group>\n',
				'\t<name replace-wildcards="yes">%s</name>\n' % (service['name']),
				'\t<service>\n',
				'\t\t<type>%s</type>\n' % (service['type']),
				'\t\t<port>%s</port>\n' % (service['port'])
				]
		text = service.get('text', None)
		if text:
			if isinstance(text, (six.string_types)):
				lines.append('\t\t<txt-record>%s</txt-record>\n' % (text))
			else:
				for txt in text:
					lines.append('\t\t<txt-record>%s</txt-record>\n' % (txt))
		lines.extend([
					'\t</service>\n',
					'</service-group>\n'
					])

		return lines

	def txtFromDict(self, dict):
		if not dict:
			return '\0'
		parts = []
		for name, value in six.iteritems(dict):
			if value is None:
				item = name
			else:
				item = '%s=%s' % (name, value)
			if len(item) > 255:
				item = item[:255]
			parts.append(item)
		return parts

	def __writeService(self, service):
		print("[Bonjour.__writeService] Creating service file '%s'" % (service['file']))
		if 'type' in service and 'port' in service and 'file' in service:
			filepath = "%s%s" % (self.AVAHI_SERVICES_DIR, service['file'])
			try:
				file = open(filepath, 'w')
				file.writelines(self.__createServiceConfig(service))
				file.flush()
				fsync(file.fileno())
				file.close()
				return True
			except IOError:
				pass

		print("[Bonjour.__writeService] Cannot create service file '%s'" % (service['file']))
		return False

	def __deleteService(self, protocol):
		filepath = "%s%s.service" % (self.AVAHI_SERVICES_DIR, protocol)
		if path.exists(filepath):

			os_remove(filepath)
			return True

		return False

	def __parse(self, file):
		print("[Bonjour.__parse] parsing %s%s" % (self.AVAHI_SERVICES_DIR, file))
		try:
			config = cet_parse(self.AVAHI_SERVICES_DIR + file).getroot()
		except ParseError: #parsing failed, skip the file
			return

		name = config.find('name').text

		service = config.find('service')
		type = service.find('type').text
		port = service.find('port').text
		text = service.findall('txt-record')
		textList = []
		if text != None:
			for txt in text:
				textList.append(txt.text)

		service = self.buildServiceFull(file, name, type, port, textList)
		self.registerService(service)

	def __removeServiceFromList(self, service):
		oldservices = self.services
		self.services = []

		for s in oldservices:
			if s['file'] != service['file']:
				self.services.append(s)
				self.files[s['file']] = len(self.services) - 1

		self.files[service['file']] = None


	def reloadConfig(self):
		self.services = []
		self.files = {}
		if path.exists(self.AVAHI_SERVICES_DIR):
			print("[Bonjour.reloadConfig] reloading config")
			service_files = filter(lambda x: x.endswith('.service'), listdir(self.AVAHI_SERVICES_DIR))
			for file in service_files:
				self.__parse(file)

		self.registerDefaultServices()


	def registerService(self, service, replace=False):
		print("[Bonjour.registerService] %s" % service)

		if 'type' in service and 'port' in service and 'file' in service:
			if (service['file'] not in self.files) or replace:
				filepath = "%s%s" % (self.AVAHI_SERVICES_DIR, service['file'])
				if not self.__writeService(service):
					return False

				if replace and service['file'] in self.files:
					self.__removeServiceFromList(service)


				self.services.append(service)
				self.files[service['file']] = len(self.services) - 1

				return True

		else:
			print("[Bonjour.registerService] Missing port or type definition in %s%s" % (self.AVAHI_SERVICES_DIR, service['file']))
			return False


	def updateService(self, service):
		if 'type' in service and 'port' in service and 'file' in service:

			filepath = "%s%s" % (self.AVAHI_SERVICES_DIR, service['file'])
			if not path.exists(filepath):
				print("[Bonjour.updateService] Cannot update non-existent service file '%s'" % (service['file']))
				return False

			else:
				if not self.__writeService(service):
					print("[Bonjour.updateService] Cannot write service file '%s'" % (service['file']))
					return False

		return True

	def unregisterService(self, protocol):
		if self.__deleteService(protocol):
			self.reloadConfig()


	def buildService(self, protocol, port, text=[], udp=False):
		file = "%s.service" % protocol

		type = "_%s._tcp" % protocol
		if udp:
			type = "_%s._udp" % protocol

		name = "%h "
		name += protocol.upper()

		return {
				'file': file,
				'name': name,
				'type': type,
				'port': port,
				'text': text
				}

	def buildServiceFull(self, file, name, type, port, text=[], udp=False):
		return {
				'file': file,
				'name': name,
				'type': type,
				'port': port,
				'text': text
				}

	def registerDefaultServices(self):
		print("[Bonjour.registerDefaultServices] called")
		service = self.buildService('ftp', '21')
		filepath = "%s%s" % (self.AVAHI_SERVICES_DIR, service['file'])
		if not path.exists(filepath):
			self.registerService(service)

		service = self.buildService('ssh', '22')
		filepath = "%s%s" % (self.AVAHI_SERVICES_DIR, service['file'])
		if not path.exists(filepath):
			self.registerService(service)

		service = self.buildService('sftp-ssh', '22')
		filepath = "%s%s" % (self.AVAHI_SERVICES_DIR, service['file'])
		if not path.exists(filepath):
			self.registerService(service)

		service = self.buildService('smb', '139')
		filepath = "%s%s" % (self.AVAHI_SERVICES_DIR, service['file'])
		if not path.exists(filepath):
			self.registerService(service)

bonjour = Bonjour()
