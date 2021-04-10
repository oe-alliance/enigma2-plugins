# -*- coding: utf-8 -*-
from __future__ import print_function
from os import statvfs, path as os_path, chmod as os_chmod, write as os_write, \
		close as os_close, unlink as os_unlink, open as os_open, rename as os_rename, O_WRONLY, \
		O_CREAT
from twisted.web import resource, http
from tempfile import mkstemp
from re import search


class UploadTextResource(resource.Resource):
	default_uploaddir = "/tmp/"

	def render_POST(self, req):
		uploaddir = self.default_uploaddir
		print("[UploadTextResource] req.args ", req.args)
		if req.args['path'][0]:
			if os_path.isdir(req.args['path'][0]):
				uploaddir = req.args['path'][0]
				if uploaddir[-1] != "/":
					uploaddir += "/"
			else:
				print("[UploadTextResource] not a dir", req.args['path'][0])
				req.setResponseCode(http.OK)
				req.setHeader('Content-type', 'text/html')
				return "path '%s' to upload not existing!" % req.args['path'][0]
			
			if uploaddir[:10] == "/etc/opkg/" or uploaddir[:12] == "/usr/script/":
				pass
			else:
				req.setResponseCode(http.OK)
				req.setHeader('Content-type', 'text/html')
				return "illegal upload directory: " + req.args['path'][0]

			data = req.args['text'][0].replace('\r\n', '\n')
		if not data:
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'text/html')
			return "filesize was 0, not uploaded"
		else:
			print("[UploadTextResource] text:", data)

		filename = req.args['filename'][0]

		fd, fn = mkstemp(dir=uploaddir)
		cnt = os_write(fd, data)
		os_close(fd)
		os_chmod(fn, 0o755)
		
		if cnt <= 0: # well, actually we should check against len(data) but lets assume we fail big time or not at all
			try:
				os_unlink(fn)
			except OSError as oe:
				pass
			req.setResponseCode(http.OK)
			req.setHeader('Content-type', 'text/html')
			return "error writing to disk, not uploaded"
		else:
			file = uploaddir + filename
			os_rename(fn, file)
			return """
					<?xml version="1.0" encoding="UTF-8"?>
					<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
							"http://www.w3.org/TR/html4/loose.dtd">
					<html>
					
					<head>
					<meta content="text/html; charset=UTF-8" http-equiv="content-type">
					
					<link href="/web-data/tpl/default/style.min.css" type="text/css" rel="stylesheet">
					<link rel="shortcut icon" type="image/x-icon" href="/web-data/img/favicon.ico">
					</head>
					<body onunload="javascript:opener.location.reload()" >
						<hr>
						<p align="left">
						uploaded to %s
						</p>
						<hr>
						<form>
							<input type="button" value="%s" onClick="window.close();">
						</form>
					</body>
					</html>""" % (file, _("Close"))

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
				<tr><td>Filename to save<input name="filename"></td></tr>
				<tr><textarea name="textarea" rows=10 cols=100>bla...</textarea></tr>
				<tr><td colspan="2">Filesize must not be greather than %dMB! /tmp/ has not more free space!</td></tr>
				<tr><td colspan="2"><input type="submit"><input type="reset"></td><tr>
				</table>
				</form>
		""" % (self.default_uploaddir, freespace)
