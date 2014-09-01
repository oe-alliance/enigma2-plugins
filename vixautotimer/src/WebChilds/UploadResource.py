from os import write as os_write, close as os_close, O_WRONLY as os_O_WRONLY, O_CREAT as os_O_CREAT, open as os_open, remove as os_remove
from twisted.web import resource, http

class UploadResource(resource.Resource):
	FILENAME = "/tmp/autotimer_backup.tar"
	def __init__(self, session):
		self.session = session
		resource.Resource.__init__(self)

	def render_POST(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml;' )
		req.setHeader('charset', 'UTF-8')	
		data = req.args['file'][0]
		if not data:
			result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
				<e2simplexmlresult>\n
					<e2state>False</e2state>
					<e2statetext>Filesize was 0, not uploaded</e2statetext>
				</e2simplexmlresult>\n"""
			return result
		fd = os_open( self.FILENAME, os_O_WRONLY|os_O_CREAT )
		if fd:
			cnt = os_write(fd, data)
			os_close(fd)
		if cnt <= 0:
			try:
				os_remove(FILENAME)
			except OSError, oe:
				pass
			result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
				<e2simplexmlresult>\n
					<e2state>False</e2state>
					<e2statetext>Error writing to disk, not uploaded</e2statetext>
				</e2simplexmlresult>\n"""
		else:
			result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
				<e2simplexmlresult>\n
					<e2state>True</e2state>
					<e2statetext>%s</e2statetext>
				</e2simplexmlresult>\n""" % self.FILENAME
		return result

