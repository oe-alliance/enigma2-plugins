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

# for localized messages
from . import _

# Config
from Components.config import *

import os
import json

# Plugin internal
from Logger import splog


scheme_fallback = [
		("Off", "Disabled"),
		
		("{org:s} S{season:02d}E{episode:02d}"            , "Org S01E01"),
		("{org:s} S{season:02d}E{episode:02d} {title:s}"  , "Org S01E01 Title"),
		("{title:s} {org:s}"                              , "Title Org"),
		("S{season:02d}E{episode:02d} {title:s} {org:s}"  , "S01E01 Title Org"),
		("{title:s} S{season:02d}E{episode:02d} {org:s}"  , "Title S01E01 Org"),
		
		("{series:s} S{season:02d}E{episode:02d}"            , "Series S01E01"),
		("{series:s} S{season:02d}E{episode:02d} {title:s}"  , "Series S01E01 Title"),
		("{title:s} {series:s}"                              , "Title Series"),
		("S{season:02d}E{episode:02d} {title:s} {series:s}"  , "S01E01 Title Series"),
		("{title:s} S{season:02d}E{episode:02d} {series:s}"  , "Title S01E01 Series"),
	]

def readPatternFile():
	path = config.plugins.seriesplugin.pattern_file.value
	obj = None
	patterns = None
	
	if os.path.exists(path):
		splog("[SeriesPlugin] Found pattern file")
		f = None
		try:
			f = open(path, 'rb')
			header, patterns = json.load(f)
			patterns = [tuple(p) for p in patterns]
		except Exception as e:
			splog("[SeriesPlugin] Exception in readEpisodePatternsFile: " + str(e))
		finally:
			if f is not None:
				f.close()
	return patterns or scheme_fallback
