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
		
		("{org:s} S{season:02d}E{episode:02d}", "Org S01E01"),
		("{org:s} S{season:d}E{episode:d}", "Org S1E1"),

		("{org:s} S{season:02d}E{episode:02d} {title:s}", "Org S01E01 Title"),
		("{org:s} S{season:d}E{episode:d} {title:s}", "Org S1E1 Title"),

		("{org:s} {title:s} S{season:02d}E{episode:02d}", "Org Title S01E01"),
		("{org:s} {title:s} S{season:d}E{episode:d}", "Org Title S1E1"),

		("{org:s} - S{season:02d}E{episode:02d} - {title:s}", "Org - S01E01 - Title"),
		("{org:s} - S{season:2d}E{episode:2d} - {title:s}", "Org - S1E1 - Title"),

		("S{season:02d}E{episode:02d}", "S01E01"),
		("S{season:02d}E{episode:02d} {org:s}", "S01E01 Org"),
		("S{season:d}E{episode:d} {org:s}", "S1E1 Org"),

		("S{season:02d}E{episode:02d} {title:s} {org:s}", "S01E01 Title Org"),
		("S{season:d}E{episode:d} {title:s} {org:s}", "S1E1 Title Org"),

		("{title:s} S{season:02d}E{episode:02d} {org:s}", "Title S01E01 Org"),
		("{title:s} S{season:d}E{episode:d} {org:s}", "Title S1E1 Org"),

		("{title:s}", "Title"),
		("{title:s} {org:s}", "Title Org"),
		("{title:s} {series:s}", "Title Series"),
		
		("{org:s} {title:s}", "Org Title"),
		("{series:s} {title:s}", "Series Title"),
		
		("{series:s} S{season:02d}E{episode:02d}", "Series S01E01"),
		("{series:s} S{season:d}E{episode:d}", "Series S1E1"),

		("{series:s} S{season:02d}E{episode:02d} {title:s}", "Series S01E01 Title"),
		("{series:s} S{season:d}E{episode:d} {title:s}", "Series S1E1 Title"),
		
		("{series:s} {title:s} S{season:02d}E{episode:02d}", "Series Title S01E01"),
		("{series:s} {title:s} S{season:d}E{episode:d}", "Series Title S1E1"),

		("S{season:02d}E{episode:02d} {series:s}", "S01E01 Series"),
		("S{season:d}E{episode:d} {series:s}", "S1E1 Series"),

		("S{season:02d}E{episode:02d} {title:s} {series:s}", "S01E01 Title Series"),
		("S{season:d}E{episode:d} {title:s} {series:s}", "S1E1 Title Series"),

		("{title:s} S{season:02d}E{episode:02d} {series:s}", "Title S01E01 Series"),
		("{title:s} S{season:d}E{episode:d} {series:s}", "Title S1E1 Series"),

		("{series:s} - s{season:02d}e{episode:02d} - {title:s}", "Series - s01e01 - Title"),
		("{series:s} - S{season:02d}E{episode:02d} - {title:s}", "Series - S01E01 - Title"),

		("{org:s}_S{season:02d}EP{episode:02d}", "Org_S01EP01"),
		("{org:s}_S{season:02d}EP{episode:02d_}", "Org_S01EP01_"),
		
		
		("{org:s} S{season:02d} E{rawepisode:s} {title:s}", "Org S01 ERaw Title"),
		("{org:s} S{season:02d}E{rawepisode:s} {title:s}", "Org S01ERaw Title"),
		("{org:s} {season:02d} {rawepisode:s} {title:s}", "Org 01 Raw Title"),
		("{org:s} {season:02d}{rawepisode:s} {title:s}", "Org 01Raw Title"),
		
		("{org:s} - S{season:02d} E{rawepisode:s} - {title:s}", "Org - S01 ERaw - Title"),
		("{org:s} - S{season:02d}E{rawepisode:s} - {title:s}", "Org - S01ERaw - Title"),
		("{org:s} - {season:02d} {rawepisode:s} - {title:s}", "Org - 01 Raw - Title"),
		("{org:s} - {season:02d}{rawepisode:s} - {title:s}", "Org - 01Raw - Title"),
		
		("{series:s} S{season:02d} E{rawepisode:s} {title:s}", "Series S01 ERaw Title"),
		("{series:s} S{season:02d}E{rawepisode:s} {title:s}", "Series S01ERaw Title"),
		("{series:s} {season:02d} {rawepisode:s} {title:s}", "Series 01 Raw Title"),
		("{series:s} {season:02d}{rawepisode:s} {title:s}", "Series 01Raw Title"),
		
		("{series:s} - S{season:02d} E{rawepisode:s} - {title:s}", "Series - S01 ERaw - Title"),
		("{series:s} - S{season:02d}E{rawepisode:s} - {title:s}", "Series - S01ERaw - Title"),
		("{series:s} - {season:02d} {rawepisode:s} - {title:s}", "Series - 01 Raw - Title"),
		("{series:s} - {season:02d}{rawepisode:s} - {title:s}", "Series - 01Raw - Title"),
		
		
		("{org:s} S{rawseason:s} E{rawepisode:s} {title:s}", "Org SRaw ERaw Title"),
		("{org:s} S{rawseason:s}E{rawepisode:s} {title:s}", "Org SRawERaw Title"),
		("{org:s} {rawseason:s} {rawepisode:s} {title:s}", "Org Raw Raw Title"),
		("{org:s} {rawseason:s}{rawepisode:s} {title:s}", "Org RawRaw Title"),
		
		("{org:s} - S{rawseason:s} E{rawepisode:s} - {title:s}", "Org - SRaw ERaw - Title"),
		("{org:s} - S{rawseason:s}E{rawepisode:s} - {title:s}", "Org - SRawERaw - Title"),
		("{org:s} - {rawseason:s} {rawepisode:s} - {title:s}", "Org - Raw Raw - Title"),
		("{org:s} - {rawseason:s}{rawepisode:s} - {title:s}", "Org - RawRaw - Title"),
		
		("{series:s} S{rawseason:s} E{rawepisode:s} {title:s}", "Series SRaw ERaw Title"),
		("{series:s} S{rawseason:s}E{rawepisode:s} {title:s}", "Series SRawERaw Title"),
		("{series:s} {rawseason:s} {rawepisode:s} {title:s}", "Series Raw Raw Title"),
		("{series:s} {rawseason:s}{rawepisode:s} {title:s}", "Series RawRaw Title"),
		
		("{series:s} - S{rawseason:s} E{rawepisode:s} - {title:s}", "Series - SRaw ERaw - Title"),
		("{series:s} - S{rawseason:s}E{rawepisode:s} - {title:s}", "Series - SRawERaw - Title"),
		("{series:s} - {rawseason:s} {rawepisode:s} - {title:s}", "Series - Raw Raw - Title"),
		("{series:s} - {rawseason:s}{rawepisode:s} - {title:s}", "Series - RawRaw - Title"),
		
		
		("{channel:s} {series:s} S{season:02d} E{rawepisode:s} {title:s}", "Channel Series S01 ERaw Title"),
		("{service:s} {series:s} S{season:02d}E{rawepisode:s} {title:s}", "Service Series S01ERaw Title"),
		
		("{date:s} {channel:s} {series:s} S{season:02d} E{rawepisode:s} {title:s}", "Date Channel Series S01 ERaw Title"),
		("{date:s} {time:s} {channel:s} {series:s} S{season:02d} E{rawepisode:s} {title:s}", "Date Time Channel Series S01 ERaw Title")
	]


def readFilePatterns():
	path = config.plugins.seriesplugin.pattern_file.value
	obj = None
	patterns = None
	
	if os.path.exists(path):
		log.debug("Found title pattern file")
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
