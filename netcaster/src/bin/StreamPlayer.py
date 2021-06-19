from __future__ import print_function
from enigma import eServiceReference, iServiceInformation


class StreamPlayer:
	is_playing = False

	def __init__(self, session, args=0):
	    print("[NETcaster.StreamPlayer] init StreamPlayer")
	    self.is_playing = False
	    self.session = session
	    self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
	    self.session.nav.event.append(self.__event)
	    self.metadatachangelisteners = []
	    self.onStop = []

	def __event(self, ev):
	    print("[NETcaster.StreamPlayer] EVENT ==>", ev)
	    if ev == 5: # can we use a constant here instead of just 5?
   			currentServiceRef = self.session.nav.getCurrentService()
   			if currentServiceRef is not None:
   				#it seems, that only Title is avaible for now
   				sTagTitle = currentServiceRef.info().getInfoString(iServiceInformation.sTagTitle)
				self._onMetadataChanged(sTagTitle)
# TODO: Figure out the correct event for "STOP", 1 appears to be wrong.
#	    elif ev == 1:
#	       for c in self.onStop:
#	           c()

	def _onMetadataChanged(self, title):
		for i in self.metadatachangelisteners:
			i(title)

	def play(self, stream):
	    if self.is_playing:
	        self.stop()
	    stream.getURL(self._playURL)

	def _playURL(self, url=None):
		if not url:
			print("no URL provided for play")
			return
		print("[NETcaster.StreamPlayer] playing stream", url)

		esref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s" % url.replace(':', '%3a'))

		try:
			self.session.nav.playService(esref)
			self.is_playing = True
		except:
			print("[NETcaster.StreamPlayer] Could not play %s" % esref)

	def stop(self, text=""):
	    if self.is_playing:
	        print("[NETcaster.StreamPlayer] stop streaming", text)
	        try:
	            self.is_playing = False
	            self.session.nav.stopService()
	            self.session.nav.playService(self.oldService)
	        except TypeError as e:
	            print(" ERROR Z", e)
	            self.exit()

	def exit(self):
	    self.stop()
