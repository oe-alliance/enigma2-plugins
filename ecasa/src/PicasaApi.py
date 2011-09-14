from __future__ import print_function

#pragma mark - Picasa API

import gdata.photos.service
import gdata.media
import gdata.geo
import os

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.web.client import downloadPage

def list_recursive(dirname):
	for file in os.listdir(dirname):
		fn = os.path.join(dirname, file)
		if os.path.isfile(fn):
			yield fn
		elif os.path.isdir(fn):
			for f in list_recursive(fn):
				yield f

def remove_empty(dirname):
	files = os.listdir(dirname)
	if files:
		for file in os.listdir(dirname):
			fn = os.path.join(dirname, file)
			if os.path.isdir(fn):
				remove_empty(fn)
	else:
		try:
			os.rmdir(dirname)
		except OSError as ose:
			print("Unable to remove directory", dirname + ":", ose)

#_PicasaApi__returnPhotos = lambda photos: [(photo.title.text, photo) for photo in photos.entry]
_PicasaApi__returnPhotos = lambda photos: photos.entry

class PicasaApi:
	"""Wrapper around gdata/picasa API to make our life a little easier."""
	def __init__(self, email=None, password=None, cache='/tmp/ecasa'):
		"""Initialize API, login to google servers"""
		gd_client = gdata.photos.service.PhotosService()
		gd_client.source = 'enigma2-plugin-extensions-ecasa'
		if email and password:
			gd_client.email = email
			gd_client.password = password
			# NOTE: this might fail
			gd_client.ProgrammaticLogin()

		self.gd_client = gd_client
		self.cache = cache

	def setCredentials(self, email, password):
		# TODO: check if this is sane
		gd_client = self.gd_client
		gd_client.email = email
		gd_client.password = password
		if email and password:
			# NOTE: this might fail
			gd_client.ProgrammaticLogin()

	def getAlbums(self, user='default'):
		albums = self.gd_client.GetUserFeed(user=user)
		return [(album.title.text, album.numphotos.text, album) for album in albums.entry]

	def getSearch(self, query, limit='10'):
		photos = self.gd_client.SearchCommunityPhotos(query, limit=str(limit))
		return __returnPhotos(photos)

	def getAlbum(self, album):
		photos = self.gd_client.GetFeed(album.GetPhotosUri())
		return __returnPhotos(photos)

	def getTags(self, feed):
		tags = self.gd_client.GetFeed(feed.GetTagsUri())
		return [(tag.summary.text, tag) for tag in tags.entry]

	def getComments(self, feed):
		comments = self.gd_client.GetCommentFeed(feed.GetCommentsUri())
		return [(comment.summary.text, comment) for comment in comments.entry]

	def getFeatured(self):
		featured = self.gd_client.GetFeed('/data/feed/base/featured')
		return __returnPhotos(featured)

	def downloadPhoto(self, photo, thumbnail=False):
		if not photo: return

		cache = os.path.join(self.cache, 'thumb', photo.albumid.text) if thumbnail else os.path.join(self.cache, photo.albumid.text)
		try: os.makedirs(cache)
		except OSError: pass

		url = photo.media.thumbnail[0].url if thumbnail else photo.media.content[0].url
		filename = url.split('/')[-1]
		fullname = os.path.join(cache, filename)
		d = Deferred()
		# file exists, assume it's valid...
		if os.path.exists(fullname):
			reactor.callLater(0, d.callback, (fullname, photo))
		else:
			downloadPage(url, fullname).addCallbacks(
				lambda value:d.callback((fullname, photo)),
				lambda error:d.errback((error, photo)))
		return d

	def downloadThumbnail(self, photo):
		return self.downloadPhoto(photo, thumbnail=True)

	def cleanupCache(self, maxSize):
		"""
			Housekeeping for our download cache.
			Removes pictures and thumbnails (oldest to newest) until the cache is smaller than maxSize MB.
		"""
		stat = os.stat
		maxSize *= 1048576 # input size is assumed to be in mb, but we work with bytes internally

		files = [(f, stat(f)) for f in list_recursive(self.cache)]
		curSize = sum(map(lambda x: x[1].st_size, files))
		if curSize > maxSize:
			files.sort(key=lambda x: x[1].st_mtime)
			while curSize > maxSize:
				file, stat = files.pop(0)
				try:
					os.unlink(file)
				except Exception as e:
					print("[PicasaApi] Unable to unlink file", file + ":", e)
				else:
					curSize -= stat.st_size
			remove_empty(self.cache)

__all__ = ['PicasaApi']
