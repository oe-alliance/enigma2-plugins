# -*- coding: utf-8 -*-
###########################################################################
#
# http://newnigma2.to
#
# $Id:
#
# Copyright (C) 2009 by
# <nixkoenner@newnigma2.to>
#
#	   License: GPL
#
#	   This program is free software; you can redistribute it and/or modify
#	   it under the terms of the GNU General Public License as published by
#	   the Free Software Foundation; either version 2 of the License, or
#	   (at your option) any later version.
#
#	   This program is distributed in the hope that it will be useful,
#	   but WITHOUT ANY WARRANTY; without even the implied warranty of
#	   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	   GNU General Public License for more details.
#
#	   You should have received a copy of the GNU General Public License
#	   along with this program; if not, write to the Free Software
#	   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
###########################################################################
#
# thx to <kayshadow@newnigma2.to> for painting the icon 
#
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.ActionMap import ActionMap
from Components.Button import Button
from Components.Label import Label 

import socket
import struct
import base64
import os

from twisted.web.client import getPage

TPMD_DT_RESERVED = 0x00
TPMD_DT_PROTOCOL_VERSION = 0x01
TPMD_DT_TPM_VERSION = 0x02
TPMD_DT_SERIAL = 0x03
TPMD_DT_LEVEL2_CERT = 0x04
TPMD_DT_LEVEL3_CERT = 0x05
TPMD_DT_FAB_CA_CERT = 0x06
TPMD_DT_DATABLOCK_SIGNED = 0x07
TPMD_CMD_RESERVED = 0x0000
TPMD_CMD_GET_DATA = 0x0001
TPMD_CMD_APDU = 0x0002
TPMD_CMD_COMPUTE_SIGNATURE = 0x0003
TPMD_CMD_APP_CERT = 0x0004
TPMD_PV_2 = 0x02


