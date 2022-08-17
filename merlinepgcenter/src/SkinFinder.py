from __future__ import print_function
#
#  SkinFinder E2
#
#  $Id: SkinFinder.py,v 1.0 2011-06-28 00:00:00 shaderman Exp $
#
#  Coded by Shaderman (c) 2011
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#

# PYTHON IMPORTS
from glob import iglob
from os.path import basename as path_basename

# ENIGMA IMPORTS
from enigma import getDesktop
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN

# DESCRIPTION:
"""
SKINDIR:
A subdirectory of you plugin where required default skins (HD_default.xml, XD_default.xml and SD_default.xml) can be found
along with more (optional) custom skins.

SKINLIST:
A list of 3 tuples (full path and filename of a skin file, basename of the skin file).

config.plugins.yourConfigText.skin.value:
A ConfigText value of a skin filename.

getSkinData() checks if a skin file set in config.plugins.yourConfigText.skin.value can be found in SKINDIR. If it's found,
it'll be returned together with a list of all skins found in SKINDIR (thos files with a .xml ending). If it can't be found,
the matching skin file for the detected reolution will be returned along with a list of all skins found in SKINDIR.
These return values can be used by a ConfigSelection object to build a choice list with a default choice value
(config.plugins.yourConfigSelection.skinSelection.setChoices(skinList, default = skinFile)).
This function can also be called for example on plugin start to load a selected skin (skin.loadSkin), or to refresh the
ConfigSelection choices when plugin settings are shown.
"""

# USAGE EXAMPLE:
"""
SKINDIR = "Extensions/YourPlugin/skins/"

SKINLIST =	[ # order is important (HD, XD, SD)!
		(resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SKINDIR, "HD_default.xml"])), "HD_default.xml"),
		(resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SKINDIR, "XD_default.xml"])), "XD_default.xml"),
		(resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SKINDIR, "SD_default.xml"])), "SD_default.xml")
		]

class YourClass():
	(skinFile, skinList) = SkinFinder.getSkinData(SKINLIST, SKINDIR, config.plugins.yourConfigText.skin.value)
	if skinFile is not None:
		if config.plugins.yourConfigText.skin.value != skinFile:
			config.plugins.yourConfigText.skin.value = skinFile
			config.plugins.yourConfigText.skin.save()
		config.plugins.yourConfigSelection.skinSelection.setChoices(skinList, default = skinFile)
		loadSkin(skinFile, "")
"""


class SkinFinder(object):
	skinList = None
	skinDir = None

	@staticmethod
	def getSkinData(skinList, skinDir, currentSkinValue):
		SkinFinder.skinList = skinList[:]  # we don't want the passed list to be modified, let's use a copy instead
		SkinFinder.skinDir = skinDir

		if currentSkinValue == "":
			firstRun = True
		else:
			firstRun = False

		# build a list of the filenames from our (default) skin list
		skinListFiles = [x[0] for x in SkinFinder.skinList]

		# try to find additional skins and add them to our list
		path = resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([skinDir, "*.xml"]))
		for fileName in iglob(path):
			if not fileName in skinListFiles:
				baseName = path_basename(fileName)
				SkinFinder.skinList.append((fileName, baseName))
				if not firstRun:
					skinListFiles.append(fileName)

		if not firstRun:
			# try to find the config value in our list of files
			if currentSkinValue in skinListFiles:
				skinIndex = skinListFiles.index(currentSkinValue)
			else:
				# fall back to the default skin
				print('[SkinFinder] unable to find skin file %s, tryig to load a default skin' % currentSkinValue)
				skinIndex = SkinFinder.getDefaultSkinEntry()
		else:
			# get the index of the detected skin in our list of default skins
			skinIndex = SkinFinder.getDefaultSkinEntry()

		if skinIndex is not None:
			skinFile = SkinFinder.skinList[skinIndex][0]
			print('[SkinFinder] found skin file', skinFile)
			return skinFile, SkinFinder.skinList
		else:
			print('[SkinFinder] unable to find any skin!')
			return None

	@staticmethod
	def getDefaultSkinEntry():
		desktopSize = getDesktop(0).size()
		if desktopSize.width() == 1280:
			fileName = resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SkinFinder.skinDir, SkinFinder.skinList[0][1]]))
		elif desktopSize.width() == 1024:
			fileName = resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SkinFinder.skinDir, SkinFinder.skinList[1][1]]))
		elif desktopSize.width() == 720:
			fileName = resolveFilename(SCOPE_CURRENT_PLUGIN, ''.join([SkinFinder.skinDir, SkinFinder.skinList[2][1]]))
		else:
			fileName = None

		if fileName is not None:
			try:
				index = [x[0] for x in SkinFinder.skinList].index(fileName)
				return index
			except ValueError:
				pass

		print('[SkinFinder] skin index error! File:', fileName)
		return None
