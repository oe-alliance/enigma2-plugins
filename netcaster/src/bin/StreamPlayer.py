from enigma import eServiceReference

class StreamPlayer:
	is_playing = False

	def __init__(self, session, args=0):
	    print "[NETcaster.StreamPlayer] init StreamPlayer"
	    self.is_playing = False
	    self.session = session
	    self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
	    self.session.nav.event.append(self.__event)
	
	def __event(self, ev):
	    print "[NETcaster.StreamPlayer] EVENT ==>", ev
	
	def play(self, stream):
	    if self.is_playing:
	        self.stop()
	    stream.getURL(self._playURL)
	
	def _playURL(self, url=None):
		if not url:
			print "no URL provided for play"
			return
		print "[NETcaster.StreamPlayer] playing stream", url
		
		esref = eServiceReference("4097:0:0:0:0:0:0:0:0:0:%s" % url.replace(':', '%3a'))
		
		try:
			self.session.nav.playService(esref)
			self.is_playing = True
		except:
			print "[NETcaster.StreamPlayer] Could not play %s" % esref
	
	def stop(self, text=""):
	    if self.is_playing:
	        print "[NETcaster.StreamPlayer] stop streaming", text
	        try:
	            self.is_playing = False
	            self.session.nav.stopService()
	            self.session.nav.playService(self.oldService)
	        except TypeError, e:
	            print " ERROR Z", e
	            self.exit()

	def exit(self):
	    self.stop()