class genuineDreambox(Screen):
	skin = """
		<screen position="center,center" size="620,420" title="%s" >
		<widget name="infotext" position="10,20" zPosition="1" size="600,150" font="Regular;20" halign="center" valign="center" />
		<widget name="resulttext" position="10,160" zPosition="1" size="600,110" font="Regular;20" halign="center" valign="center" />
		<widget name="infotext2" position="10,280" zPosition="1" size="600,80" font="Regular;20" halign="center" valign="center" />
		<widget name="kRed" position="185,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />	   
		<ePixmap name="red" position="185,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<widget name="kGreen" position="330,365" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<ePixmap name="green" position="330,365" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		</screen>""" % _("Genuine Dreambox")

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"green": self.restart,
			"cancel": self.exit,
		 }, -1)
		self["kGreen"] = Button(_("Test again"))
		self["kRed"] = Button(_("Cancel"))
		self["infotext"] = Label("With this plugin you can verify the authenticity of your Dreambox.\nFor additional information, \nplease visit our website \nhttps://www.dream-multimedia-tv.de.")
		self["resulttext"] = Label("... Please wait ...")
		self["infotext2"] = Label("Please visit our website and follow the instructions.\nAlternatively you can call our customer service hotline.")
		self.onLayoutFinish.append(self.start)

	def restart(self):
		if not self.isStart:
			self.start()

	def start(self):
		udsError = False
		self.isStart = True
		try:
			self["resulttext"].setText("Please wait (Step 1)")
			self.uds = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			self.uds.connect(("/var/run/tpmd_socket"))
			self.uds.settimeout(5.0)
		except:
			self["resulttext"].setText("Security service not running.")
			udsError = True
		if not udsError:
			if (self.stepFirst(TPMD_CMD_GET_DATA, [TPMD_DT_PROTOCOL_VERSION, TPMD_DT_TPM_VERSION, TPMD_DT_SERIAL])):
				try:  
					url = ("https://www.dream-multimedia-tv.de/verify/challenge?serial=%s&version=%s" % (self.serial, self.tpmdVersion))
					getPage(url).addCallback(self._gotPageLoadRandom).addErrback(self.errorLoad)
				except:
					self["resulttext"].setText(_("Can't connect to server. Please check your network!"))

	def needsTPMUpdate(self):
		return self.level3_cert is None
	
	def updateCallback(self, result):
		if result:
			self.isStart = True
			url = self.buildUrlUpdate()
			#url = ("https://www.dream-multimedia-tv.de/verify/challenge?serial=%s&version=%s" % (self.serial,self.tpmdVersion))
			self["resulttext"].setText(_("Updating, please wait..."))
			getPage(url).addCallback(self._gotPageLoadUpdate).addErrback(self.errorLoad)
		else:
			print "not updating"

	def _gotPageLoad(self, data):
		authcode = data.strip().replace('+', '')
		if len(authcode) == 12:
			self.finish = "%s-%s-%s" % (authcode[0:4], authcode[4:8], authcode[8:12])
			self["resulttext"].setText(self.finish)
			if self.needsTPMUpdate():
				if int(self.protocolVersion) >= TPMD_PV_2:
					self.session.openWithCallback(self.updateCallback, MessageBox, _("There's a certificate update available for your dreambox. Would you like to apply this update now?"))
		else:
			self["resulttext"].setText(_("Invalid response from server."))
		self.closeUds()
		self.isStart = False
		
	def _gotPageLoadRandom(self, data):
		self["resulttext"].setText(_("Please wait (Step 2)"))
		self.back = data.strip()
		self.random = (self.formatList(base64.b64decode(self.back)))
		self.level2_cert = None
		self.level3_cert = None
		if (self.stepSecond(TPMD_CMD_GET_DATA, [TPMD_DT_PROTOCOL_VERSION, TPMD_DT_TPM_VERSION, TPMD_DT_SERIAL, TPMD_DT_LEVEL2_CERT,
				TPMD_DT_LEVEL3_CERT, TPMD_DT_FAB_CA_CERT, TPMD_DT_DATABLOCK_SIGNED])):
			url = self.buildUrl()
			getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)
			
	def _gotPageLoadUpdate(self, data):
		updatedata = base64.decodestring(data)
		if len(updatedata) != 409:
			self["resulttext"].setText(_("Updating failed. Nothing is broken, just the update couldn't be applied."))
			self.isStart = False
		else:
			udsError = False
			
			try:
				self.uds = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
				self.uds.connect(("/var/run/tpmd_socket"))
				self.uds.settimeout(5.0)
			except:
				self["resulttext"].setText(_("Security service not running."))
				udsError = True
			if not udsError:
				data = [chr(0)]
				data.extend(updatedata)
				data = self.formatList(data)
				self.udsSend(TPMD_CMD_APP_CERT, data, 410)
				self["resulttext"].setText(_("Update done..."))
				self.closeUds()
				self.isStart = False
				self.session.openWithCallback(self.updateFinished, MessageBox, _("Update done... The genuine dreambox test will now be rerun and should not ask you to update again."), MessageBox.TYPE_INFO)
	
	def updateFinished(self, result):
		self.start()		

	def errorLoad(self, error):
		print str(error)
		self["resulttext"].setText(_("Invalid response from server. Please report: %s") % str(error))

	def buildUrl(self):
		# NOTE: this is a modified base64 which uses -_ instead of +/ to avoid the need for escpaing + when using urlencode 
		tmpra = ("random=%s" % self.back.replace('+', '-').replace('/', '_'))
		tmpl2 = ("&l2=%s" % base64.b64encode(self.level2_cert).replace('+', '-').replace('/', '_'))
		if self.level3_cert is not None:
			tmpl3 = ("&l3=%s" % base64.b64encode(self.level3_cert).replace('+', '-').replace('/', '_'))
		else:
			tmpl3 = ""
		tmpfa = ("&fab=%s" % base64.b64encode(self.fab_ca_cert).replace('+', '-').replace('/', '_'))
		tmpda = ("&data=%s" % base64.b64encode(self.datablock_signed).replace('+', '-').replace('/', '_'))
		tmpr = ("&r=%s" % base64.b64encode(self.r).replace('+', '-').replace('/', '_'))
		return("https://www.dream-multimedia-tv.de/verify/challenge?%s%s%s%s%s%s&serial=%s" % (tmpra, tmpl2, tmpl3, tmpfa, tmpda, tmpr, self.serial))

	def buildUrlUpdate(self):
		return self.buildUrl() + "&getupdate=true"

	def formatList(self, l):
		liste = []
		for x in l:
			liste.append(ord(x))
		return liste
	
	def formatString(self, s):
		myString = ""
		for x in s:
			myString = myString + chr(x)
		return myString

	def stepFirst(self, typ, daten):
		return (self.parseResult(self.udsSend(typ, daten, len(daten))))

	def stepSecond(self, typ, daten):
		if (self.parseResult(self.udsSend(typ, daten, len(daten))) == False):
			return False
		if (self.parseSignature(self.udsSend(TPMD_CMD_COMPUTE_SIGNATURE, self.random, 8)) == False):
			return False
		return True	 

	def parseResult(self, rbuf):
		if (rbuf != -1):
			buf = self.formatList(rbuf)
			
			pos = 0
			while pos < len(buf):
				tag = buf[pos]
				length = buf[pos + 1]
				value = buf[pos + 2: pos + 2 + length]
				if tag == TPMD_DT_PROTOCOL_VERSION:
					if length != 1:
						self.protocolVersion = None
					else:
						self.protocolVersion = "%d" % value[0]
				elif tag == TPMD_DT_TPM_VERSION:
					if length != 1:
						self.tpmdVersion = None
					else:
						self.tpmdVersion = "%d" % value[0]
				elif tag == TPMD_DT_SERIAL:
					if length != 4:
						self.serial = None
					else:
						self.serial = "%d" % ((value[0] << 24) | (value[1] << 16) | (value[2] << 8) | value[3])
				elif tag == TPMD_DT_LEVEL2_CERT:
					if length != 210:
						self.level2_cert = None
					else:
						self.level2_cert = ''.join([chr(x) for x in value])
				elif tag == TPMD_DT_LEVEL3_CERT:
					if length != 210:
						self.level3_cert = None
					else:
						self.level3_cert = ''.join([chr(x) for x in value])
				elif tag == TPMD_DT_FAB_CA_CERT:
					if length != 210:
						self.fab_ca_cert = None
					else:
						self.fab_ca_cert = ''.join([chr(x) for x in value])
				elif tag == TPMD_DT_DATABLOCK_SIGNED:
					if length != 128:
						self.datablock_signed = None
					else:
						self.datablock_signed = ''.join([chr(x) for x in value])
				else:
					print "unknown tag:", tag
				pos += 2 + length
				
			return True
		else:
			return False
		
	def parseSignature(self, rbuf):
		if (rbuf != -1):
			self.r = self.formatString(self.formatList(rbuf))
			return True
		else:
			return False

	def udsSend(self, cmdTyp, data, length):
		udsError = False
		sbuf = [(cmdTyp >> 8) & 0xff, (cmdTyp >> 0) & 0xff, (length >> 8) & 0xff, (length >> 0) & 0xff]
		sbuf.extend(data[:length])
		sbuf = struct.pack(str((length + 4)) + "B", *sbuf)
		try:
			self.uds.send(sbuf)
			udsError = False
		except socket.timeout:
			udsError = True
		try:
			rbuf = self.uds.recv(4)
			udsError = False
		except socket.timeout:
			udsError = True
			
		res = -1
	
		if (udsError == False):
			leng = [ord(rbuf[2]) << 8 | ord(rbuf[3])]
			if (leng != 4):
				try:
					res = self.uds.recv(leng[0])
				except socket.timeout:
					udsError = True
			else:
				return -1
		else:
			self["resulttext"].setText(_("Invalid response from Security service pls restart again"))
			os.system("kill -9 $(pidof tpmd)")
			return -1
		return res

	def closeUds(self):
		try:
			self.uds.close()
		except:
			pass

	def exit(self):
		self.closeUds()
		self.close() 


def main(session, **kwargs):
		session.open(genuineDreambox)


def Plugins(path, **kwargs):
		global plugin_path
		plugin_path = path
		return [
				PluginDescriptor(name="Genuine Dreambox", description=_("Genuine Dreambox verification"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="genuine.png", fnc=main)
				]
