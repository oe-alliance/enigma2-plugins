# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. L�tsch 2007
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from Components.config import config
from VlcControlHttp import getLocalHostIP
import socket

def vlctime2sec(t):
	t = float(t)
	if t < 0:
		t += 2**32
	return t/1000000

class VlcControlTelnet:
	defaultStreamName = None
	
	def __init__(self, servernum):
		cfg = config.plugins.vlcplayer.servers[servernum]
		host = cfg.host.value
		port = cfg.adminport.value
		self.address = (host, int(port));
		self.passwd = cfg.adminpwd.value
		if VlcControlTelnet.defaultStreamName is None:
			try:
				ip = getLocalHostIP( (cfg.host.value, cfg.httpport.value) )
				VlcControlTelnet.defaultStreamName = "dream" + str(ip)
			except Exception, e:
				VlcControlTelnet.defaultStreamName = "dreambox"

	def __connect(self):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.settimeout(10)
		self.s.connect(self.address)
		resp = self.s.recv(1024)
		if resp.find("Password:") == -1:
			raise IOError, "expected: 'Password:', got: %s" % resp
		resp = self.__submitCmd(self.passwd)
		if resp.find("Welcome") == -1:
			raise IOError, "expected: 'Welcome', got: %s" % resp
		self.s.settimeout(3)

	def __close(self):
		self.s.close()

	def __submitCmd(self, command):
		print "[VLC] SEND:", command
		self.s.send(command + "\n")
		msg = self.s.recv(4096)
		if msg is None: 
			msg = ""
		else:
			msg = msg.strip()
		if msg[-1:] == ">": msg = msg[:-1].strip()
		#print "[VLC] RECV:", msg
		return msg
		
	def __submitCmdExpectNone(self, command):
		resp = self.__submitCmd(command)
		if len(resp) > 0:
			raise IOError, "Error with VLC command:\n%s\nResponse: %s" % (command,resp)

	def __setupStream(self, inputfile, sout):
		self.__submitCmd('del ' + self.defaultStreamName)
		self.__submitCmdExpectNone(
			'new %s broadcast enabled input "%s" output %s' % (self.defaultStreamName, inputfile, sout)
		)

	def __status(self):
		stats = {}
		resp = self.__submitCmd("show %s \n" % self.defaultStreamName)
		if resp is None or len(resp) == 0:
			return stats
		for line in resp.split("\n"):
			if len(line) == 0 or line[0] == '>':
				break
			args = line.strip().split(" : ", 2)
			if len(args) == 2:
				key = args[0].strip()
				val = args[1].strip()
				if key == "time":
					stats[key] = vlctime2sec(val)
				elif key == "length":
					stats[key] = vlctime2sec(val)
				elif key == "state":
					stats[key] = val
				elif key == "position":
					stats[key] = float(val)
		return stats

	def playfile(self, filename, output):
		self.__connect()
		self.__setupStream(filename, output)
		self.play()
		self.__close()

	def play(self, listid=None):
		if listid is None: listid = self.defaultStreamName
		self.__connect()
		self.__submitCmdExpectNone(
			'control %s play' % listid
		)
		self.__close()

	def pause(self):
		self.__connect()
		self.__submitCmdExpectNone(
			'control %s pause' % self.defaultStreamName
		)
		self.__close()

	def stop(self):
		self.__connect()
		self.__submitCmdExpectNone(
			'control %s stop' % self.defaultStreamName
		)
		self.__close()

	def seek(self, value):
		self.__connect()
		stats = self.__status()
		time = stats["time"]
		length = stats["length"]
		if time is not None and length is not None:
			time += float(value)
			if time < 0: time = 0
			elif time > length: time = length
			value = str(time/length*100) + "%"
		self.__submitCmdExpectNone(
			'control %s seek %s' % (self.defaultStreamName, value)
		)
		self.__close()

	def delete(self, listid=None):
		if listid is None:
			listid = self.defaultStreamName
		self.__connect()
		self.__submitCmd('del ' + listid)
		self.__close()
		
	def status(self):
		self.__connect()
		stats = self.__status()
		self.__close()
		return stats

