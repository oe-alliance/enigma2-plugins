# -*- coding: utf-8 -*-
from __future__ import print_function
from PKG import PKGConsoleStream

from twisted.web import server, resource, http

class Script(resource.Resource):
	
	def render(self, request):
		self.args = request.args
		self.command = self.getArg("command")

		if self.command is not None:
			return self.execCmd(request)

	def execCmd(self, request):
		cmd = self.command.split("+")
		cmd[0] = "/usr/script/" + cmd[0]
		print("[Script] cmd: %s" % cmd)
		request.setResponseCode(http.OK)
		PKGConsoleStream(request, cmd)

		return server.NOT_DONE_YET

	def getArg(self, key):
		if key in self.args:
			return self.args[key][0]
		else:
			return None
