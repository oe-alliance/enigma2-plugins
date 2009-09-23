from twisted.web import resource, http, server, static
from urllib import unquote_plus
from os import path as os_path

class FileStreamer(resource.Resource):
	addSlash = True

	def render(self, request):
		dir = request.args.get("dir", request.args.get("root"))
		if dir and dir[0]:
			dir = unquote_plus(dir[0])
		else:
			dir = ''

		if 'file' in request:
			filename = unquote_plus(request.args["file"][0])

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

