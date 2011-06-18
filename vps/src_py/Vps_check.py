# -*- coding: utf-8 -*-

from . import _
from enigma import eTimer, eConsoleAppContainer, getBestPlayableServiceReference, eServiceReference, eEPGCache
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Tools.XMLTools import stringToXML
from Tools import Directories
from time import time
from Vps import vps_exe
import NavigationInstance
from xml.etree.cElementTree import parse as xml_parse

check_pdc_interval_available = 3600*24*30*6
check_pdc_interval_unavailable = 3600*24*30*2

# Prüfen, ob PDC-Descriptor vorhanden ist.
class VPS_check_PDC(Screen):
	skin = """<screen name="vpsCheck" position="center,center" size="540,110" title="VPS-Plugin">
		<widget source="infotext" render="Label" position="10,10" size="520,90" font="Regular;21" valign="center" halign="center" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
	</screen>"""
	
	def __init__(self, session, service, timer_entry):
		Screen.__init__(self, session)
		
		self["infotext"] = StaticText(_("VPS-Plugin checks if the channel supports VPS for manual timers ..."))
		
		self["actions"] = ActionMap(["OkCancelActions"], 
			{
				"cancel": self.finish,
			}, -1)
		
		if service is None or service.ref.getPath():
			self.close()
			return

		self.service = service.ref
		self.program = eConsoleAppContainer()
		self.program.dataAvail.append(self.program_dataAvail)
		self.program.appClosed.append(self.program_closed)
		self.check = eTimer()
		self.check.callback.append(self.doCheck)
		self.simulate_recordService = None
		self.last_serviceref = None
		self.calledfinished = False
		
		self.checked_services = { }
		self.has_pdc = -1
		self.timer_entry = timer_entry
		
		if self.service and self.service.flags & eServiceReference.isGroup:
			self.service = getBestPlayableServiceReference(self.service, eServiceReference())
		self.service_ref_str = self.service.toString()
		
		self.load_pdc()
		
		try:
			if self.checked_services[self.service_ref_str]["has_pdc"] == True:
				self.has_pdc = 1
			else:
				self.has_pdc = 0
		except:
			self.has_pdc = -1
		
		self.check.start(100, True)
		
	def load_pdc(self):
		try:
			doc = xml_parse(Directories.resolveFilename(Directories.SCOPE_CONFIG, "vps.xml"))
			xmlroot = doc.getroot()
			
			if xmlroot is not None:
				for xml in xmlroot.findall("channel"):
					serviceref = xml.get("serviceref").encode("utf-8")
					has_pdc = xml.get("has_pdc")
					last_check = xml.get("last_check")
					self.checked_services[serviceref] = { }
					self.checked_services[serviceref]["last_check"] = int(last_check)
					if has_pdc == "1":
						self.checked_services[serviceref]["has_pdc"] = True
					else:
						self.checked_services[serviceref]["has_pdc"] = False
		except:
			pass
	
	def save_pdc(self):
		list = []
		list.append('<?xml version="1.0" ?>\n')
		list.append('<pdc_available>\n')
		
		now = time()
		for ch in self.checked_services:
			if self.checked_services[ch]["last_check"] < (now - check_pdc_interval_available):
				continue
			list.append('<channel')
			list.append(' serviceref="' + stringToXML(ch) + '"')
			list.append(' has_pdc="' + str(int(self.checked_services[ch]["has_pdc"])) + '"')
			list.append(' last_check="' + str(int(self.checked_services[ch]["last_check"])) + '"')
			list.append('></channel>\n')
		
		list.append('</pdc_available>\n')
		
		file = open(Directories.resolveFilename(Directories.SCOPE_CONFIG, "vps.xml"), "w")
		for x in list:
			file.write(x)
		file.close()
	
	def doCheck(self):
		if (self.has_pdc == 1 and self.checked_services[self.service_ref_str]["last_check"] > (time() - check_pdc_interval_available)) or (self.has_pdc == 0 and self.checked_services[self.service_ref_str]["last_check"] > (time() - check_pdc_interval_unavailable)):
			self.finish()
			return
		
		self.demux = -1
		if self.simulate_recordService is None:
			self.simulate_recordService = NavigationInstance.instance.recordService(self.service, True)
			if self.simulate_recordService:
				res = self.simulate_recordService.start()
				if res != 0 and res != -1:
					# Fehler aufgetreten (kein Tuner frei?)
					NavigationInstance.instance.stopRecordService(self.simulate_recordService)
					self.simulate_recordService = None
					
					if self.last_serviceref is not None:
						self.finish()
						return
					else:
						cur_ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
						if cur_ref and not cur_ref.getPath():
							self.last_serviceref = cur_ref
							NavigationInstance.instance.playService(None)
							self.check.start(1500, True)
							return
				else: # hat geklappt
					self.check.start(1000, True)
					return
		else:
			stream = self.simulate_recordService.stream()
			if stream:
				streamdata = stream.getStreamingData()
				if (streamdata and ('demux' in streamdata)):
					self.demux = streamdata['demux']
			if self.demux != -1:
				self.startProgram()
				return
		
		if self.simulate_recordService is not None:
			NavigationInstance.instance.stopRecordService(self.simulate_recordService)
			self.simulate_recordService = None
		if self.last_serviceref is not None:
			NavigationInstance.instance.playService(self.last_serviceref)
		self.finish()
	
	def startProgram(self):
		sid = self.service.getData(1)
		tsid = self.service.getData(2)
		onid = self.service.getData(3)
		demux = "/dev/dvb/adapter0/demux" + str(self.demux)
		
		cmd = vps_exe + " "+ demux +" 10 "+ str(onid) +" "+ str(tsid) +" "+ str(sid) +" 0 0"
		self.program.execute(cmd)
	
	def program_closed(self, retval):
		if not self.calledfinished:
			self.setServicePDC(-1)
			self.finish()
	
	def program_dataAvail(self, str):
		lines = str.split("\n")
		for line in lines:
			if line == "PDC_AVAILABLE" and not self.calledfinished:
				self.calledfinished = True
				self.setServicePDC(1)
				self.finish()
				
			elif line == "NO_PDC_AVAILABLE" and not self.calledfinished:
				self.calledfinished = True
				self.setServicePDC(0)
				self.finish()
	
	def setServicePDC(self, state):
		if state == -1:
			self.has_pdc = -1
			try:
				del self.checked_services[self.service_ref_str]
			except:
				pass
		elif state == 1:
			self.has_pdc = 1
			self.checked_services[self.service_ref_str] = { }
			self.checked_services[self.service_ref_str]["has_pdc"] = True
			self.checked_services[self.service_ref_str]["last_check"] = time()
		elif state == 0:
			self.has_pdc = 0
			self.checked_services[self.service_ref_str] = { }
			self.checked_services[self.service_ref_str]["has_pdc"] = False
			self.checked_services[self.service_ref_str]["last_check"] = time()
		
		self.save_pdc()
		
	def finish(self):
		self.calledfinished = True
		self.check.stop()
		
		if self.simulate_recordService is not None:
			NavigationInstance.instance.stopRecordService(self.simulate_recordService)
			self.simulate_recordService = None
		
		if self.last_serviceref is not None:
			NavigationInstance.instance.playService(self.last_serviceref)
		
		if self.has_pdc == 1: # PDC vorhanden
			self.close()
		elif self.has_pdc == 0: # kein PDC
			#nachfragen
			self.session.openWithCallback(self.finish_callback, MessageBox, _("The selected channel doesn't support VPS for manually programmed timers!\n Do you really want to enable VPS?"), default = False)
		else: # konnte nicht ermitteln
			self.session.openWithCallback(self.finish_callback, MessageBox, _("The VPS-Plugin couldn't check if the selected channel supports VPS for manually programmed timers!\n Do you really want to enable VPS?"), default = False)
	
	
	def finish_callback(self, result):
		if not result:
			self.timer_entry.timerentry_vpsplugin_enabled.value = False
			self.timer_entry.createSetup("config")
		
		self.close()
			