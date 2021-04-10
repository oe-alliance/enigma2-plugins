#######################################################################
#
#    Push Service for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779
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

# Config
from Components.config import NoSave, ConfigNumber

# Plugin internal
from Plugins.Extensions.PushService.__init__ import _
from Plugins.Extensions.PushService.ServiceBase import ServiceBase

# Plugin specific
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox


# Constants
POPUP_TEMPLATE = _("{name:s} {plugin:s}\n{subject:s}\n{body:s}")


class PopUp(ServiceBase):
	
	ForceSingleInstance = True
	
	def __init__(self):
		# Is called on instance creation
		ServiceBase.__init__(self)
		# Default configuration
		self.setOption( 'timeout', NoSave(ConfigNumber(default=30)), _("Timeout") )

	def push(self, callback, errback, pluginname, subject, body="", attachments=[]):
		from Plugins.Extensions.PushService.plugin import NAME
		# Fire and forget
		AddPopup(
			POPUP_TEMPLATE.format( **{'name': NAME, 'plugin': pluginname, 'subject': subject, 'body': body} ),
			MessageBox.TYPE_INFO,
			self.getValue('timeout'),
			'PS_PopUp_ID_' + subject
		)
		# There is no known error state
		callback(_("The PopUp will be shown after all dialogs are closed."))
