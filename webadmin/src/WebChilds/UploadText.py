# -*- coding: utf-8 -*-
from __future__ import print_function
from os import statvfs, path as os_path, chmod as os_chmod, write as os_write, close as os_close, unlink as os_unlink, rename as os_rename
from twisted.web import resource, http
from tempfile import mkstemp
from .. import _


def _arg_str(req, key, default=""):
	value = req.args.get(key, [default])[0]
	if isinstance(value, bytes):
		return value.decode("utf-8", "ignore")
	return value


class UploadTextResource(resource.Resource):
	default_uploaddir = "/tmp/"

	def render_POST(self, req):
		uploaddir = self.default_uploaddir
		print("[UploadTextResource] req.args ", req.args)
		req_path = _arg_str(req, 'path')
		if req_path:
			if os_path.isdir(req_path):
				uploaddir = req_path
				if uploaddir[-1] != "/":
					uploaddir += "/"
			else:
				print("[UploadTextResource] not a dir", req_path)
				req.setResponseCode(http.OK)
				req.setHeader(b'Content-type', b'text/html; charset=UTF-8')
				return ("path '%s' to upload not existing!" % req_path).encode("utf-8")

		if uploaddir[:10] != "/etc/opkg/" and uploaddir[:12] != "/usr/script/":
			req.setResponseCode(http.OK)
			req.setHeader(b'Content-type', b'text/html; charset=UTF-8')
			return ("illegal upload directory: " + uploaddir).encode("utf-8")

		data = _arg_str(req, 'text') or _arg_str(req, 'textarea')
		data = data.replace('\r\n', '\n')
		if not data:
			req.setResponseCode(http.OK)
			req.setHeader(b'Content-type', b'text/html; charset=UTF-8')
			return b"filesize was 0, not uploaded"
		print("[UploadTextResource] text:", data)

		filename = _arg_str(req, 'filename')
		fd, fn = mkstemp(dir=uploaddir)
		cnt = os_write(fd, data.encode("utf-8"))
		os_close(fd)
		os_chmod(fn, 0o755)

		if cnt <= 0:
			try:
				os_unlink(fn)
			except OSError:
				pass
			req.setResponseCode(http.OK)
			req.setHeader(b'Content-type', b'text/html; charset=UTF-8')
			return b"error writing to disk, not uploaded"

		file = uploaddir + filename
		os_rename(fn, file)
		req.setResponseCode(http.OK)
		req.setHeader(b'Content-type', b'text/html; charset=UTF-8')
		return ("""
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
					</html>""" % (file, _("Close"))).encode("utf-8")

	def render_GET(self, req):
		try:
			stat = statvfs("/tmp/")
		except OSError:
			return b"-1"

		freespace = stat.f_bfree / 1000 * stat.f_bsize / 1000

		req.setResponseCode(http.OK)
		req.setHeader(b'Content-type', b'text/html; charset=UTF-8')
		return ("""
				<form method="POST" enctype="multipart/form-data">
				<table>
				<tr><td>Path to save (default is '%s')</td><td><input name="path"></td></tr>
				<tr><td>Filename to save<input name="filename"></td></tr>
				<tr><textarea name="textarea" rows=10 cols=100>bla...</textarea></tr>
				<tr><td colspan="2">Filesize must not be greather than %dMB! /tmp/ has not more free space!</td></tr>
				<tr><td colspan="2"><input type="submit"><input type="reset"></td><tr>
				</table>
				</form>
		""" % (self.default_uploaddir, freespace)).encode("utf-8")
