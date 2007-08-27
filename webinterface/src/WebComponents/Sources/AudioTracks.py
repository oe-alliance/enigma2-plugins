from Components.Sources.Source import Source
from Tools.ISO639 import LanguageCodes

class AudioTracks( Source ):
    
    def __init__(self, session):
        self.session = session
        Source.__init__(self)
        
    def getList(self):
        service = self.session.nav.getCurrentService()
        audio = service and service.audioTracks()
        n = audio and audio.getNumberOfTracks() or 0
        tlist = []
        for name in dir(audio):
            print getattr(audio, name)
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
                
                tlist.append((description, x, pid))
        
        return tlist
    
    list = property(getList)
    lut = {"Description": 0, "Id": 1, "Pid": 2}