from Plugins.Extensions.WebInterface.WebScreens import WebScreen


class AdditionalWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Plugins.Extensions.WebBouquetEditor.WebComponents.Sources.SatellitesList import SatellitesList
		self["SatellitesList"] = SatellitesList(func=SatellitesList.FETCH)

		from Plugins.Extensions.WebBouquetEditor.WebComponents.Sources.ServiceList import ServiceList

		from Screens.ChannelSelection import service_types_tv
		from enigma import eServiceReference

		fav = eServiceReference(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')
		self["ServiceList"] = ServiceList(fav, command_func=self.getServiceList, validate_commands=False)

		from Plugins.Extensions.WebBouquetEditor.WebComponents.Sources.ProtectionSettings import ProtectionSettings
		self["ProtectionSettings"] = ProtectionSettings()

	def getServiceList(self, sRef):
		self["ServiceList"].root = sRef
