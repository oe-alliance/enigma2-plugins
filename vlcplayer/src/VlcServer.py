# -*- coding: ISO-8859-1 -*-
#===============================================================================
# VLC Player Plugin by A. Lätsch 2007
#                   modified by Volker Christian 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================


import re
import posixpath
from sys import maxint
from random import randint, seed
from urllib import urlencode
from urllib import urlopen
from xml.dom.minidom import parse
from VlcPlayer import isDvdUrl

seed()

def normpath(path):
	if path is None:
		return None
	path = path.replace("\\","/").replace("//", "/")
	if path == "/..":
		return None
	if len(path) > 0 and path[0] != '/':
		path = posixpath.normpath('/' + path)[1:]
	else:
		path = posixpath.normpath(path)

	if len(path) == 0 or path == "//":
		return "/"
	elif path == ".":
		return None
	return path
	

class VlcServer:
	def __init__(self, cfg):
		self.cfg = cfg

	def getCfg(self):
		return self.cfg

	def getName(self):
		return self.cfg.name.value

	def name(self):
		return self.cfg.name

	def getHost(self):
		if self.cfg.hostip.value == [0,0,0,0]:
			return self.cfg.name.value
		else:
			return '.'.join(["%d" % d for d in self.cfg.hostip.value])

	def host(self):
		return self.cfg.hostip

	def getHttpPort(self):
		return self.cfg.httpport.value

	def httpPort(self):
		return self.cfg.httpport

	def getBasedir(self):
		return self.cfg.basedir.value

	def basedir(self):
		return self.cfg.basedir

	def getVideoCodec(self):
		return self.cfg.videocodec.value

	def videoCodec(self):
		return self.cfg.videocodec

	def getVideoBitrate(self):
		return self.cfg.videobitrate.value

	def videoBitrate(self):
		return self.cfg.videobitrate

	def getAudioCodec(self):
		return self.cfg.audiocodec.value

	def audioCodec(self):
		return self.cfg.audiocodec

	def getAudioBitrate(self):
		return self.cfg.audiobitrate.value

	def audioBitrate(self):
		return self.cfg.audiobitrate

	def getSamplerate(self):
		return self.cfg.samplerate.value

	def samplerate(self):
		return self.cfg.samplerate

	def getAudioChannels(self):
		return self.cfg.audiochannels.value

	def audioChannels(self):
		return self.cfg.audiochannels

	def getVideoWidth(self):
		return self.cfg.videowidth.value

	def videoWidth(self):
		return self.cfg.videowidth

	def getVideoHeight(self):
		return self.cfg.videoheight.value

	def videoHeight(self):
		return self.cfg.videoheight

	def getFramesPerSecond(self):
		return self.cfg.framespersecond.value

	def framesPerSecond(self):
		return self.cfg.framespersecond

	def getAspectRatio(self):
		return self.cfg.aspectratio.value

	def aspectRatio(self):
		return self.cfg.aspectratio

	def getSOverlay(self):
		return self.cfg.soverlay.value

	def sOverlay(self):
		return self.cfg.soverlay

	def getTranscodeVideo(self):
		return self.cfg.transcodeVideo.value

	def transcodeVideo(self):
		return self.cfg.transcodeVideo

	def getTranscodeAudio(self):
		return self.cfg.transcodeAudio.value

	def transcodeAudio(self):
		return self.cfg.transcodeAudio

	def dvdPath(self):
		return self.cfg.dvdPath

	def getDvdPath(self):
		return self.cfg.dvdPath.value

	def __xmlRequest(self, request, params):
		uri = "/requests/" + request + ".xml"
		if params is not None: uri = uri + "?" + urlencode(params)
		location = "%s:%d" % (self.getHost(), self.getHttpPort())
		resp = urlopen("http://" + location + uri)
		if resp is None:
			raise IOError, "No response from Server"
		return parse(resp)

	def getFilesAndDirs(self, directory, regex):
		files = []
		directories = []
		response = self.__xmlRequest("browse", {"dir": directory})
		for element in response.getElementsByTagName("element"):
			if element.hasAttribute("type"):
				name = element.getAttribute("name").encode("utf8")
				path = normpath(element.getAttribute("path").encode("utf8"))
				if path is not None:
					elementType = element.getAttribute("type")
					if elementType == "directory":
						directories.append([name, path])
					elif elementType == "file":
						if regex is None or regex.search(path):
							files.append([name, path])
		return (files, directories)

	def getPlaylistEntries(self):
		xml = self.__xmlRequest("playlist", None)
		files = []
		for e in xml.getElementsByTagName("leaf"):
			if e.hasAttribute("uri") is not None:
				name = e.getAttribute("name").encode("utf8")
				if len(name) >= 50:
					name = "..." + name[-50:]
				path = e.getAttribute("uri").encode("utf8")
				files.append([name, path, int(e.getAttribute("id")), e.hasAttribute("current")])
		return files

	def getCurrentElement(self):
		xml = self.__xmlRequest("playlist", None)
		for e in xml.getElementsByTagName("leaf"):
			if e.hasAttribute("current"):
				return e
		return None
		
	def getCurrentId(self):
		files = self.getPlaylistEntries()
		for file in files:
			[name, path, id, isCurrent] = file
			if isCurrent:
				return id
		return None

	def playFile(self, filename, videoPid, audioPid):
		streamName = "dream" + str(randint(0, maxint))
		transcode = []

		doDirect = isDvdUrl(filename) or re.match("(?i).*\.(mpg|mpeg|ts)$", filename)

		if not doDirect or self.getTranscodeVideo():
			transcode.append("vcodec=%s,vb=%d,venc=ffmpeg{strict-rc=1},width=%s,height=%s,fps=%s,scale=1" % (
				self.getVideoCodec(),
				self.getVideoBitrate(),
				self.getVideoWidth(),
				self.getVideoHeight(),
				self.getFramesPerSecond()
			))
			if self.getAspectRatio() != "none":
				transcode.append("canvas-width=%s,canvas-height=%s,canvas-aspect=%s" % (
					self.getVideoWidth(),
					self.getVideoHeight(),
					self.getAspectRatio()
				))

		if not doDirect or self.getTranscodeAudio():
			transcode.append("acodec=%s,ab=%d,channels=%d,samplerate=%s" % (
				self.getAudioCodec(),
				self.getAudioBitrate(),
				self.getAudioChannels(),
				self.getSamplerate()
			))

		if self.getSOverlay():
			transcode.append("soverlay")

		if re.match("[a-zA-Z]:", filename):
			# Fix for subtitles with VLC on Windows.
			filename = filename.replace("/", "\\")

		filename = filename.replace("\\", "\\\\").replace("'", "\\'")
