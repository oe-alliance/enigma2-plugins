from os import statvfs, path as os_path, chmod as os_chmod, write as os_write, \
		close as os_close, unlink as os_unlink, open as os_open, O_WRONLY, \
		O_CREAT
from twisted.web import resource, http
from tempfile import mkstemp
from re import search

class UploadResource(resource.Resource):
	default_uploaddir = "/tmp/"

	def render_POST(self, req):
		uploaddir = self.default_uploaddir
		if req.args['path'][0]:
			if os_path.isdir(req.args['path'][0]):
				uploaddir = req.args['path'][0]
				if uploaddir[-1] != "/":
					uploaddir += "/"
			else:
				req.setResponseCode(http.OK)
				req.setHeader('Content-type', 'text/html')
				return "path '%s' to upload not existing!" % req.args['path'][0]

		data = req.args['file'][0]
		if not data:
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'text/html')
			return "filesize was 0, not uploaded"

		try:
			matches = search('.*?filename="(.*?)"\r\n.*?', req.content.getvalue())
			fn=os_path.join(uploaddir, matches.group(1))
		except Exception, e:
			fn= None

		# NOTE: we only accept the given filename if no such file exists yet
		if fn and not os_path.exists(fn):
			fd = os_open(fn, O_WRONLY | O_CREAT)
		else:
			fd, fn = mkstemp(dir = uploaddir)
		cnt = os_write(fd, data)
		os_close(fd)
		os_chmod(fn, 0755)
		
		if cnt <= 0: # well, actually we should check against len(data) but lets assume we fail big time or not at all
			try:
				os_unlink(fn)
			except OSError, oe:
				pass
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'text/html')
			return "error writing to disk, not uploaded"
		else:
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'text/html')
			return "uploaded to %s" % fn

	def render_GET(self, req):
		try:
			stat = statvfs("/tmp/")
		except OSError:
			return - 1

		freespace = stat.f_bfree / 1000 * stat.f_bsize / 1000

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		return """
				<form method="POST" enctype="multipart/form-data">
				<table>
				<tr><td>Path to save (default is '%s')</td><td><input name="path"></td></tr>
				<tr><td>File to upload</td><td><input name="file" type="file"></td></tr>
				<tr><td colspan="2">Filesize must not be greather than %dMB! /tmp/ has not more free space!</td></tr>
				<tr><td colspan="2"><input type="submit"></td><tr>
				</table>
				</form>
		""" % (self.default_uploaddir, freespace)

