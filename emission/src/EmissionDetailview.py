# -*- coding: utf-8 -*-

# GUI (Screens)
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Screens.HelpMenu import HelpableScreen

# GUI (Components)
from Components.ActionMap import HelpableActionMap
from Components.Sources.List import List
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText

from enigma import eTimer

from . import EmissionBandwidth

class EmissionDetailview(Screen, HelpableScreen):
	skin = """<screen name="EmissionDetailview" title="Torrent View" position="75,75" size="565,450">
		<ePixmap position="0,0" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="140,0" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="280,0" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="420,0" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget source="key_red" render="Label" position="0,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_green" render="Label" position="140,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_yellow" render="Label" position="280,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget source="key_blue" render="Label" position="420,0" zPosition="1" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<eLabel position="450,45" text="DL: " size="30,20" font="Regular;18" />
		<widget source="downspeed" render="Label" position="480,45" size="85,20" halign="right" font="Regular;18" />
		<eLabel position="450,67" text="UL: " size="30,20" font="Regular;18" transparent="1" />
		<widget source="upspeed" render="Label" position="480,67" size="85,20" halign="right" font="Regular;18" />
		<widget source="name" render="Label" position="5,45" size="445,20" font="Regular;18" />
		<widget source="peers" render="Label" position="5,67" size="445,20" font="Regular;18" />
		<!-- XXX: the actual uri might end up in the next line, this sucks :-) -->
		<widget source="tracker" render="Label" position="5,90" size="555,20" font="Regular;18" />
		<widget source="private" render="Label" position="5,113" size="555,20" font="Regular;18" />
		<widget source="eta" render="Label" position="5,170" size="555,20" font="Regular;18" />
		<widget source="progress_text" render="Label" position="5,195" size="400,20" font="Regular;18" />
		<widget source="ratio" render="Label" position="410,195" size="150,20" font="Regular;18" halign="right" />
		<widget source="progress" render="Progress" position="5,220" size="555,6" />
		<widget source="files_text" render="Label" position="5,230" size="100,20" font="Regular;18" />
		<widget source="files" render="Listbox" position="0,255" size="566,185" scrollbarMode="showAlways">
			<convert type="TemplatedMultiContent">
				{"template": [
						MultiContentEntryText(pos=(2,2), size=(560,22), text = 4, font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(2,26), size=(110,20), text = "Downloaded", font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(117,26), size=(100,20), text = 2, font = 1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(365,26), size=(70,20), text = "Total", font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(435,26), size=(100,20), text = 5, font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER),
						MultiContentEntryText(pos=(220,26), size=(160,20), text = 6, font = 1, flags = RT_VALIGN_CENTER),
						(eListboxPythonMultiContent.TYPE_PROGRESS, 0, 47, 540, 6, -7),
					],
				  "fonts": [gFont("Regular", 20),gFont("Regular", 18)],
				  "itemHeight": 54
				 }
			</convert>
		</widget>
	</screen>"""

	def __init__(self, session, daemon, torrent, prevFunc=None, nextFunc=None):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.transmission = daemon
		self.torrentid = torrent.id
		self.prevFunc = prevFunc
		self.nextFunc = nextFunc

		self["ChannelSelectBaseActions"] = HelpableActionMap(self, "ChannelSelectBaseActions",
		{
			"prevMarker": (self.prevDl, _("show previous download details")),
			"nextMarker": (self.nextDl, _("show next download details")),
		})

		self["SetupActions"] = HelpableActionMap(self, "SetupActions",
		{
			"ok": (self.ok, _("toggle file status")),
			"cancel": self.close,
		})

		self["ColorActions"] = HelpableActionMap(self, "ColorActions",
		{
			"yellow": (self.toggleStatus, _("toggle download status")),
			"green": (self.bandwidth, _("open bandwidth settings")),
			"blue": (self.remove , _("remove torrent")),
		})

		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Bandwidth"))
		if torrent.status == "stopped":
			self["key_yellow"] = StaticText(_("start"))
		else:
			self["key_yellow"] = StaticText(_("stop"))
		self["key_blue"] = StaticText(_("remove"))

		self["upspeed"] = StaticText("")
		self["downspeed"] = StaticText("")
		self["peers"] = StaticText("")
		self["name"] = StaticText(str(torrent.name))
		self["files_text"] = StaticText(_("Files"))
		self["files"] = List([])
		self["progress"] = Progress(int(torrent.progress))
		self["progress_text"] = StaticText("")
		self["ratio"] = StaticText("")
		self["eta"] = StaticText("")
		self["tracker"] = StaticText("")
		self["private"] = StaticText("")

		self.timer = eTimer()
		self.timer.callback.append(self.updateList)
		self.timer.start(0, 1)

	def bandwidthCallback(self, ret=None):
		if ret:
			try:
				self.transmission.change([self.torrentid], **ret)
			except transmission.TransmissionError as te:
				self.session.open(
					MessageBox,
					_("Error communicating with transmission-daemon: %s.") % (te),
					type=MessageBox.TYPE_ERROR,
					timeout=5
				)
		self.updateList()

	def bandwidth(self):
		#reload(EmissionBandwidth)
		self.timer.stop()
		id = self.torrentid
		try:
			torrent = self.transmission.info([id])[id]
			rpc_version = self.transmission.rpc_version
		except transmission.TransmissionError as te:
			self.session.open(
				MessageBox,
				_("Error communicating with transmission-daemon: %s.") % (te),
				type=MessageBox.TYPE_ERROR,
				timeout=5
			)
			# XXX: this seems silly but cleans the gui and restarts the timer :-)
			self.updateList()
		else:
			self.session.openWithCallback(
				self.bandwidthCallback,
				EmissionBandwidth.EmissionBandwidth,
				torrent,
				True,
				rpc_version
			)

	def prevDl(self):
		if self.prevFunc:
			torrent = self.prevFunc()
			if torrent:
				self.timer.stop()
				self.torrentid = torrent.id
				self["name"].text = str(torrent.name)
				self.updateList()

	def nextDl(self):
		if self.nextFunc:
			torrent = self.nextFunc()
			if torrent:
				self.timer.stop()
				self.torrentid = torrent.id
				self["name"].text = str(torrent.name)
				self.updateList()

	def toggleStatus(self):
		id = self.torrentid
		try:
			torrent = self.transmission.info([id])[id]
			status = torrent.status
			if status == "stopped":
				self.transmission.start([id])
				self["key_yellow"].text = _("pause")
			elif status in ("downloading", "seeding"):
				self.transmission.stop([id])
				self["key_yellow"].text = _("start")
		except transmission.TransmissionError as te:
			self.session.open(
				MessageBox,
				_("Error communicating with transmission-daemon: %s.") % (te),
				type=MessageBox.TYPE_ERROR,
				timeout=5
			)

	def remove(self):
		self.session.openWithCallback(
			self.removeCallback,
			ChoiceBox,
			_("Really delete torrent?"),
			[(_("no"), "no"),
			(_("yes"), "yes"),
			(_("yes, including data"), "data")]
		)

	def removeCallback(self, ret=None):
		if ret:
			ret = ret[1]
			try:
				if ret == "yes":
					self.transmission.remove([self.torrentid], delete_data=False)
					self.close()
				elif ret == "data":
					self.transmission.remove([self.torrentid], delete_data=True)
					self.close()
			except transmission.TransmissionError as te:
				self.session.open(
					MessageBox,
					_("Error communicating with transmission-daemon: %s.") % (te),
					type=MessageBox.TYPE_ERROR,
					timeout=5
				)

	def updateList(self, *args, **kwargs):
		id = self.torrentid
		try:
			torrent = self.transmission.info([id])[id]
		except transmission.TransmissionError:
			self["upspeed"].text = ""
			self["downspeed"].text = ""
			self["peers"].text = ""
			self["progress_text"].text = ""
			self["ratio"].text = ""
			self["eta"].text = ""
			self["tracker"].text = ""
			self["private"].text = ""
			self["files"].setList([])
		else:
			self["upspeed"].text = _("%d kb/s") % (torrent.rateUpload / 1024)
			self["downspeed"].text = _("%d kb/s") % (torrent.rateDownload / 1024)
			self["progress"].setValue(int(torrent.progress))

			status = torrent.status
			progressText = ''
			if status == 'check pending':
				peerText = _("check pending") # ???
			elif status == 'checking':
				peerText = _("checking")
				progressText = str(torrent.recheckProgress) # XXX: what is this? :D
			elif status == 'downloading':
				peerText = _("Downloading from %d of %d peers") % (torrent.peersSendingToUs, torrent.peersConnected)
				progressText = _("Downloaded %d of %d MB (%d%%)") % (torrent.downloadedEver/1048576, torrent.sizeWhenDone/1048576, torrent.progress)
			elif status == 'seeding':
				peerText = _("Seeding to %d of %d peers") % (torrent.peersGettingFromUs, torrent.peersConnected)
				progressText = _("Downloaded %d and uploaded %d MB") % (torrent.downloadedEver/1048576, torrent.uploadedEver/1048576)
			elif status == 'stopped':
				peerText = _("stopped")
				progressText = _("Downloaded %d and uploaded %d MB") % (torrent.downloadedEver/1048576, torrent.uploadedEver/1048576)
			self["peers"].text = peerText
			self["progress_text"].text = progressText
			self["ratio"].text = _("Ratio: %.2f") % (torrent.ratio)
			self["eta"].text = _("Remaining: %s") % (torrent.eta or '?:??:??')

			# XXX: we should not need to set this all the time but when we enter this screen we just don't have this piece of information
			trackers = torrent.trackers
			if trackers:
				self["tracker"].text = str(_("Tracker: %s") % (trackers[0]['announce']))
			self["private"].text = _("Private: %s") % (torrent.isPrivate and _("yes") or _("no"))

			l = []
			files = torrent.files()
			for id, x in files.items():
				completed = x['completed']
				size = x['size'] or 1 # to avoid division by zero ;-)
				l.append((id, x['priority'], str(completed/1048576) + " MB",
					x['selected'], str(x['name']), str(size/1048576) + " MB",
					x['selected'] and _("downloading") or _("skipping"),
					int(100*(completed / float(size)))
				))

			index = min(self["files"].index, len(l)-1)
			self["files"].setList(l)
			self["files"].index = index
		self.timer.startLongTimer(5)

	def ok(self):
		cur = self["files"].getCurrent()
		if cur:
			self.timer.stop()
			id = self.torrentid
			try:
				torrent = self.transmission.info([id])[id]
				files = torrent.files()

				# XXX: we need to make sure that at least one file is selected for
				# download so unfortunately we might have to check all files if
				# we are unselecting this one
				if cur[3]:
					files[cur[0]]['selected'] = False
					atLeastOneSelected = False
					for file in files.values():
						if file['selected']:
							atLeastOneSelected = True
							break
					if not atLeastOneSelected:
						self.session.open(
							MessageBox,
							_("Unselecting the only file scheduled for download is not possible through RPC."),
							type=MessageBox.TYPE_ERROR
						)
						self.updateList()
						return
				else:
					files[cur[0]]['selected'] = True

				self.transmission.set_files({self.torrentid: files})
			except transmission.TransmissionError as te:
				self.session.open(
					MessageBox,
					_("Error communicating with transmission-daemon: %s.") % (te),
					type=MessageBox.TYPE_ERROR,
					timeout=5
				)
			self.updateList()

	def close(self):
		self.timer.stop()
		Screen.close(self)

