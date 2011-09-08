from __future__ import print_function

#from Plugins.Plugin import PluginDescriptor

#pragma mark - Picasa API

import gdata.photos.service
import gdata.media
import gdata.geo

class PicasaApi:
	"""Wrapper around gdata/picasa API to make our life a little easier."""
	def __init__(self, email, password):
		"""Initialize API, login to google servers"""
		gd_client = gdata.photos.service.PhotosService()
		gd_client.email = email
		gd_client.password = password
		gd_client.source = 'enigma2-plugin-extensions-ecasa'
		gd_client.ProgrammaticLogin()

		self.gd_client = gd_client

	def getAlbums(self, user='default'):
		albums = self.gd_client.GetUserFeed(user=user)
		# flatten list to something our gui renderers can handle more easily
		return [(album.title.text, album.numphotos.text, user, album.gphoto_id.text, album) for album in albums.entry]

	def getAlbum(self, gphoto_id, user='default'):
		photos = self.gd_client.GetFeed('/data/feed/api/user/%s/albumid/%s?kind=photo' % (user, gphoto_id))
		return [(photo.title.text, user, photo.gphoto_id.text, photo) for photo in photos.entry]

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
			l = api.getAlbum(l[0][3])
			print("Pictures in first album:", l)
			print("Thumbnail of first picture could be found under:", l[0][3].media.thumbnail[0].url)
			print("Picture should be:", l[0][3].media.content[0].url)
