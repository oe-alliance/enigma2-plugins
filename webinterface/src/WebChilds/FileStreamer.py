from twisted.web import resource, http, server, static
from urllib import unquote
from os import path as os_path
from Tools.Directories import resolveFilename, SCOPE_HDD

class FileStreamer(resource.Resource):
	addSlash = True

	def render(self, request):
		if 'dir' in request.args:
			dir = unquote(request.args['dir'][0])
		elif 'root' in request.args:
			dir = unquote(request.args['root'][0])
		else:
			dir = ''

		if 'file' in request.args:
			filename = unquote(request.args["file"][0])
			path = dir + filename

			#dirty backwards compatibility hack
			if not os_path.exists(path):
				path = resolveFilename(SCOPE_HDD, filename)

			print "[WebChilds.FileStreamer] path is %s" %path

			if os_path.exists(path):
				basename = filename.decode('utf-8', 'ignore').encode('ascii', 'ignore')

				if '/' in basename:
					basename = basename.split('/')[-1]

				request.setHeader("content-disposition", "attachment;filename=\"%s\"" % (basename))
				file = static.File(path, defaultType="application/octet-stream")
				return file.render_GET(request)

			else:
				return resource.NoResource(message="file '%s' was not found" %(dir + filename)).render(request)
		else:
			return resource.NoResource(message="no file given with file={filename}").render(request)

		return server.NOT_DONE_YET

