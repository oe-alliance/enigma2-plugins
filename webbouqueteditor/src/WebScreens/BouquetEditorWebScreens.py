from Plugins.Extensions.WebInterface.WebScreens import WebScreen


class BouquetEditorWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Plugins.Extensions.WebBouquetEditor.WebComponents.Sources.BouquetEditor import BouquetEditor
		self["AddBouquet"] = BouquetEditor(session, func=BouquetEditor.ADD_BOUQUET)
		self["RemoveBouquet"] = BouquetEditor(session, func=BouquetEditor.REMOVE_BOUQUET)
		self["MoveBouquet"] = BouquetEditor(session, func=BouquetEditor.MOVE_BOUQUET)
		self["MoveService"] = BouquetEditor(session, func=BouquetEditor.MOVE_SERVICE)
		self["RemoveService"] = BouquetEditor(session, func=BouquetEditor.REMOVE_SERVICE)
		self["AddServiceToBouquet"] = BouquetEditor(session, func=BouquetEditor.ADD_SERVICE_TO_BOUQUET)
		self["AddProviderToBouquetlist"] = BouquetEditor(session, func=BouquetEditor.ADD_PROVIDER_TO_BOUQUETLIST)
		self["AddServiceToAlternative"] = BouquetEditor(session, func=BouquetEditor.ADD_SERVICE_TO_ALTERNATIVE)
		self["RemoveAlternativeServices"] = BouquetEditor(session, func=BouquetEditor.REMOVE_ALTERNATIVE_SERVICES)
		self["ToggleLock"] = BouquetEditor(session, func=BouquetEditor.TOGGLE_LOCK)
		self["Backup"] = BouquetEditor(session, func=BouquetEditor.BACKUP)
		self["Restore"] = BouquetEditor(session, func=BouquetEditor.RESTORE)
		self["RenameService"] = BouquetEditor(session, func=BouquetEditor.RENAME_SERVICE)
		self["AddMarkerToBouquet"] = BouquetEditor(session, func=BouquetEditor.ADD_MARKER_TO_BOUQUET)
		
