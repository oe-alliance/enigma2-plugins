from enigma import eConsoleAppContainer

from twisted.web import server, resource, http

class IPKGResource(resource.Resource):
	IPKG_PATH = "/usr/bin/ipkg"

	SIMPLECMDS = ( "list", "list_installed", "update", "upgrade" )
	PACKAGECMDS = ( "info", "status", "install", "remove" )
	FILECMDS = ( "search", )

	def render(self, request):
		self.args = request.args
		self.command = self.getArg("command")

		if self.command is not None:
			if self.command in IPKGResource.SIMPLECMDS:
				return self.execSimpleCmd(request)
			elif self.command in IPKGResource.PACKAGECMDS:
				return self.execPackageCmd(request)
			elif self.command in IPKGResource.FILECMDS:
				return self.execFileCmd(request)
			else:
				return self.doErrorPage(request, "Unknown command: "+ self.command)
		else:
			return self.doIndexPage(request)

	def buildCmd(self, parms=[]):
		cmd = [IPKGResource.IPKG_PATH, "ipkg", self.command] + parms
		print "[IPKG.py] cmd: %s" % cmd
		return cmd

	def execCmd(self, request, parms=[]):
		cmd = self.buildCmd(parms)

		request.setResponseCode(http.OK)
		IPKGConsoleStream(request, cmd)

		return server.NOT_DONE_YET

	def execSimpleCmd(self, request):
		 return self.execCmd(request)

	def execPackageCmd(self, request):
		package = self.getArg("package")
		if package is not None:
			return self.execCmd(request, [package])
		else:
			return self.doErrorPage(request, "Missing parameter: package")

	def execFileCmd(self, request):
		file = self.getArg("file")
		if file is not None:
			return self.execCmd(request, [file])

		else:
			return self.doErrorPage("Missing parameter: file")

	def doIndexPage(self, request):
		html = "<html><body>"
		html += "<h1>Interface to IPKG</h1>"
		html += "update, ?command=update<br>"
		html += "upgrade, ?command=upgrade<br>"
		html += "list_installed, ?command=list_installed<br>"
		html += "list, ?command=list<br>"
		html += "search, ?command=search&file=&lt;filename&gt;<br>"
		html += "info, ?command=info&package=&lt;packagename&gt;<br>"
		html += "status, ?command=status&package=&lt;packagename&gt;<br>"
		html += "install, ?command=install&package=&lt;packagename&gt;<br>"
		html += "remove, ?command=remove&package=&lt;packagename&gt;<br>"
		html += "</body></html>"

		request.setResponseCode(http.OK)
		request.write(html)
		request.finish()

		return server.NOT_DONE_YET

	def doErrorPage(self, request, errormsg):
		request.setResponseCode(http.OK)
		request.write(errormsg)
		request.finish()

		return server.NOT_DONE_YET

	def getArg(self, key):
		if key in self.args:
			return self.args[key][0]
		else:
			return None

class IPKGConsoleStream:
	def __init__(self, request, cmd):
		self.request = request

		self.container = eConsoleAppContainer()

		self.container.dataAvail.append(self.dataAvail)
		self.container.appClosed.append(self.cmdFinished)

		self.container.execute(*cmd)

	def cmdFinished(self, data):
		self.request.finish()

	def dataAvail(self, data):
		self.request.write(data)

