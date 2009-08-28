from twisted.web import resource, http, http_headers, server, static
from urllib import unquote_plus
from os import path as os_path

class FileStreamer(resource.Resource):
	addSlash = True
	
	def __init__(self):
		resource.Resource.__init__(self)
	
	def render(self, request):
		try:
			w1 = request.uri.split("?")[1]
			w2 = w1.split("&")
			parts = {}
			for i in w2:
				w3 = i.split("=")
				parts[w3[0]] = w3[1]
		except:
			request.setResponseCode(http.OK)
			request.write("no file given with file=???")
			request.finish()
						
		dir = ""
		
		if parts.has_key("root"):
			#root = parts["root"].replace("%20"," ")
			dir = unquote_plus(parts["root"])
		if parts.has_key("dir"):
			dir = unquote_plus(parts["dir"])
		if parts.has_key("file"):
			#filename = parts["file"].replace("%20"," ")
			filename = unquote_plus(parts["file"])
			
			path = "%s%s" %(dir, filename)
			#dirty backwards compatibility hack
			if not os_path.exists(path):
				path = "/hdd/movie/%s" %filename
			
			if os_path.exists(path):
				file = static.File(path)
				return file.render(request)
				
			else:
				request.setResponseCode(http.OK)
				request.write("file '%s' was not found"%path)
				request.finish()				
		else:
			request.setResponseCode(http.OK)
			request.write("no file given with file=???")
			request.finish()
			
		return server.NOT_DONE_YET




