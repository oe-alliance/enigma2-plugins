# -*- coding: utf-8 -*-
from __future__ import print_function
from os import rename as os_rename,\
	chmod as os_chmod,\
	write as os_write,\
	close as os_close,\
	unlink as os_unlink, \
	popen as os_popen
from tempfile import mkstemp
from twisted.web import resource, http

from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild

def mbasename(fname):
	l = fname.split('/')
	win = l[len(l)-1]
	l2 = win.split('\\')
	return l2[len(l2)-1]
	
class UploadPkgResource(resource.Resource):
	res="""
	<?xml version="1.0" encoding="UTF-8"?>
	<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
			"http://www.w3.org/TR/html4/loose.dtd">
	<html>
					
	<head>
		<link rel="shortcut icon" type="/web-data/image/x-icon" href="/web-data/img/favicon.ico">
		<meta content="text/html; charset=UTF-8" http-equiv="content-type">
		<script type="text/javascript">
		</script>
	</head>
	<body onunload="javascript:opener.location.reload()" >
		<p>Ipk: %s</p>
		<br>
		<form>
			<input type="button" value="%s" onClick="javascript:window.close();">
			<input type="button" value="Package %s" onClick="javascript:location='uploadpkg'";>
		</form>
	</body>
	</html>
	"""
			
	def render_POST(self, req):
		data = req.args['file'][0]
		print("[filename req.args]", req.args['filename'][0])
		filename = mbasename(req.args['filename'][0])
		print("[filename]", filename)
		if not filename.endswith(".ipk"):
			return self.res % (_("wrong filetype!"), _("Close"), _("Add"))
		
		if not data:
			req.setResponseCode(http.OK)
			return self.res % ( _("filesize was 0, not uploaded"),
					_("Close"),
					 _("Add")
					)
		
		fd, fn = mkstemp(dir = "/tmp/")
		cnt = os_write(fd, data)
		os_close(fd)
		os_chmod(fn, 0o755)
		
		if cnt <= 0: # well, actually we should check against len(data) but lets assume we fail big time or not at all
			try:
				os_unlink(fn)
			except OSError as oe:
				pass
			req.setResponseCode(http.OK)
			return  self.res % (_("error writing to disk, not uploaded"), _("Close"), _("Add"))
		
		else:
			file = "/tmp/" + filename
			os_rename(fn, (file))
			if file is not None:
				out = os_popen("opkg install %s" %file)
				debug = ""
				for line in out:
					debug += line
			else:
				return  self.res % (_("error writing to disk, not uploaded"), _("Close"), _("Add"))

			req.setResponseCode(http.OK)
			return self.res % ((debug),
					_("Close"),
					 _("Add")
					)

	def render_GET(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'text/html')
		return """
				<?xml version="1.0" encoding="UTF-8"?>
				<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
						"http://www.w3.org/TR/html4/loose.dtd">
				<html>
					
				<head>
				<link rel="shortcut icon" type="/web-data/image/x-icon" href="/web-data/img/favicon.ico">
				<meta content="text/html; charset=UTF-8" http-equiv="content-type">
				<script type="text/javascript">
				function getPkgFilename(){
					var frm = document.forms["form_uploadpkg"];
					frm.filename.value = frm.file.value;
				}
				</script>
				</head>
				<body onunload="javascript:opener.location.reload()" onload="window.scrollBy(0,1000000);" >
				<form name="form_uploadpkg" method="POST" enctype="multipart/form-data">
				Ipk %s:
				<input name="file" type="file" size="50" maxlength="100000" accept="text/*" onchange="getPkgFilename();">
				<br>
				<input type="hidden" name="filename" value="">
				<input type="submit">
				</form>
				</body>
				</html>
		""" % _("Add")
