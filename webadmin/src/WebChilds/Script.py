# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
from .PKG import PKGConsoleStream
from twisted.web import server, resource, http
from urllib.parse import unquote_plus


class Script(resource.Resource):
	def _to_str(self, value):
		if isinstance(value, bytes):
			return value.decode("utf-8", "ignore")
		return value

	def _normalize_args(self, args):
		result = {}
		for key, values in args.items():
			result[self._to_str(key)] = [self._to_str(v) for v in values]
		return result

	def render(self, request):
		self.args = self._normalize_args(request.args)
		self.command = self.getArg("command")

		if self.command is not None:
			return self.execCmd(request)
		request.setResponseCode(http.BAD_REQUEST)
		return b"missing command"

	def execCmd(self, request):
		cmd = [part for part in unquote_plus(self.command).split() if part]
		if not cmd:
			request.setResponseCode(http.BAD_REQUEST)
			return b"invalid command"
		cmd[0] = "/usr/script/" + cmd[0]
		print("[Script] cmd: %s" % cmd)
		request.setResponseCode(http.OK)
		PKGConsoleStream(request, cmd)
		return server.NOT_DONE_YET

	def getArg(self, key):
		if key in self.args:
			return self.args[key][0]
		return None
