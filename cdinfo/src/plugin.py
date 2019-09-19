from enigma import eServiceReference, eConsoleAppContainer
from Components.MediaPlayer import PlayList
import xml.dom.minidom
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Screens.Screen import Screen
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, getConfigListEntry
from Components.ConfigList import ConfigListScreen

config.plugins.CDInfo = ConfigSubsection()
config.plugins.CDInfo.useCDTEXT = ConfigYesNo(default = True)
config.plugins.CDInfo.useCDDB = ConfigYesNo(default = True)
config.plugins.CDInfo.displayString = ConfigText("$i - $t ($a)", fixed_size = False)
config.plugins.CDInfo.preferCDDB = ConfigYesNo(default = False)
config.plugins.CDInfo.CDDB_server = ConfigText("freedb.freedb.org", fixed_size = False)
config.plugins.CDInfo.CDDB_port = ConfigInteger(8880,limits = (1, 65536))
config.plugins.CDInfo.CDDB_timeout = ConfigInteger(20,limits = (-1, 60))
config.plugins.CDInfo.CDDB_cache = ConfigYesNo(default = True)

class CDInfo(ConfigListScreen,Screen):
	skin = """
		<screen position="90,95" size="560,430" title="CDInfo" >
		    <ePixmap pixmap="skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />
		    <ePixmap pixmap="skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />
		    <ePixmap pixmap="skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />
		    <widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
		    <widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />
		    <widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />
		    <widget name="info" position="20,50" size="520,40" font="Regular;20" transparent="1" />
		    <widget name="config" position="20,120" size="520,200" scrollbarMode="showOnDemand" />
		    <widget name="info2" position="20,340" size="520,80" font="Regular;20" transparent="1" />
		</screen>
		"""
	
	def __init__(self, session, args = None):
		self.skin = CDInfo.skin
		Screen.__init__(self, session)

		self["info"] = Label(_("Gather audio cd album information and track listing from CDDB (online database) and / or CD-Text (from medium)."))

		self["info2"] = Label(_("Playlist string variables: $i=track, $t=title, $a=artist\nCDDB query will not delay start of audio CD playback. The request will be sent asynchronously and playlist text will be updated when match was found."))

		self.list = []
		self.list.append(getConfigListEntry(_("Try to extract CDTEXT"), config.plugins.CDInfo.useCDTEXT))
		self.list.append(getConfigListEntry(_("Try to query CDDB"), config.plugins.CDInfo.useCDDB))
		self.list.append(getConfigListEntry(_("Playlist string"), config.plugins.CDInfo.displayString))
		self.list.append(getConfigListEntry(_("CDDB overwrites CDTEXT info"), config.plugins.CDInfo.preferCDDB))
		self.list.append(getConfigListEntry(_("CDDB server hostname"), config.plugins.CDInfo.CDDB_server))
		self.list.append(getConfigListEntry(_("CDDB server port number"), config.plugins.CDInfo.CDDB_port))
		self.list.append(getConfigListEntry(_("CDDB retrieval timeout (s)"), config.plugins.CDInfo.CDDB_timeout))
		self.list.append(getConfigListEntry(_("store local CDDB cache"), config.plugins.CDInfo.CDDB_cache))
		
		ConfigListScreen.__init__(self, self.list)
		self["key_red"] = Button(_("cancel"))
		self["key_green"] = Button(_("ok"))
		self["key_blue"] = Button(_("defaults"))

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
		    "green": self.save,
		    "red": self.cancel,
		    "blue": self.defaults,
		    "save": self.save,
		    "cancel": self.cancel,
		    "ok": self.save,
		}, -2)

	def save(self):
		for x in self["config"].list:
			x[1].save()
		self.close(True)

	def cancel(self):
		for x in self["config"].list:
			x[1].cancel()
		self.close(False)

	def defaults(self):
		config.plugins.CDInfo.useCDTEXT.setValue(True)
		config.plugins.CDInfo.useCDDB.setValue(True)
		config.plugins.CDInfo.displayString.setValue("$i - $t ($a)")
		config.plugins.CDInfo.preferCDDB.setValue(False)
		config.plugins.CDInfo.CDDB_server.setValue("freedb.freedb.org")
		config.plugins.CDInfo.CDDB_port.setValue(8880)
		config.plugins.CDInfo.CDDB_timeout.setValue(20)
		config.plugins.CDInfo.CDDB_cache.setValue(True)
		for x in self["config"].list:
			x[1].save()
		self.close(True)

