from __future__ import print_function
from twisted.web import resource, http, server, static
from urllib.parse import unquote
from os import path as os_path
from Tools.Directories import resolveFilename, SCOPE_HDD


def _decode_if_bytes(value):
	if isinstance(value, bytes):
		return value.decode("utf-8", "ignore")
	return value


def _normalize_request_args(args):
	return {_decode_if_bytes(k): [_decode_if_bytes(v) for v in values] for k, values in args.items()}


class FileStreamer(resource.Resource):
	addSlash = True

	def render(self, request):
		args = _normalize_request_args(request.args)
		if 'dir' in args:
			dir = unquote(args['dir'][0])
		elif 'root' in args:
			dir = unquote(args['root'][0])
		else:
			dir = ''

		if 'file' in args:
			filename = unquote(args["file"][0])
			path = dir + filename

			#dirty backwards compatibility hack
			if not os_path.exists(path):
				path = resolveFilename(SCOPE_HDD, filename)

			print("[WebChilds.FileStreamer] path is %s" % path)

			if os_path.exists(path):
				basename = filename.encode('utf-8', 'ignore').decode('utf-8', 'ignore').encode('ascii', 'ignore').decode('ascii')

				if '/' in basename:
					basename = basename.split('/')[-1]

				request.setHeader("content-disposition", "attachment;filename=\"%s\"" % (basename))
				file = static.File(path, defaultType="application/octet-stream")
				return file.render_GET(request)

			else:
				return resource.NoResource(message="file '%s' was not found" % (dir + filename)).render(request)
		else:
			return resource.NoResource(message="no file given with file={filename}").render(request)

		return server.NOT_DONE_YET
