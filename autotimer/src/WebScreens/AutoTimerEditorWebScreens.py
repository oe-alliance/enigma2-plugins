from Plugins.Extensions.WebInterface.WebScreens import WebScreen

class AutoTimerEditorWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Plugins.Extensions.AutoTimer.WebComponents.Sources.AutoTimerEditor import AutoTimerEditor
		self["Backup"] = AutoTimerEditor(session, func=AutoTimerEditor.BACKUP)
		self["Restore"] = AutoTimerEditor(session, func=AutoTimerEditor.RESTORE)

