# -*- coding: utf-8 -*-
from enigma import eConsoleAppContainer
from twisted.web import server, resource, http
from Plugins.Extensions.WebInterface.WebChilds.IPKG import IPKGConsoleStream, IPKGResource


class PKGResource(IPKGResource):
	def execCmd(self, request, parms=[]):
		cmd = self.buildCmd(parms)
		request.setResponseCode(http.OK)
		PKGConsoleStream(request, cmd)
		return server.NOT_DONE_YET


class PKGConsoleStream(IPKGConsoleStream):
	def __init__(self, request, cmd):
		self.cmd = cmd
		self.request = request
		html = """<?xml version="1.0" encoding="UTF-8"?>
					<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
							"http://www.w3.org/TR/html4/loose.dtd">
					<html>

					<head>
					<meta content="text/html; charset=UTF-8" http-equiv="content-type">

					<link href="/web-data/tpl/default/style.min.css" type="text/css" rel="stylesheet">
					<link rel="shortcut icon" type="image/x-icon" href="/web-data/img/favicon.ico">
				</head>
				<body onunload="javascript:opener.location.reload()" onload="window.scrollBy(0,1000000);" >
					<hr>
					<p align="left">"""

		self.request.write(html)

		if hasattr(self.request, 'notifyFinish'):
			self.request.notifyFinish().addErrback(self.connectionLost)
		self.container = eConsoleAppContainer()
		self.lastdata = None
		self.stillAlive = True
		self.container.dataAvail.append(self.dataAvail)
		self.container.appClosed.append(self.cmdFinished)
		self.container.execute(*cmd)

	def cmdFinished(self, data):
		if self.stillAlive:
			print "[PKGConsoleStream].self.cmd ", self.cmd
			if "/usr/bin/opkg" in self.cmd and not "update" in self.cmd:
				html = """</p>
						<hr>
						<form>
							<input type="button" value="%s" onClick="opener.core.power.set('gui');">
							<input type="button" value="%s" onClick="opener.core.power.set('reboot');">
							<input type="button" value="%s" onClick="window.close();">
						</form>
					</body>
					</html>""" % (_("Restart GUI"), _("Restart"), _("Close"))
			else:
				html = """</p>
						<hr>
						<form>
							<input type="button" value="%s" onClick="window.close();">
						</form>
					</body>
					</html>""" % _("Close")
			self.request.write(html)
			self.request.finish()
