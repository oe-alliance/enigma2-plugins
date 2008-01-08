from Components.Sources.Source import Source
from Tools.ISO639 import LanguageCodes

class AudioTracks( Source ):
    
    GET = 0
    SET = 1
    
    text="False"
    
    def __init__(self, session, func=GET):
        self.session = session
        self.func = func
        Source.__init__(self)
    
    def handleCommand(self, cmd):
        self.cmd = cmd
    
    def setAudioTrack(self):
        service = self.session.nav.getCurrentService()
        audio = service and service.audioTracks()
        try:
            cmd = int(self.cmd)
        except ValueError:
            cmd = -1
            
        print "COMMAND is %s" %self.cmd
        if self.session.nav.getCurrentService().audioTracks().getNumberOfTracks() > cmd and cmd >= 0:
            audio.selectTrack(cmd)
            return "Success"
        else:
            return "Error"
     
    def getAudioTracks(self):
        service = self.session.nav.getCurrentService()
        audio = service and service.audioTracks()
        n = audio and audio.getNumberOfTracks() or 0
        currentTrack = audio.getCurrentTrack()
        tlist = []

        if n > 0:
            print "[AudioTracks.py] got %s Audiotracks!" %(n)
            
            for x in range(n):
                i = audio.getTrackInfo(x)
                for name in dir(i):
                    print getattr(i, name)
                language = i.getLanguage()
                description = i.getDescription()
                pid = i.getPID()
                
                if LanguageCodes.has_key(language):
                    language = LanguageCodes[language][0]
                
                if len(description):
                    description += " (" + language + ")"
                else:
                    description = language
                
                if x == currentTrack:
                    active = "True"
                else:
                    active = "False"
                
                tlist.append((description, x, pid, active))
        
        return tlist
    
    text = property(setAudioTrack)
    list = property(getAudioTracks)
    lut = {"Description": 0, "Id": 1, "Pid": 2, "Active": 3}