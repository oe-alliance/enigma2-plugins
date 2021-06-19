# -*- coding: UTF-8 -*-

from __future__ import print_function
from Components.ActionMap import ActionMap
from Components.Sensors import sensors
from Components.Sources.Sensor import SensorSource
from Components.Sources.StaticText import StaticText
from Components.Sources.Progress import Progress
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap, MultiPixmap
from Components.Label import MultiColorLabel
from Components.config import config, getConfigListEntry, ConfigSubsection, ConfigBoolean, ConfigOnOff, ConfigInteger, ConfigSlider, ConfigText, ConfigSelection, ConfigSelectionNumber, ConfigNothing, ConfigFloat, ConfigText
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
from enigma import eTimer, eListbox, gFont, eListboxPythonMultiContent, \
	RT_HALIGN_LEFT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP, eRect, eTimer

from socket import *
import xml.dom.minidom

from Components.Language import language
import os
import gettext

PluginLanguageDomain = "EIBox"
PluginLanguagePath = "Extensions/EIBox/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[" + PluginLanguageDomain + "] fallback to default translation for " + txt)
		return gettext.gettext(txt)


language.addCallback(localeInit())

config.eib = ConfigSubsection()
config.eib.xmlfile = ConfigText(default="design.xml")
config.eib.host = ConfigText(default="")
config.eib.port = ConfigInteger(default="1028")
config.eib.debug = ConfigBoolean(default=True)
config.eib.refresh = ConfigInteger(default="1000")

EIB_SWITCH, EIB_MULTISWITCH, EIB_DIMMER, EIB_GOTO, EIB_THERMO, EIB_TEXT = ("switch", "multi", "dimmer", "goto", "thermostat", "text")

file_prefix = resolveFilename(SCOPE_PLUGINS, 'Extensions/EIBox/')
img_prefix = file_prefix + 'images/'

up_down_descriptions = {False: _("up"), True: _("down")}


class ConfigUpDown(ConfigBoolean):
	def __init__(self, default=False):
		ConfigBoolean.__init__(self, default=default, descriptions=up_down_descriptions)


goto_descriptions = {False: "", True: ""}


class ConfigGoto(ConfigBoolean):
	def __init__(self, default=False):
		ConfigBoolean.__init__(self, default=default, descriptions=goto_descriptions)


class ConfigEIBText(ConfigText):
	def __init__(self, default="", fixed_size=True, visible_width=False):
		ConfigText.__init__(self, default, fixed_size, visible_width)

	def onSelect(self, session):
		self.allmarked = (self.value != "")


