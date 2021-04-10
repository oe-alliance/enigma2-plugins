# -*- coding: utf-8 -*-
#######################################################################
#
#    Series Plugin for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=TBD
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

from __future__ import absolute_import
import os
import re
from glob import glob #Py3 ,escape

# for localized messages
from . import _

# Config
from Components.config import config

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

from Tools.BoundFunction import boundFunction
from Tools.ASCIItranslit import ASCIItranslit

from enigma import eServiceCenter, iServiceInformation, eServiceReference
from ServiceReference import ServiceReference

# Plugin internal
from .SeriesPlugin import getInstance, refactorTitle, refactorDescription, refactorDirectory
from .Logger import log

import six


CompiledRegexpGlobEscape = re.compile('([\[\]\?*])')  # "[\\1]"


# By Bin4ry
def newLegacyEncode(string):
	string2 = ""
	for z, char in enumerate(string.decode("utf-8")):
		i = ord(char)
		if i < 33:
			string2 += " "
		elif i in ASCIItranslit:
			# There is a bug in the E2 ASCIItranslit some (not all) german-umlaut(a) -> AE
			if char.islower():
				string2 += ASCIItranslit[i].lower()
			else:
				string2 += ASCIItranslit[i]

		else:
			try:
				string2 += char.encode('ascii', 'strict')
			except:
				string2 += " "
	return string2


def rename(servicepath, name, short, data):
	# Episode data available
	log.debug("rename:", data)
	result = True

	#MAYBE Check if it is already renamed?
	try:
		# Before renaming change content
		rewriteMeta(servicepath, name, data)
	except Exception as e:
		log.exception("rewriteMeta:", str(e))
		result = "rewriteMeta:" + str(e)

	if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":

		if config.plugins.seriesplugin.rename_file.value == True:

			try:
				renameFiles(servicepath, name, data)
			except Exception as e:
				log.exception("renameFiles:", str(e))
				result = "renameFiles:" + str(e)

	return result


# Adapted from MovieRetitle setTitleDescr
def rewriteMeta(servicepath, name, data):
	#TODO Use MetaSupport EitSupport classes from EMC ?
	if servicepath.endswith(".ts"):
		meta_file = servicepath + ".meta"
	else:
		meta_file = servicepath + ".ts.meta"

	# Create new meta for ts files
	if not os.path.exists(meta_file):
		if os.path.isfile(servicepath):
			_title = os.path.basename(os.path.splitext(servicepath)[0])
		else:
			_title = name
		_sid = ""
		_descr = ""
		_time = ""
		_tags = ""
		metafile = open(meta_file, "w")
		metafile.write("%s\n%s\n%s\n%s\n%s" % (_sid, _title, _descr, _time, _tags))
		metafile.close()

	if os.path.exists(meta_file):
		metafile = open(meta_file, "r")
		sid = metafile.readline()
		oldtitle = metafile.readline().rstrip()
		olddescr = metafile.readline().rstrip()
		rest = metafile.read()
		metafile.close()

		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":
			title = refactorTitle(oldtitle, data)
		else:
			title = oldtitle
		log.debug("title", title)
		if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off":
			descr = refactorDescription(olddescr, data)
		else:
			descr = olddescr
		log.debug("descr", descr)

		metafile = open(meta_file, "w")
		metafile.write("%s%s\n%s\n%s" % (sid, title, descr, rest))
		metafile.close()
	return True


def renameFiles(servicepath, name, data):
	log.debug("servicepath", servicepath)

	path = os.path.dirname(servicepath)
	file_name = os.path.basename(os.path.splitext(servicepath)[0])
	log.debug("file_name", file_name)

	log.debug("name     ", name)
	# Refactor title
	name = refactorTitle(file_name, data)
	log.debug("name     ", name)
	#if config.recording.ascii_filenames.value:
	#	filename = ASCIItranslit.legacyEncode(filename)
	if config.plugins.seriesplugin.rename_legacy.value:
		name = newLegacyEncode(name)
		log.debug("name     ", name)

	src = os.path.join(path, file_name)
	log.debug("servicepathSrc", src)

	path = refactorDirectory(path, data)
	dst = os.path.join(path, name)
	log.debug("servicepathDst", dst)

	return osrename(src, dst)