#		input = filename + " :dvdread-caching=3000 :sub-track=1 :audio-track=1 :sout=#"
		input = filename + " :sout=#"

		if len(transcode) > 0:
			input += "transcode{%s}:" % (",".join(transcode))

		mux="ts{pid-video=%d,pid-audio=%d}" % (videoPid, audioPid)
		input += "std{access=http,mux=%s,dst=/%s.ts} :sout-all :sout-keep" % (mux, streamName)

		print "[VLC] playfile", input

		xml = self.__xmlRequest("status", {"command": "in_play", "input": input})
		error = xml.getElementsByTagName("error")
		if error is not None and len(error) > 0:
			self.lastError = getText(error[0].childNodes).strip()
			if len(self.lastError) == 0:
				self.lastError = None
			else:
				print "[VLC] VlcControl error:", self.lastError
			return None
		else:
			self.lastError = None
		return "http://%s:%d/%s.ts" % (self.getHost(), self.getHttpPort(), streamName)

	def play(self):
		self.__xmlRequest("status", {"command": "pl_pause"})

	def stop(self):
		self.__xmlRequest("status", {"command": "pl_stop"})

	def pause(self):
		self.__xmlRequest("status", {"command": "pl_pause"})

	def delete(self, id):
		self.__xmlRequest("status", {"command": "pl_delete", "id": str(id)})

	def deleteCurrent(self):
		listid = self.getCurrentId()
		self.delete(listid)

	def deleteCurrentTree(self):
		print "[VLC] delete current tree"
		currentElement = self.getCurrentElement()
		while currentElement is not None and currentElement.parentNode.getAttribute("ro") != "ro":
			currentElement = currentElement.parentNode
		id = int(currentElement.getAttribute("id"))
		self.delete(id)
		
	def seek(self, value):
		"""  Allowed values are of the form:
  [+ or -][<int><H or h>:][<int><M or m or '>:][<int><nothing or S or s or ">]
  or [+ or -]<int>%
  (value between [ ] are optional, value between < > are mandatory)
examples:
  1000 -> seek to the 1000th second
  +1H:2M -> seek 1 hour and 2 minutes forward
  -10% -> seek 10% back"""
		self.__xmlRequest("status", {"command": "seek", "val": str(value)})

	def status(self):
		xml = self.__xmlRequest("status", None)
		stats = {}
		for e in xml.documentElement.childNodes:
			if e.nodeType == e.ELEMENT_NODE:
				if e.firstChild is None:
					stats[e.nodeName.encode("latin_1", "replace")] = None
				else:
					stats[e.nodeName.encode("latin_1", "replace")] = e.firstChild.nodeValue.encode("latin_1", "replace")
		return stats

	def loadPlaylist(self, playlist):
		self.__xmlRequest("status", {"command": "in_play", "input": playlist})
		self.__xmlRequest("status", {"command": "pl_stop"})
		xml = self.__xmlRequest("playlist", None)
		id = None
		for n in xml.getElementsByTagName("node"):
			if n.hasAttribute("name") is not None:
				if n.getAttribute("name").encode("latin_1", "replace") == playlist:
					if id is None:
						id = n.getAttribute("id")
					elif int(id) < int(n.getAttribute("id")):
						id = n.getAttribute("id")
		return id