class EIBObject(object):
	def __init__(self, order, object_id, object_type, label, position, img=None, custom_img=[], custom_values=[], textformat=None, readonly=False):
		self.order = order
		self.object_id = object_id
		self.object_type = object_type
		self.label = label
		self.position = position
		self.img = img
		self.custom_img = custom_img
		self.custom_values = custom_values
		self.textformat = textformat
		self.readonly = readonly
		self.config_element = None
		self.createConfigElement()
		self.multiswitch_dict = {}

	def createConfigElement(self):
		if self.object_type == EIB_SWITCH and self.img in ("light", "outlet", "fan", "pump"):
			self.config_element = ConfigOnOff()
		elif self.object_type == EIB_SWITCH and self.img == "blinds":
			self.config_element = ConfigUpDown()
		elif self.object_type == EIB_SWITCH:
			self.config_element = ConfigBoolean()
		elif self.object_type == EIB_MULTISWITCH:
			choiceslist = []
			for choice in self.custom_values:
				choiceslist.append(choice)
			self.config_element = ConfigSelection(choices=choiceslist)
		elif self.object_type == EIB_DIMMER:
			self.config_element = ConfigSelectionNumber(0, 255, 1)
			#self.config_element = ConfigSlider(increment = 10, limits=(0,255))
		elif self.object_type == EIB_THERMO:
			self.config_element = ConfigFloat(default=[0, 0], limits=[(-31, +31), (0, 99)])
		elif self.object_type == EIB_GOTO:
			self.config_element = ConfigGoto()
		elif self.object_type == EIB_TEXT:
			self.config_element = ConfigEIBText()
		else:
			print("[createConfigElement] couldn't create config_element for", self.getInfo())

	def getValue(self):
		if self.config_element:
			if self.object_type == EIB_THERMO:
				val = self.config_element.getValue()
				return "%d.%d" % (val[0], val[1])
			else:
				return self.config_element.getValue()

	def getText(self):
		if self.config_element:
			if self.object_type == EIB_THERMO:
				return str(self.value + "°C")
			elif self.object_type == EIB_TEXT:
				return str(self.textformat.replace("$1", str(self.value)))
			else:
				return str(self.value)

	def getPos(self, offset=[0, 0]):
		x = self.position[0] - offset[0]
		y = self.position[1] - offset[1]
		return "%d,%d" % (x, y)

	def setValue(self, val):
		if self.config_element:
			if self.object_type == EIB_SWITCH:
				if val == "off" or val == "down" or val == 0 or val == False:
					self.config_element.setValue(False)
				if val == "on" or val == "up" or val == 1 or val == True:
					self.config_element.setValue(True)
			else:
				try:
					if self.object_type == EIB_THERMO:
						val = val.split('.')
						if len(val) == 1:
							val.append(0)
						self.config_element.setValue([int(val[0]), int(val[1])])
					elif self.object_type in (EIB_TEXT, EIB_MULTISWITCH):
						self.config_element.setValue(str(val))
					else:
						self.config_element.setValue(int(val))
				except ValueError:
					print("[setValue] Error setting", val, self.getInfo())
					return
			if config.eib.debug.value:
				print("[setValue]", self.object_id, ":=", val, "before:", self.config_element.getValue())
		else:
			print("[setValue] error: no config_element", self.getInfo())

	def getInfo(self):
		return "[EIBOject] order=%d, id=%s, type=%s, label=%s, position=(%d,%d), img=%s, custom_img=%s, custom_values=%s, textformat=%s, readonly=%s, config_element=%s, value=%s" % (self.order, self.object_id, str(self.object_type), self.label, self.position[0], self.position[1], str(self.img), str(self.custom_img), str(self.custom_values), str(self.textformat), str(self.readonly), str(self.config_element), self.value)

	def getKNXvalue(self):
		value = self.value
		if isinstance(value, bool) and value == True:
			return "on"
		elif isinstance(value, bool) and value == False:
			return "off"
		else:
			return str(value)

	value = property(getValue, setValue)


