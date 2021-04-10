# -*- coding: utf-8 -*-
# by betonme @2015

# for localized messages
from __future__ import absolute_import
from . import _

from Components.config import *

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

# Plugin internal
from .SeriesPluginTimer import SeriesPluginTimer
from .Logger import log


import six


loop_data = []
loop_counter = 0


def bareGetEpisode(service_ref, name, begin, end, description, path, future=True, today=False, elapsed=False):
	result = _("SeriesPlugin is deactivated")
	if config.plugins.seriesplugin.enabled.value:

		log.start()

		log.info("Bare:", service_ref, name, begin, end, description, path, future, today, elapsed)

		from .SeriesPlugin import getInstance, refactorTitle, refactorDescription, refactorDirectory
		seriesPlugin = getInstance()
		data = seriesPlugin.getEpisode(
			None,
			name, begin, end, service_ref, future, today, elapsed, block=True
		)
		global loop_data
		global loop_counter
		loop_counter += 1

		if data and isinstance(data, dict):
			name = str(refactorTitle(name, data))
			description = str(refactorDescription(description, data))
			path = refactorDirectory(path, data)
			log.info("Bare: Success", name, description, path)
			return (name, description, path, log.get())

		elif data and isinstance(data, six.string_types):
			msg = _("Failed: %s." % (str(data)))
			log.debug(msg)
			loop_data.append(name + ": " + msg)

		else:
			msg = _("No data available")
			log.debug(msg)
			loop_data.append(name + ": " + msg)

		log.info("Bare: Failed", str(data))
		return str(data)

	return result


def bareShowResult():
	global loop_data, loop_counter

	if loop_data:
		msg = "SeriesPlugin:\n" + _("Finished with errors:\n") + "\n" + "\n".join(loop_data)
		log.warning(msg)

	else:
		if loop_counter > 0:
			msg = "SeriesPlugin:\n" + _("Lookup of %d episodes was successful") % (loop_counter)
			log.success(msg)

	loop_data = []
	loop_counter = 0
