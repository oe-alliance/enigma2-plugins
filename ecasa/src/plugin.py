from __future__ import print_function

#from Plugins.Plugin import PluginDescriptor

#pragma mark - Picasa API

import gdata.photos.service
import gdata.media
import gdata.geo
import os

from twisted.web.client import downloadPage

_PicasaApi__returnPhotos = lambda photos: [(photo.title.text, photo.summary.text, photo) for photo in photos.entry]

class PicasaApi:
	"""Wrapper around gdata/picasa API to make our life a little easier."""
	def __init__(self, email, password, cache='/tmp/ecasa'):
		"""Initialize API, login to google servers"""
		gd_client = gdata.photos.service.PhotosService()
		gd_client.email = email
		gd_client.password = password
		gd_client.source = 'enigma2-plugin-extensions-ecasa'
		# NOTE: this might fail
		gd_client.ProgrammaticLogin()

		self.gd_client = gd_client
		self.cache = cache

	def getAlbums(self, user='default'):
		albums = self.gd_client.GetUserFeed(user=user)
		return [(album.title.text, album.numphotos.text, album) for album in albums.entry]

	def getSearch(self, query, limit='10'):
		photos = gd_client.SearchCommunityPhotos(query, limit=str(limit))
		return __returnPhotos(photos)

	def getAlbum(self, album):
		photos = self.gd_client.GetFeed(album.GetPhotosUri())
		return __returnPhotos(photos)

	def getTags(self, feed):
		tags = self.gd_client.GetFeed(feed.GetTagsUri())
		return [(tag.summary.text, tag) for tag in tags.entry]

	def getComments(self, feed):
		comments = self.gd_client.GetCommentFeed(feed.GetCommentsUri())
		return [(comment.summary.text, comment) for comment in comments]

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
		return downloadPage(url, os.path.join(cache, filename))

	def downloadThumbnail(self, photo):
		return self.downloadPhoto(photo, thumbnail=True)

#pragma mark - GUI

#pragma mark - Plugin

def Plugins(**kwargs):
	return [
	]

if __name__ == '__main__':
	import sys
	if not len(sys.argv) > 2:
		print("Not enough parameters, aborting...")
	else:
		api = PicasaApi(sys.argv[1], sys.argv[2])
		l = api.getAlbums()
		print("List of Albums:", l)
		if l:
			l = api.getAlbum(l[0][2])
			print("Pictures in first album:", l)
			print("Thumbnail of first picture could be found under:", l[0][2].media.thumbnail[0].url)
			print("Picture should be:", l[0][2].media.content[0].url)
		l = api.getFeatured()
		print("Featured Pictures:", l)