class EIBObjects(object):
	def __init__(self, zone_id, zone_name, zone_img):
		self.ids = {}
		self.cfg = {}
		self.zone_id = zone_id
		self.zone_name = zone_name
		self.zone_img = zone_img

	def by_id(self, x): return self.ids[x]
	def by_cfg(self, x): return self.cfg[x]

	def append(self, x):
		self.ids[x.object_id] = x
		self.cfg[x.config_element] = x

	def EIBwriteSingle(self, EIBObject):
		ret = True
		if not EIBObject.readonly:
			query = '<write><object id="%s" value="%s"/></write>\n\x04' % (EIBObject.object_id, EIBObject.getKNXvalue())
			ret = self.sendKNX(query)
		return ret

	def EIBreadSingle(self, EIBObject):
		query = '<read><object id="%s" /></read>\n\x04' % EIBObject.object_id
		return self.sendKNX(query, self.parseSingleRead, EIBObject)

	def EIBreadAll(self):
		persist_request_cmd = '<read><objects>'
		for EIBObject in self.ids.itervalues():
			if EIBObject.object_type != EIB_GOTO:
				persist_request_cmd += '<object id="%s"/>' % EIBObject.object_id
		persist_request_cmd += '</objects></read>\n\x04'
		return self.sendKNX(persist_request_cmd, self.parseMultiRead)

	def sendKNX(self, query, callback=None, user_args=None):
		try:
			knx = socket(AF_INET, SOCK_STREAM)
			host = config.eib.host.getValue()
			port = int(config.eib.port.getValue())
			knx.connect((host, port))
			knx.settimeout(2)
			ret = knx.send(query)
			if config.eib.debug.value:
				print("[sendKNX]", query, ret)

			knxdata = knx.recv(1024)
			while not knxdata.endswith('\n\x04'):
				knxdata += knx.recv(1024)
			knx.close()
			if callback:
				callback(knxdata[:-1], user_args)
			return True
		except timeout:
			print(("[sendKNX] socket timeout with linknx server %s:%d") % (host, port))
		except error:
			print(("[sendKNX] can't connect to linknx server %s:%d") % (host, port))
		return False

	def parseSingleRead(self, knxdata, EIBObject):
		if config.eib.debug.value:
			print("[parseSingleRead]", knxdata)
		try:
			dom = xml.dom.minidom.parseString(knxdata)
			if dom.childNodes[0].getAttribute("status") == "success":
				subnode = dom.childNodes[0].childNodes[0]
				if subnode.nodeType == xml.dom.minidom.Text.nodeType:
					value = subnode.nodeValue
					if config.eib.debug.value:
						print("[parseSingleRead] value=", value)
					try:
						EIBObject.value = str(value)
					except KeyError:
						print("[parseSingleRead] KeyError exception")
					return
			print("[parseSingleRead] XML parser error parseSingleRead failed")
		except xml.parsers.expat.ExpatError as ValueError:
			print("[parseSingleRead] XML parser error parseSingleRead DOM error")

	def parseMultiRead(self, knxdata, user_args):
		if config.eib.debug.value:
			print("[parseMultiRead]", knxdata)
		try:
			dom = xml.dom.minidom.parseString(knxdata)
			for node in dom.childNodes[0].childNodes:
				if node.nodeType == xml.dom.minidom.Element.nodeType:
				    if node.tagName == 'objects':
					for subnode in node.childNodes:
					    if subnode.nodeType == xml.dom.minidom.Element.nodeType:
						if subnode.tagName == 'object':
						    i = 0
						    object_id = None
						    value = None
						    while i < subnode.attributes.length:
						      item = subnode.attributes.item(i)
						      key = item.name.encode("utf-8")
						      if key == "id":
							object_id = item.nodeValue
						      elif key == "value":
							value = item.nodeValue
						      i += 1
						    if object_id and value != None and object_id in self.ids:
							  EIBObject = self.ids[object_id]
							  EIBObject.value = value
							  if config.eib.debug.value:
								print("[parseMultiRead]", EIBObject.object_id, " := ", EIBObject.value)
					            elif config.eib.debug.value:
							  print("[parseMultiRead] couldn't parse persistence object", object_id, value)
		except xml.parsers.expat.ExpatError:
			print("[parseMultiRead] XML parser error")

	def __iter__(self):
		list = self.ids.itervalues()
		return iter(sorted(list, key=lambda EIBObject: EIBObject.order))


