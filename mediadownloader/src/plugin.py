from __future__ import absolute_import
#
# To be used as simple Downloading Application by other Plugins
#

# for localized messages
from . import _

from Components.config import config, ConfigSubsection, ConfigLocations
from Tools.Directories import resolveFilename, SCOPE_HDD

# SCOPE_HDD is not really what we want but the best we can get :-)
config.plugins.mediadownloader = ConfigSubsection()
config.plugins.mediadownloader.bookmarks = ConfigLocations(default=[resolveFilename(SCOPE_HDD)])

# TODO: support custom bookmark element?

# Download a single File
def download_file(session, url, to=None, askOpen=False, callback=None,
	**kwargs):
	"""Provides a simple downloader Application"""

	from Components.Scanner import ScanFile
	file = ScanFile(url, autodetect=False)

	from .MediaDownloader import MediaDownloader
	session.open(MediaDownloader, file, askOpen, to, callback)

# Item chosen
def filescan_chosen(session, item):
	if item:
		from .MediaDownloader import MediaDownloader

		session.open(MediaDownloader, item[1], askOpen=True)

# Open as FileScanner
def filescan_open(items, session, **kwargs):
	"""Download a file from a given List"""

	Len = len(items)
	if Len > 1:
		from Screens.ChoiceBox import ChoiceBox
		from Tools.BoundFunction import boundFunction

		# Create human-readable filenames
		choices = [
			(
				item.path[item.path.rfind("/")+1:].replace('%20', ' ').
					replace('%5F', '_').replace('%2D', '-'),
				item
			)
				for item in items
		]

		# And let the user choose one
		session.openWithCallback(
			boundFunction(filescan_chosen, session),
			ChoiceBox,
			_("Which file do you want to download?"),
			choices
		)
	elif Len:
		from .MediaDownloader import MediaDownloader

		session.open(MediaDownloader, items[0], askOpen=True)

# Return Scanner provided by this Plugin
def filescan(**kwargs):
	from Components.Scanner import Scanner, ScanPath

	# Overwrite checkFile to detect remote files
	class RemoteScanner(Scanner):
		def checkFile(self, file):
			return file.path.startswith(("http://", "https://", "ftp://"))

	return [
		RemoteScanner(
			mimetypes=None,
			paths_to_scan=[
					ScanPath(path="", with_subdirs=False),
				],
			name="Download",
			description=_("Download..."),
			openfnc=filescan_open,
		)
	]

def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor

	return [
		PluginDescriptor(
			name="MediaDownloader",
			where=PluginDescriptor.WHERE_FILESCAN,
			fnc=filescan,
			needsRestart=False,
		)
	]