class Query:
	def __init__(self, mediaplayer):
		self.playlist = mediaplayer.playlist
		self.mp = mediaplayer
		self.cddb_container = eConsoleAppContainer()
		self.cddb_output = ""
		self.cdtext_container = eConsoleAppContainer()
		self.cdtext_output = ""
		self.tracklisting = {}
		self.albuminfo = {}

	def getText(self, nodelist):
	    rc = ""
	    for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
		    rc = rc + node.data
	    return rc.encode("utf-8")

	def xml_parse_output(self,string):
		data = string.decode("utf-8","replace").replace('&',"&amp;").encode("ascii",'xmlcharrefreplace')
		try:
			cdinfodom = xml.dom.minidom.parseString(data)
		except:
			print "[xml_parse_output] error, could not parse"
			return False
		xmldata = cdinfodom.childNodes[0]
		queries = xmldata.childNodes
		self.xml_parse_query(queries)
		print "[xml_parse_output] albuminfo: " + str(self.albuminfo)
		print "[xml_parse_output] tracklisting: " + str(self.tracklisting)
		return True

	def xml_parse_query(self, queries_xml):
	    for queries in queries_xml:
		if queries.nodeType == xml.dom.minidom.Element.nodeType:
		    if queries.tagName == 'query':
			print "[xml_parse_query] cdinfo source is %s, hit %s of %s" % (queries.getAttribute("source"),queries.getAttribute("match"),queries.getAttribute("num_matches"))
			for query in queries.childNodes:
			    if query.nodeType == xml.dom.minidom.Element.nodeType:
				if query.tagName == 'albuminfo':
				    self.xml_parse_albuminfo(query.childNodes)
				elif query.tagName == 'tracklisting':
				    self.xml_parse_tracklisting(query.childNodes)

	def xml_parse_albuminfo(self, albuminfo_xml):
	    for albuminfo in albuminfo_xml:
		if albuminfo.nodeType == xml.dom.minidom.Element.nodeType:
		    if albuminfo.tagName == 'PERFORMER' or albuminfo.tagName == 'artist':
			artist = self.getText(albuminfo.childNodes)
			self.albuminfo["artist"] = artist
		    elif albuminfo.tagName.upper() == 'TITLE':
			title = self.getText(albuminfo.childNodes)
			self.albuminfo["title"] = title
		    elif albuminfo.tagName.upper() == 'YEAR':
			year = self.getText(albuminfo.childNodes)
			self.albuminfo["year"] = year
		    elif albuminfo.tagName.upper() == 'GENRE':
			genre = self.getText(albuminfo.childNodes)
			self.albuminfo["genre"] = genre
		    elif albuminfo.tagName == 'category' and not "GENRE" in self.albuminfo:
			category = self.getText(albuminfo.childNodes)
			self.albuminfo["genre"] = category

	def xml_parse_tracklisting(self, tracklisting_xml):
	    for tracklist in tracklisting_xml:
		if tracklist.nodeType == xml.dom.minidom.Element.nodeType:
		    if tracklist.tagName == 'track':
			index = int(tracklist.getAttribute("number"))
			trackinfo = {}
			for track in tracklist.childNodes:
			    if track.nodeType == xml.dom.minidom.Element.nodeType:
				if track.tagName == 'PERFORMER' or track.tagName == 'artist':
				    artist = self.getText(track.childNodes)
				    trackinfo["artist"] = artist
				if track.tagName.upper() == 'TITLE':
				    title = self.getText(track.childNodes)
				    trackinfo["title"] = title
				#elif track.tagName == 'length':
				    #tracktext += "Dauer=%ss " % self.getText(track.childNodes)
			self.tracklisting[index]=trackinfo

	def updateAlbuminfo(self, replace = False):
		for tag in self.albuminfo:
			if tag not in self.mp.AudioCD_albuminfo or replace:
				self.mp.AudioCD_albuminfo[tag] = self.albuminfo[tag]
	
	def updatePlaylist(self, replace = False):
		for idx in range(len(self.playlist)):
			ref = self.playlist.getServiceRefList()[idx]
			track = idx+1
			if idx < len(self.tracklisting):
				if replace or not ref.getName():
					trackinfo = self.tracklisting[track]
					displayString = config.plugins.CDInfo.displayString.value.replace("$i", str(track))
					if "title" in trackinfo:
						displayString = displayString.replace("$t", trackinfo["title"])
					if "artist" in trackinfo:
						displayString = displayString.replace("$a", trackinfo["artist"])
					ref.setName(displayString)
					self.playlist.updateFile(idx, ref)
		self.playlist.updateList()

	def scan(self):
		if config.plugins.CDInfo.useCDTEXT.value:
		    self.cdtext_scan()
		if config.plugins.CDInfo.useCDDB.value:
		    self.cddb_scan()

	def cdtext_scan(self):
		cmd = "cdtextinfo -xalT"
		print "[cdtext_scan] " + cmd
		self.cdtext_container.appClosed.append(self.cdtext_finished)
		self.cdtext_container.dataAvail.append(self.cdtext_avail)
		self.cdtext_container.execute(cmd)

	def cddb_scan(self):
		cmd = "cdtextinfo -xalD --cddb-port=%d --cddb-server=%s --cddb-timeout=%s" % (config.plugins.CDInfo.CDDB_port.value, config.plugins.CDInfo.CDDB_server.value, config.plugins.CDInfo.CDDB_timeout.value)
		if not config.plugins.CDInfo.CDDB_cache.value:
			cmd += " --no-cddb-cache"
		print "[cddb_scan] " + cmd
		self.cddb_container.appClosed.append(self.cddb_finished)
		self.cddb_container.dataAvail.append(self.cddb_avail)
		self.cddb_container.execute(cmd)

	def cddb_avail(self,string):
		self.cddb_output += string

	def cdtext_avail(self,string):
		self.cdtext_output += string

	def cddb_finished(self,retval):
		self.cddb_container.appClosed.remove(self.cddb_finished)
		self.cddb_container.dataAvail.remove(self.cddb_avail)
		if not self.xml_parse_output(self.cddb_output):
			return
		if config.plugins.CDInfo.preferCDDB.value:
			self.updatePlaylist(replace = True)
			self.updateAlbuminfo(replace = True)
		else:
			self.updatePlaylist(replace = False)
			self.updateAlbuminfo(replace = False)
		self.mp.readTitleInformation()
		self.cddb_output = ""

	def cdtext_finished(self,retval):
		self.cdtext_container.appClosed.remove(self.cdtext_finished)
		self.cdtext_container.dataAvail.remove(self.cdtext_avail)
		if not self.xml_parse_output(self.cdtext_output):
			return
		if not config.plugins.CDInfo.preferCDDB.value:
			self.updatePlaylist(replace = True)
			self.updateAlbuminfo(replace = True)
		else:
			self.updatePlaylist(replace = False)
			self.updateAlbuminfo(replace = False)
		self.mp.readTitleInformation()
		self.cdtext_output = ""

def main(session, **kwargs):
	session.open(CDInfo)

def Plugins(**kwargs):
	return [ PluginDescriptor(name="CDInfo", description=_("AudioCD info from CDDB & CD-Text"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main, icon="plugin.png") ]