def osrename(src, dst):
	#Py3 for f in glob( escape(src) + "*" ):
	glob_src = CompiledRegexpGlobEscape.sub("[\\1]", src)
	log.debug("glob_src      ", glob_src)
	for f in glob(glob_src + ".*"):
		log.debug("servicepathRnm", f)
		to = f.replace(src, dst)
		log.debug("servicepathTo ", to)

		if not os.path.exists(to):
			try:
				os.rename(f, to)
			except:
				log.exception("rename error", f, to)
		elif config.plugins.seriesplugin.rename_existing_files.value:
			log.debug("Destination file already exists", to, " - Append '_'")
			return osrename(src, dst + "_")
			break
		else:
			log.warning(_("Skipping rename because file already exists") + "\n" + to + "\n\n" + _("Can be configured within the setup"))
	return True


#######################################################
# Rename movies
class SeriesPluginRenamer(object):
	def __init__(self, session, services, *args, **kwargs):

		log.info("SeriesPluginRenamer: services, service:", str(services))

		if services and not isinstance(services, list):
			services = [services]

		self.services = services

		self.data = []
		self.counter = 0

		session.openWithCallback(
			self.confirm,
			MessageBox,
			_("Do You want to start renaming?"),
			MessageBox.TYPE_YESNO,
			timeout=15,
			default=True
		)

	def confirm(self, confirmed):
		if confirmed and self.services:
			serviceHandler = eServiceCenter.getInstance()

			try:
				for service in self.services:

					seriesPlugin = getInstance()

					if isinstance(service, eServiceReference):
						service = service
					elif isinstance(service, ServiceReference):
						service = service.ref
					else:
						log.debug("Wrong instance")
						continue

					servicepath = service.getPath()

					if not os.path.exists(servicepath):
						log.debug("File not exists: " + servicepath)
						continue

					info = serviceHandler.info(service)
					if not info:
						log.debug("No info available: " + servicepath)
						continue

					short = ""
					begin = None
					end = None
					duration = 0

					event = info.getEvent(service)
					if event:
						name = event.getEventName() or ""
						short = event.getShortDescription()
						begin = event.getBeginTime()
						duration = event.getDuration() or 0
						end = begin + duration or 0
						# We got the exact start times, no need for margin handling
						log.debug("event")
					else:
						name = service.getName() or info.getName(service) or ""
						if name[-2:] == 'ts':
							name = name[:-2]
						log.debug("not event")

					if not begin:
						begin = info.getInfo(service, iServiceInformation.sTimeCreate) or -1
						if begin != -1:
							end = begin + (info.getLength(service) or 0)
						else:
							end = os.path.getmtime(servicepath)
							begin = end - (info.getLength(service) or 0)

						#MAYBE we could also try to parse the filename
						log.debug("We don't know the exact margins, we will assume the E2 default margins")
						begin -= (int(config.recording.margin_before.value) * 60)
						end += (int(config.recording.margin_after.value) * 60)

					rec_ref_str = info.getInfoString(service, iServiceInformation.sServiceref)
					#channel = ServiceReference(rec_ref_str).getServiceName()

					log.debug("getEpisode:", name, begin, end, rec_ref_str)
					seriesPlugin.getEpisode(
							boundFunction(self.renamerCallback, servicepath, name, short),
							name, begin, end, rec_ref_str, elapsed=True, block=True, rename=True
						)

			except Exception as e:
				log.exception("Exception:", str(e))

	def renamerCallback(self, servicepath, name, short, data=None):
		log.debug("renamerCallback", name, data)

		result = None

		if data and isinstance(data, dict):
			result = rename(servicepath, name, short, data)

		elif data and isinstance(data, six.string_types):
			msg = _("Failed: %s." % (str(data)))
			log.debug(msg)
			self.data.append(name + ": " + msg)

		else:
			msg = _("No data available")
			log.debug(msg)
			self.data.append(name + ": " + msg)

		self.counter = self.counter + 1

		# Maybe there is a better way to avoid multiple Popups
		from .SeriesPlugin import getInstance

		instance = getInstance()

		if instance.thread.empty() and instance.thread.finished():
			if self.data:
				msg = "SeriesPlugin:\n" + _("Record rename has been finished with %d errors:\n") % (len(self.data)) + "\n" + "\n".join(self.data)
				log.warning(msg)

			else:
				if self.counter > 0:
					msg = "SeriesPlugin:\n" + _("%d records renamed successfully") % (self.counter)
					log.success(msg)

			self.data = []
			self.counter = 0
