from __future__ import print_function
from enigma import eConsoleAppContainer

from twisted.web import resource, http, http_headers, server

from os import path as os_path, remove as os_remove
from os.path import getsize as os_path_getsize


def _decode_if_bytes(value):
	if isinstance(value, bytes):
		return value.decode("utf-8", "ignore")
	return value


def _normalize_request_args(args):
	return {_decode_if_bytes(k): [_decode_if_bytes(v) for v in values] for k, values in args.items()}


class GrabResource(resource.Resource):
	'''
		this is a interface to Seddis AiO Dreambox Screengrabber
	'''
	GRAB_BIN = '/usr/bin/grab'
	SPECIAL_ARGS = ('format', 'filename', 'save')

	def render(self, request):
		args = []
		append = args.append

		# some presets
		filename = 'screenshot'
		imageformat = 'bmp'
		osdOnly = False
		videoOnly = False
		save = False

		request_args = _normalize_request_args(request.args)
		for key, value in list(request_args.items()):
			if key in GrabResource.SPECIAL_ARGS:
				if key == 'format':
					format = value[0]

					if format == 'png':
						#-p produce png files instead of bmp
						imageformat = format
						append('-p')
					elif format == 'jpg':
						#-j (quality) produce jpg files instead of bmp

						imageformat = format
						append('-j')
						#Quality Setting
						if 'jpgquali' in request_args:
							append("%s" % (request_args["jpgquali"][0]))
						else:
							append('80')

				elif key == 'filename':
					filename = value[0]

				elif key == 'save':
					save = True
			else:
				if key == "o" and videoOnly is True:
					continue
				if key == "v" and osdOnly is True:
					continue

				append("-%s" % key)

				if value:
					if value[0]:
						append("%s" % (value[0]))

		if not os_path.exists(self.GRAB_BIN):
			request.setResponseCode(http.OK)
			return ('Grab is not installed at %s. Please install package aio-grab.' % self.GRAB_BIN).encode("utf-8")

		else:
			request.setHeader('Content-Disposition', 'inline; filename=screenshot.%s;' % imageformat)
			mimetype = imageformat
			if mimetype == 'jpg':
				mimetype = 'jpeg'

			request.setHeader('Content-Type', 'image/%s' % mimetype)

			filename = "%s.%s" % (filename, imageformat)
			append(filename)
			cmd = [self.GRAB_BIN, self.GRAB_BIN] + args

			GrabStream(request, cmd, filename, save)

		return server.NOT_DONE_YET


class GrabStream:
	'''
		used to start the grab-bin in the console in the background
		while this takes some time, the browser must wait until the grabis finished
	'''

	def __init__(self, request, cmd, target=None, save=False):
		self.target = target
		self.save = save
		self.output = ''
		self.request = request

		self.container = eConsoleAppContainer()
		self.container.appClosed.append(self.cmdFinished)

		self.stillAlive = True
		if hasattr(self.request, 'notifyFinish'):
			self.request.notifyFinish().addErrback(self.connectionLost)

		print('[Screengrab.py] starting AiO grab with cmdline:', cmd)
		self.container.execute(*cmd)

	def connectionLost(self, err):
		self.stillAlive = False

	def cmdFinished(self, data):
		print('[Screengrab.py] cmdFinished')
		if self.stillAlive:
			self.request.setResponseCode(http.OK)
			if int(data) == 0 and self.target is not None:
				try:
					self.request.setHeader('Content-Length', '%i' % os_path_getsize(self.target))
					with open(self.target, "rb") as fp:
						self.request.write(fp.read())
					if self.save is False:
						os_remove(self.target)
						print('[Screengrab.py] %s removed' % self.target)
				except Exception as e:
					self.request.write(b'Internal error while reading target file')
					self.request.setResponseCode(http.INTERNAL_SERVER_ERROR)

			elif int(data) == 0 and self.target is None:
				self.request.write(self.output.encode("utf-8") if isinstance(self.output, str) else self.output)
			elif int(data) == 1:
				self.request.write(self.output.encode("utf-8") if isinstance(self.output, str) else self.output)
			else:
				self.request.setResponseCode(http.INTERNAL_SERVER_ERROR)

			self.request.finish()
		else:
			print('[Screengrab.py] already disconnected!')

	def requestFinished(self, val):
		pass
