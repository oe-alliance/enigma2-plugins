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
import json

# for localized messages
from . import _

# Config
from Components.config import *

# Plugin internal
from .Logger import log


scheme_fallback = [
		("Off", "Disabled"),

		("{org:s}/{series:s}/{season:02d}/", "Original/Series/01/"),
		("{org:s}/{series:s}/S{season:02d}/", "Original/Series/S01/"),
		("{org:s}/{series:s}/{rawseason:s}/", "Original/Series/Raw/"),

		("{org:s}/{series:s}/Season {season:02d}/", "Original/Series/Season 01/"),
		("{org:s}/{series:s}/Season {rawseason:s}/", "Original/Series/Season Raw/"),

		("{org:s}/{series:s} {season:02d}/", "Original/Series 01/"),
		("{org:s}/{series:s} S{season:02d}/", "Original/Series S01/"),

		("{org:s}/{series:s} Season {season:02d}/", "Original/Series Season 01/"),
		("{org:s}/{series:s} Season {rawseason:s}/", "Original/Series Season Raw/"),

		("{org:s}/{service:s}/{series:s}/Season {rawseason:s}/", "Original/Service/Series/Season Raw/"),
		("{org:s}/{channel:s}/{series:s}/Season {rawseason:s}/", "Original/Channel/Series/Season Raw/"),

		("{org:s}/{date:s}/{series:s}/", "Date/Series/"),
		("{org:s}/{time:s}/{series:s}/", "Time/Series/")
	]


def readDirectoryPatterns():
	path = config.plugins.seriesplugin.pattern_file_directories.value
	obj = None
	patterns = None

	if os.path.exists(path):
		log.debug("Found directory pattern file")
		f = None
		try:
			f = open(path, 'rb')
			header, patterns = json.load(f)
			patterns = [tuple(p) for p in patterns]
		except Exception as e:
			log.exception(_("Your pattern file is corrupt") + "\n" + path + "\n\n" + str(e))
		finally:
			if f is not None:
				f.close()
	return patterns or scheme_fallback
