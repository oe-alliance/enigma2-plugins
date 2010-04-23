from enigma import eServiceReference
from Screens.Screen import Screen
from WebComponents.Sources.RequestData import RequestData

class WebScreen(Screen):
	def __init__(self, session, request):
		Screen.__init__(self, session)
		self.stand_alone = True
		self.request = request
		self.instance = None

class DummyWebScreen(WebScreen):
	#use it, if you dont need any source, just to can do a static file with an xml-file
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)

class UpdateWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Components.Sources.Clock import Clock

		self["CurrentTime"] = Clock()


class MessageWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.Message import Message

		self["Message"] = Message(session, func=Message.PRINT)
		self["GetAnswer"] = Message(session, func=Message.ANSWER)

class ServiceListReloadWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.ServiceListReload import ServiceListReload

		self["ServiceListReload"] = ServiceListReload(session)

class AudioWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.AudioTracks import AudioTracks

		self["AudioTracks"] = AudioTracks(session, func=AudioTracks.GET)
		self["SelectAudioTrack"] = AudioTracks(session, func=AudioTracks.SET)

class AboutWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.About import About
		from WebComponents.Sources.Frontend import Frontend
		from WebComponents.Sources.Hdd import Hdd
		from WebComponents.Sources.Network import Network
		from Components.config import config
		from Components.About import about
		from Components.Sources.StaticText import StaticText
		from Tools.DreamboxHardware import getFPVersion
		from Tools.HardwareInfo import HardwareInfo

		hw = HardwareInfo()

		self["About"] = About(session)

		self["Network"] = Network()
		self["Hdd"] = Hdd()
		self["Frontends"] = Frontend()
		self["EnigmaVersion"] = StaticText(about.getEnigmaVersionString())
		self["ImageVersion"] = StaticText(about.getVersionString())
		self["WebIfVersion"] = StaticText(config.plugins.Webinterface.version.value)
		self["FpVersion"] = StaticText(str(getFPVersion()))
		self["DeviceName"] = StaticText(hw.get_device_name())

class VolumeWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)

		from WebComponents.Sources.Volume import Volume
		self["Volume"] = Volume(session)

class SettingsWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.Settings import Settings

		self["Settings"] = Settings(session)

class SubServiceWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.SubServices import SubServices

		self["SubServices"] = SubServices(session)

class StreamSubServiceWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.SubServices import SubServices

		self["StreamSubServices"] = SubServices(session, streamingScreens)

class ServiceListWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		
		from Components.Sources.ServiceList import ServiceList
		from Screens.ChannelSelection import service_types_tv
	
		fav = eServiceReference(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')
		self["ServiceList"] = ServiceList(fav, command_func=self.getServiceList, validate_commands=False)
		self["localip"] = RequestData(request, what=RequestData.HOST)
		
	def getServiceList(self, sRef):
		self["ServiceList"].root = sRef	

class ServiceListRecursiveWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		
		from WebComponents.Sources.ServiceListRecursive import ServiceListRecursive
		self["ServiceListRecursive"] = ServiceListRecursive(session, func=ServiceListRecursive.FETCH)

class SwitchServiceWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		
		from WebComponents.Sources.SwitchService import SwitchService
		self["SwitchService"] = SwitchService(session)

class ReadPluginListWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.ReadPluginList import ReadPluginList
		self["ReadPluginList"] = ReadPluginList(session)

class LocationsAndTagsWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.LocationsAndTags import LocationsAndTags

		self["CurrentLocation"] = LocationsAndTags(session, LocationsAndTags.CURRLOCATION)
		self["Locations"] = LocationsAndTags(session, LocationsAndTags.LOCATIONS)
		self["AddLocation"] = LocationsAndTags(session, LocationsAndTags.ADDLOCATION)
		self["RemoveLocation"] = LocationsAndTags(session, LocationsAndTags.REMOVELOCATION)
		self["Tags"] = LocationsAndTags(session, LocationsAndTags.TAGS)

class EpgWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.EPG import EPG

		self["EpgSearch"] = EPG(session, func=EPG.SEARCH)
		self["EpgSearchSimilar"] = EPG(session, func=EPG.SEARCHSIMILAR)
		self["EpgService"] = EPG(session, func=EPG.SERVICE)
		self["EpgBouquetNow"] = EPG(session, func=EPG.BOUQUETNOW)
		self["EpgBouquetNext"] = EPG(session, func=EPG.BOUQUETNEXT)
		self["EpgServiceNow"] = EPG(session, func=EPG.SERVICENOW)
		self["EpgServiceNext"] = EPG(session, func=EPG.SERVICENEXT)
		self["EpgBouquet"] = EPG(session, func=EPG.BOUQUET)
		self["localip"] = RequestData(request, what=RequestData.HOST)

		self["EpgServiceWap"] = EPG(session, func=EPG.SERVICE, endtm=True)

	def getServiceList(self, sRef):
		self["ServiceList"].root = sRef

class MovieWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Components.MovieList import MovieList
		from Tools.Directories import resolveFilename, SCOPE_HDD
		from WebComponents.Sources.Movie import Movie

		movielist = MovieList(eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD)))
		self["MovieList"] = Movie(session, movielist, func=Movie.LIST)
		self["MovieFileDel"] = Movie(session, movielist, func=Movie.DEL)
		self["localip"] = RequestData(request, what=RequestData.HOST)

class MediaPlayerWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.MP import MP

		self["FileList"] = MP(session, func=MP.LIST)
		self["PlayFile"] = MP(session, func=MP.PLAY)
		self["RemoveFile"] = MP(session, func=MP.REMOVE)
		self["Command"] = MP(session, func=MP.COMMAND)
		self["WritePlaylist"] = MP(session, func=MP.WRITEPLAYLIST)

class AutoTimerWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.AT import AT

		self["AutoTimerList"] = AT(session, func=AT.LIST)
		self["AutoTimerWrite"] = AT(session, func=AT.WRITE)

class TimerWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.Timer import Timer

		self["TimerList"] = Timer(session, func=Timer.LIST)
		self["TimerAddEventID"] = Timer(session, func=Timer.ADDBYID)
		self["TimerAdd"] = Timer(session, func=Timer.ADD)
		self["TimerDel"] = Timer(session, func=Timer.DEL)
		self["TimerChange"] = Timer(session, func=Timer.CHANGE)
		self["TimerListWrite"] = Timer(session, func=Timer.WRITE)
		self["TVBrowser"] = Timer(session, func=Timer.TVBROWSER)
		self["RecordNow"] = Timer(session, func=Timer.RECNOW)
		self["TimerCleanup"] = Timer(session, func=Timer.CLEANUP)

class RemoteWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.RemoteControl import RemoteControl

		self["RemoteControl"] = RemoteControl(session)

class PowerWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.PowerState import PowerState

		self["PowerState"] = PowerState(session)

class ParentControlWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.ParentControl import ParentControl

		self["ParentControlList"] = ParentControl(session)

class WapWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.WAPfunctions import WAPfunctions

		self["WAPFillOptionListYear"] = WAPfunctions(session, func=WAPfunctions.LISTTIME)
		self["WAPFillOptionListDay"] = WAPfunctions(session, func=WAPfunctions.LISTTIME)
		self["WAPFillOptionListMonth"] = WAPfunctions(session, func=WAPfunctions.LISTTIME)
		self["WAPFillOptionListShour"] = WAPfunctions(session, func=WAPfunctions.LISTTIME)
		self["WAPFillOptionListSmin"] = WAPfunctions(session, func=WAPfunctions.LISTTIME)
		self["WAPFillOptionListEhour"] = WAPfunctions(session, func=WAPfunctions.LISTTIME)
		self["WAPFillOptionListEmin"] = WAPfunctions(session, func=WAPfunctions.LISTTIME)

		self["WAPFillOptionListRecord"] = WAPfunctions(session, func=WAPfunctions.OPTIONLIST)
		self["WAPFillOptionListAfterEvent"] = WAPfunctions(session, func=WAPfunctions.OPTIONLIST)

		self["WAPFillValueName"] = WAPfunctions(session, func=WAPfunctions.FILLVALUE)
		self["WAPFillValueDescr"] = WAPfunctions(session, func=WAPfunctions.FILLVALUE)
		self["WAPFillLocation"] = WAPfunctions(session, func=WAPfunctions.LOCATIONLIST)
		self["WAPFillTags"] = WAPfunctions(session, func=WAPfunctions.TAGLIST)

		self["WAPFillOptionListRepeated"] = WAPfunctions(session, func=WAPfunctions.REPEATED)
		self["WAPServiceList"] = WAPfunctions(session, func=WAPfunctions.SERVICELIST)

		self["WAPdeleteOldOnSave"] = WAPfunctions(session, func=WAPfunctions.DELETEOLD)