class EIBoxZoneScreen(Screen, ConfigListScreen):

	def __init__(self, session, EIB_objects):
		skin = """
		<screen position="center,center" size="550,450" title="E.I.B.ox" >
			<widget name="config" position="10,420" size="530,26" zPosition="1" transparent="1" scrollbarMode="showNever" />
			<ePixmap pixmap="%s" position="0,0" size="550,400" zPosition="-1" alphatest="on" />\n""" % (img_prefix + EIB_objects.zone_img)

		offset = [12, 10] # fix up browser css spacing
		iconsize = [32, 32]

		self.setup_title = "E.I.B.ox"

		self.EIB_objects = EIB_objects
		for EIB_object in self.EIB_objects:
			if EIB_object.object_type == EIB_GOTO:
				pixmap_src = (img_prefix + 'goto' + EIB_object.img.capitalize() + '.png')
				skin += '\t\t\t<widget name="%s" pixmap="%s" position="%s" size="32,32" transparent="1" alphatest="on" borderColor="#004679" zPosition="1" />\n' % (EIB_object.object_id, pixmap_src, EIB_object.getPos(offset))
				self[EIB_object.object_id] = Pixmap()

			elif EIB_object.object_type in (EIB_SWITCH, EIB_MULTISWITCH, EIB_DIMMER):
				if EIB_object.object_type == EIB_DIMMER or EIB_object.img == "light":
					pixmaps_sources = ['light_off.png', 'light_on.png']
				elif EIB_object.img == "blinds":
					pixmaps_sources = ['blinds_up.png', 'blinds_down.png']
				elif EIB_object.img == "outlet":
					pixmaps_sources = ['outlet_off.png', 'outlet_on.png']
				elif EIB_object.img == "fan":
					pixmaps_sources = ['fan_off.png', 'fan_on.png']
				elif EIB_object.img == "pump":
					pixmaps_sources = ['pump_off.png', 'pump_on.png']
				else:
					pixmaps_sources = list(EIB_object.custom_img)

				for idx, filename in enumerate(pixmaps_sources):
					  pixmaps_sources[idx] = img_prefix + filename
				pixmaps_string = ','.join(pixmaps_sources)
				skin += '\t\t\t<widget name="%s" pixmaps="%s" position="%s" size="32,32" transparent="1" alphatest="on" borderColor="#004679" zPosition="1" />\n' % (EIB_object.object_id, pixmaps_string, EIB_object.getPos(offset))
				self[EIB_object.object_id] = MultiPixmap()

				if EIB_object.object_type == EIB_DIMMER:
					skin += '\t\t\t<widget source="%s_progress" render="Progress" pixmap="skin_default/progress_small.png" position="%s" size="32,5" backgroundColor="#4f74BB" zPosition="1" />\n' % (EIB_object.object_id, EIB_object.getPos([offset[0], offset[1] - iconsize[1]]))
					self[EIB_object.object_id + "_progress"] = Progress()
					self[EIB_object.object_id + "_progress"].range = 255

			elif EIB_object.object_type in (EIB_THERMO, EIB_TEXT):
				skin += '\t\t\t<widget name="%s" position="%s" size="120,20" font="Regular;14" halign="left" valign="center" foregroundColors="#000000,#0000FF" transparent="1" zPosition="1" />\n' % (EIB_object.object_id, EIB_object.getPos(offset))
				self[EIB_object.object_id] = MultiColorLabel()
		skin += """
		</screen>"""
		if config.eib.debug.value:
			print(skin)

		self.skin = skin
		Screen.__init__(self, session)
		self.initConfigList()
		ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
		self.onChangedEntry = []

		self["actions"] = ActionMap(["SetupActions", "OkCancelActions", "ColorActions", "DirectionActions"],
		{
			"up": self.keyUp,
			"upUp": self.keyPass,
			"upRepeated": self.keyUp,
			"down": self.keyDown,
			"downUp": self.keyPass,
			"downRepeated": self.keyDown,
			"leftRepeated": self.keyLeftRepeated,
			"rightRepeated": self.keyRightRepeated,
			"cancel": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyOk,
			"ok": self.keyOk
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)

	def handleInputHelpers(self):
		pass

	def keyPass(self):
		pass

	def keyUp(self):
		self.moveBorder(self["config"].instance.moveUp)

	def keyDown(self):
		self.moveBorder(self["config"].instance.moveDown)

	def keyOk(self):
		EIB_object = self.getCurrentObj()
		if EIB_object and EIB_object.object_type == EIB_DIMMER:
			if EIB_object.value < 128:
				EIB_object.value = 255
			else:
				EIB_object.value = 0
			self.changedEntry()
			self["config"].invalidateCurrent()
		else:
			self.keyRight()

	def keyRight(self):
		ConfigListScreen.keyRight(self)

	def keyRightRepeated(self):
		EIB_object = self.getCurrentObj()
		if EIB_object and EIB_object.object_type == EIB_DIMMER:
			value = EIB_object.getValue()
			if value < 255 - 15:
				EIB_object.value += 15
			else:
				EIB_object.value = 255
			self.changedEntry()
			self["config"].invalidateCurrent()

	def keyLeftRepeated(self):
		EIB_object = self.getCurrentObj()
		if EIB_object and EIB_object.object_type == EIB_DIMMER:
			value = EIB_object.getValue()
			if value > 15:
				EIB_object.value -= 15
			else:
				EIB_object.value = 0
			self.changedEntry()
			self["config"].invalidateCurrent()

	def keyCancel(self):
		self.exit()

	def layoutFinished(self):
		self.moveBorder()
		self.refreshObjects()
		self.refresh_timer = eTimer()
		self.refresh_timer.callback.append(self.refreshObjects)
		interval = config.eib.refresh.value
		if interval >= 500:
			self.refresh_timer.start(interval)

	def getCurrentObj(self):
		current = self["config"].getCurrent()
		if current:
			return self.EIB_objects.by_cfg(current[1])
		else:
			return None

	def moveBorder(self, direction=None):
		if direction != None:
			for EIB_object in self.EIB_objects:
				if EIB_object.object_type in (EIB_SWITCH, EIB_DIMMER, EIB_GOTO, EIB_MULTISWITCH):
					self[EIB_object.object_id].instance.setBorderWidth(0)
				elif EIB_object.object_type in (EIB_THERMO, EIB_TEXT):
					self[EIB_object.object_id].setForegroundColorNum(0)
			self["config"].instance.moveSelection(direction)
		current = self["config"].getCurrent()
		if current:
			EIB_object = self.EIB_objects.by_cfg(current[1])
			if EIB_object.object_type in (EIB_SWITCH, EIB_DIMMER, EIB_GOTO, EIB_MULTISWITCH):
				self[EIB_object.object_id].instance.setBorderWidth(5)
			elif EIB_object.object_type in (EIB_THERMO, EIB_TEXT):
					self[EIB_object.object_id].setForegroundColorNum(1)

	def refreshObjects(self):
		status = self.EIB_objects.EIBreadAll()
		for EIB_object in self.EIB_objects:
			self.updateObject(EIB_object)
		self.setWindowTitle(status)

	def setWindowTitle(self, status):
		self.setup_title = "E.I.B.ox %s " % self.EIB_objects.zone_name
		if status == True:
			self.setup_title += _("(online)")
		else:
			self.setup_title += _("(offline!)")
		self.setTitle(self.setup_title)

	def updateObject(self, EIB_object):
		if EIB_object.object_type in (EIB_THERMO, EIB_TEXT):
			self.updateLabel(EIB_object)
		else:
			self.updateIcon(EIB_object)

	def updateLabel(self, EIB_object):
		if config.eib.debug.value:
			print("[refreshObjects]", EIB_object.getInfo(), EIB_object.getText())
		self[EIB_object.object_id].setText(EIB_object.getText())

	def updateIcon(self, EIB_object):
		if config.eib.debug.value:
			print("[updateIcon]", EIB_object.getInfo())
		if EIB_object.object_type == EIB_MULTISWITCH:
		        if EIB_object.value in EIB_object.custom_values:
				idx = int(EIB_object.custom_values.index(EIB_object.value))
				if len(EIB_object.custom_img) > idx:
					self[EIB_object.object_id].setPixmapNum(idx)
			return
		if EIB_object.object_type not in (EIB_SWITCH, EIB_DIMMER):
			return
		if isinstance(EIB_object.value, bool) or EIB_object.value == 0:
			self[EIB_object.object_id].setPixmapNum(int(EIB_object.value))
		elif isinstance(EIB_object.value, int) and EIB_object.value > 0:
			self[EIB_object.object_id].setPixmapNum(1)
		if EIB_object.object_type == EIB_DIMMER:
			self[EIB_object.object_id + "_progress"].value = EIB_object.value

	def initConfigList(self):
		self.list = []
		for EIB_object in self.EIB_objects:
			self.list.append(getConfigListEntry(EIB_object.label, EIB_object.config_element))

	def changedEntry(self):
		current = self["config"].getCurrent()
		if current:
			EIB_object = self.EIB_objects.by_cfg(current[1])
			if EIB_object.object_type == EIB_GOTO:
				self.exit(EIB_object.object_id)
			else:
				if not EIB_object.readonly:
					self.EIB_objects.EIBwriteSingle(EIB_object)
				status = self.EIB_objects.EIBreadSingle(EIB_object)
				self.updateObject(EIB_object)
				self.setWindowTitle(status)
		for summaryWatcher in self.onChangedEntry:
			summaryWatcher()

	def getCurrentEntry(self):
		return str(self["config"].getCurrent()[0])

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		from Screens.Setup import SetupSummary
		return SetupSummary

	def exit(self, gotoZone=None):
		self.refresh_timer.callback.remove(self.refreshObjects)
		self.close(gotoZone)


class EIBox(Screen, ConfigListScreen):
	skin = """
		<screen position="center,center" size="570,420" title="E.I.B.ox" >
		</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions"],
		{
			"cancel": self.close,
			"red": self.close
		}, -1)

		self.gotoZone = None
		self.EIB_zones = {}
		self.onShown.append(self.onFirstShown)

	def ZoneScreenCB(self, gotoZone=None):
		if not gotoZone:
			self.close()
		else:
			self.gotoZone = gotoZone
			self.displayZone()

	def onFirstShown(self):
		self.onShown.remove(self.onFirstShown)
		self.loadXML(resolveFilename(SCOPE_PLUGINS, file_prefix + config.eib.xmlfile.value))
		self.displayZone()

	def displayZone(self):
		if self.gotoZone in self.EIB_zones:
			self.session.openWithCallback(self.ZoneScreenCB, EIBoxZoneScreen, self.EIB_zones[self.gotoZone])

	def errorOut(self, message):
		self.session.openWithCallback(self.close, MessageBox, message, type=MessageBox.TYPE_ERROR)

	def loadXML(self, filename):
		try:
			if not fileExists(filename):
				self.errorOut("[loadXML] " + str(filename) + ' ' + _("not found"))
				return
				#raise AttributeError
			file = open(filename, "r")
			data = file.read().decode("utf-8").replace('&', "&amp;").encode("ascii", 'xmlcharrefreplace')
			file.close()
			projectfiledom = xml.dom.minidom.parseString(data)
			for node in projectfiledom.childNodes[0].childNodes:
			  if node.nodeType == xml.dom.minidom.Element.nodeType:
			    if node.tagName == 'zones':
			      for subnode in node.childNodes:
				if subnode.nodeType == xml.dom.minidom.Element.nodeType:
				  if subnode.tagName == 'zone':
				    zone_id = str(subnode.getAttribute("id"))
				    zone_img = str(subnode.getAttribute("img"))
				    zone_name = str(subnode.getAttribute("name"))
				    filename = img_prefix + zone_img
				    if not zone_img or not fileExists(filename):
					print("[loadXML] ", filename, " not found! using default image")
					zone_img = "default_bg.png"
    				    self.EIB_zones[zone_id] = EIBObjects(zone_id, zone_name, zone_img)
				    if config.eib.debug.value:
					print("[loadXML] new EIB_zone", zone_id, zone_name, zone_img, self.EIB_zones[zone_id])
				    self.xmlGetZoneNode(subnode, zone_id)
				    if self.gotoZone == None:
					self.gotoZone = zone_id
				    #self.EIB_zones[zone_id].EIBreadAll()
			    if node.tagName == 'settings':
				config.eib.host.value = node.getAttribute("host")
				config.eib.port.value = int(node.getAttribute("port"))
				config.eib.refresh.value = int(node.getAttribute("refresh"))
				debug = False
				if node.getAttribute("debug") == "true":
					debug = True
				config.eib.debug.setValue(debug)
				if config.eib.debug.value:
					print("[loadXML] parsed settings! host:", config.eib.host.value, "port:", config.eib.port.value, "refresh:", config.eib.refresh.value, "debug:", config.eib.debug.value)
		except:
			self.errorOut("[loadXML] " + str(filename) + ' ' + _("parser error"))

	def xmlGetMultiNodes(self, node):
		values = []
		images = []
		for subnode in node.childNodes:
			print("[xmlGetMultiNodes] subnode", subnode)
			if subnode.nodeType == xml.dom.minidom.Element.nodeType:
				i = 0
				value = 0
				img = None
				while i < subnode.attributes.length:
					item = subnode.attributes.item(i)
					key = item.name.encode("utf-8")
					if key == "value":
						values.append(str(item.nodeValue))
					elif key == "img":
						images.append(str(item.nodeValue))
					i = i + 1
		return values, images

	def xmlGetZoneNode(self, node, zone):
		order = 0
		for subnode in node.childNodes:
			if subnode.nodeType == xml.dom.minidom.Element.nodeType:
				i = 0
				object_id = None
				object_type = None
				label = None
				img = None
				readonly = False
				custom_img = [None, None]
				custom_values = []
				temp_id = None
				setpoint_id = None
				textformat = None
				while i < subnode.attributes.length:
					item = subnode.attributes.item(i)
					key = item.name.encode("utf-8")
					if key == "object":
						object_id = item.nodeValue
					#if key == "switch": # dimmer on/off (1 bit)
						#object_id = item.nodeValue
					if key == "value": # dimmer brightness value (8 bit)
						object_id = item.nodeValue
					if key == "target": # goto target
						object_id = item.nodeValue
					if key == "temp": # thermostat actual value
						temp_id = item.nodeValue
					if key == "setpoint": # thermostat set point
						setpoint_id = item.nodeValue
					if key == "type":
						if item.nodeValue in ("dimmer", "switch", "goto", "thermostat", "text"):
							object_type = item.nodeValue
						elif item.nodeValue == "thermostat":
							object_type = item.nodeValue
						elif item.nodeValue == "multi":
							object_type = item.nodeValue
							custom_values, custom_img = self.xmlGetMultiNodes(subnode)
					if key == "label":
						label = item.nodeValue
					if key == "img":
						img = str(item.nodeValue)
					if key == "x":
						x = int(item.nodeValue)
					if key == "y":
						y = int(item.nodeValue)
					if key == "off":
						custom_img[0] = str(item.nodeValue)
					if key == "on":
						custom_img[1] = str(item.nodeValue)
					if key == "format":
						textformat = item.nodeValue
						readonly = True
					if key == "readonly" and item.nodeValue == "true":
						readonly = True
					i += 1
				if object_id and object_type and label and x and y:
					obj = EIBObject(order, object_id, object_type, label, (x, y), img, custom_img, custom_values, textformat, readonly)
					self.EIB_zones[zone].append(obj)
					if config.eib.debug.value:
						print("[xmlGetZoneNode] new", obj.getInfo())
					order += 1
				elif temp_id and setpoint_id and label and x and y:
					obj = EIBObject(order, temp_id, EIB_THERMO, label + ' ' + _("(actual)"), (x, y), readonly=True)
					self.EIB_zones[zone].append(obj)
					if config.eib.debug.value:
						print("[xmlGetZoneNode] new", obj.getInfo())
					order += 1
					obj = EIBObject(order, setpoint_id, EIB_THERMO, label + ' ' + _("(set point)"), (x, y + 16), readonly=readonly)
					self.EIB_zones[zone].append(obj)
					if config.eib.debug.value:
						print("[xmlGetZoneNode] new", obj.getInfo())
					order += 1
				else:
					print("[xmlGetZoneNode] couldn't parse object", object_id, object_type, label, (x, y), img, custom_img, custom_values, textformat, readonly, temp_id, setpoint_id)


def main(session, **kwargs):
	session.open(EIBox)


def Plugins(**kwargs):
	return PluginDescriptor(name="E.I.B.ox", description=_("Visualization for European Installation Bus"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
