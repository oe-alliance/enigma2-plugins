from enigma import eConsoleAppContainer

from twisted.web import resource, http, http_headers, server

from os import path as os_path, remove as os_remove

class GrabResource(resource.Resource):
	'''
		this is a interface to Seddis AiO Dreambox Screengrabber
	'''
	GRAB_BIN = '/usr/bin/grab'
	SPECIAL_ARGS = ['format', 'filename', 'save']
	
	def __init__(self):
		resource.Resource.__init__(self)
	
	def render(self, request):
		self.baseCmd = ['/usr/bin/grab', '/usr/bin/grab']
		self.args = []

		# some presets
		filename = 'screenshot'
		imageformat = 'bmp'
		osdOnly = False
		videoOnly = False
		save = False

		for key, value in request.args.items():
			if key in GrabResource.SPECIAL_ARGS:
				if key == 'format':
					format = request.args['format'][0]

					if format == 'png':
						#-p produce png files instead of bmp
						imageformat = format
						self.args.append('-p')
					elif format == 'jpg':
						#-j (quality) produce jpg files instead of bmp

						imageformat = format
						self.args.append('-j')
						#Quality Setting
						if request.args.has_key("jpgquali"):
							self.args.append("%s" %(request.args["jpgquali"][0]) )
						else:
							self.args.append('80')

				elif key == 'filename':
					filename = request.args['filename'][0]

				elif key == 'save':
					save = True
			else:
				if key == "o" and videoOnly is True:
					continue
				if key == "v" and osdOnly is True:
					continue

				self.args.append("-%s" %key )

				if value is not None:
					if len(value[0]) > 0:
						self.args.append("%s" %value[0])

		if not os_path.exists(self.GRAB_BIN):
			request.setResponseCode(http.OK)
			request.write('Grab is not installed at %s. Please install package aio-grab.' %self.GRAB_BIN)
			request.finish()			
			
		else:
			request.setHeader('Content-Disposition', 'inline; filename=screenshot.%s;' %imageformat)			
			request.setHeader('Content-Type','image/%s' %imageformat)

			filename = filename+imageformat
			self.args.append(filename)
			cmd = self.baseCmd + self.args
					
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
		self.container.dataAvail.append(self.dataAvail)

		print '[Screengrab.py] starting AiO grab with cmdline:', cmd
		self.container.execute(*cmd)

	def cmdFinished(self, data):
		print '[Screengrab.py] cmdFinished'
		if int(data) is 0 and self.target is not None:
			try:
				fp = open(self.target)
				self.request.write(fp.read())
				fp.close()
				if self.save is False:
					os_remove(self.target)
					print '[Screengrab.py] %s removed' %self.target
			except Exception,e:
				self.request.write('Internal error while reading target file')
		elif int(data) is 0 and self.target is None:
			self.request.write(self.output)
		elif int(data) is 1:
			self.request.write(self.output)
		else:
			self.request.write('Internal error')
			
		self.request.finish()

	def dataAvail(self, data):
		print '[Screengrab.py] data Available ', data