streamingScreens = []

class StreamingWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Components.Sources.StreamService import StreamService
		self["StreamService"] = StreamService(self.session.nav)
		streamingScreens.append(self)
		self.screenIndex = len(streamingScreens) - 1

	def getRecordService(self):
		if self.has_key("StreamService"):
			return self["StreamService"].getService()
		return None

	def getRecordServiceRef(self):
		if self.has_key("StreamService"):
			return self["StreamService"].ref
		return None

class M3uStreamingWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Components.Sources.StaticText import StaticText
		from Components.Sources.Config import Config
		from Components.config import config
		self["ref"] = StaticText()
		self["localip"] = RequestData(request, what=RequestData.HOST)

class M3uStreamingCurrentServiceWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.CurrentService import CurrentService

		self["CurrentService"] = CurrentService(session)
		self["localip"] = RequestData(request, what=RequestData.HOST)

class TsM3uWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from Components.Sources.StaticText import StaticText
		from Components.Sources.Config import Config
		from Components.config import config
		self["file"] = StaticText()
		self["localip"] = RequestData(request, what=RequestData.HOST)
		self["localport"] = RequestData(request, what=RequestData.PORT)

class RestartWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		import plugin
		plugin.restartWebserver(session)

class GetPidWebScreen(WebScreen):
	def __init__(self, session, request):
		 WebScreen.__init__(self, session, request)
		 from Components.Sources.StaticText import StaticText
		 from enigma import iServiceInformation
		 pids = self.session.nav.getCurrentService()
		 if pids is not None:
		 	pidinfo = pids.info()
		 	VPID = hex(pidinfo.getInfo(iServiceInformation.sVideoPID))
			APID = hex(pidinfo.getInfo(iServiceInformation.sAudioPID))
			PPID = hex(pidinfo.getInfo(iServiceInformation.sPMTPID))
			self["pids"] = StaticText("%s,%s,%s" % (PPID.lstrip("0x"), VPID.lstrip("0x"), APID.lstrip("0x")))
		 else:
			self["pids"] = StaticText("0x,0x,0x")

		 self["localip"] = RequestData(request, what=RequestData.HOST)

class DeviceInfoWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.Network import Network
		from WebComponents.Sources.Hdd import Hdd
		from WebComponents.Sources.Frontend import Frontend
		from Components.config import config
		from Components.About import about
		from Components.Sources.StaticText import StaticText
		from Tools.DreamboxHardware import getFPVersion
		from Tools.HardwareInfo import HardwareInfo

		hw = HardwareInfo()

		self["Network"] = Network()
		self["Hdd"] = Hdd()
		self["Frontends"] = Frontend()
		self["EnigmaVersion"] = StaticText(about.getEnigmaVersionString())
		self["ImageVersion"] = StaticText(about.getVersionString())
		self["WebIfVersion"] = StaticText(config.plugins.Webinterface.version.value)
		self["FpVersion"] = StaticText(str(getFPVersion()))
		self["DeviceName"] = StaticText(hw.get_device_name())

class ServicePlayableWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.ServicePlayable import ServicePlayable
		
		self["ServicePlayable"] = ServicePlayable(session, type=ServicePlayable.SINGLE)

class ServiceListPlayableWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from WebComponents.Sources.ServicePlayable import ServicePlayable
		
		self["ServiceListPlayable"] = ServicePlayable(session, type=ServicePlayable.BOUQUET)
		