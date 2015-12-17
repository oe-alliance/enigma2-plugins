# -*- coding: utf-8 -*-
# by betonme @2012

# for localized messages
from . import _

from Components.config import *

from Screens.MessageBox import MessageBox
from Tools.Notifications import AddPopup

# Plugin internal
from SeriesPluginTimer import SeriesPluginTimer
from Logger import logDebug, logInfo, getLog, startLog


loop_data = []
loop_counter = 0


def bareGetSeasonEpisode(service_ref, name, begin, end, description, path, future=True, today=False, elapsed=False):
	result = None
	if config.plugins.seriesplugin.enabled.value:
		
		startLog()
		
		logInfo("Bare:", service_ref, name, begin, end, description, path, future, today, elapsed)
		
		from SeriesPlugin import getInstance, refactorTitle, refactorDescription, refactorDirectory
		seriesPlugin = getInstance()
		data = seriesPlugin.getEpisodeBlocking(
			name, begin, end, service_ref, future, today, elapsed
		)
		
		global loop_counter
		loop_counter += 1
		
		if data and len(data) == 4:
			name = str(refactorTitle(name, data))
			description = str(refactorDescription(description, data))
			path = refactorDirectory(path, data)
			logInfo("Bare: Success", name, description, path)
			return (name, description, path, getLog())
		elif data:
			global loop_data
			loop_data.append( str(data) )
		
		logInfo("Bare: Failed", str(data))
		return str(data)
	
	return result

def bareShowResult():
	global loop_data, loop_counter
	
	if not loop_data and config.plugins.seriesplugin.timer_popups_success.value:
		AddPopup(
			"SeriesPlugin:\n" + _("%d timer renamed successfully") % (loop_counter),
			MessageBox.TYPE_ERROR,
			int(config.plugins.seriesplugin.timer_popups_timeout.value),
			'SP_PopUp_ID_Finished'
		)
	elif loop_data and config.plugins.seriesplugin.timer_popups.value:
		AddPopup(
			"SeriesPlugin:\n" + _("SP has been finished with errors:\n") +"\n" +"\n".join(loop_data),
			MessageBox.TYPE_ERROR,
			int(config.plugins.seriesplugin.timer_popups_timeout.value),
			'SP_PopUp_ID_Finished'
		)
	
	loop_data = []
	loop_counter = 0
