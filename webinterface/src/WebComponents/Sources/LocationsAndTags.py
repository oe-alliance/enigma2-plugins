from Components.Sources.Source import Source
from Components.config import config

class LocationsAndTags(Source):
    LOCATIONS = 0
    TAGS = 1
    
    def __init__(self, session, func):
        self.func = func
        Source.__init__(self)        
        self.session = session
        self.result = False,"one two three four unknown command"

    def handleCommand(self, cmd):
        if self.func is self.LOCATIONS:
            self.result = True,self.getLocations()
        elif self.func is self.TAGS:
            self.result = True,self.getTags()
        else:
            self.result = False,"unknown command"

    def getLocations(self):
        return " ".join(config.movielist.videodirs.value)

    def getTags(self):
        try:
            file = open("/etc/enigma2/movietags")
            tags = [x.rstrip() for x in file.readlines()]
            while "" in tags:
                tags.remove("")
            file.close()
        except IOError, ioe:
            tags = []
        return " ".join(tags)

    def getText(self):
        self.handleCommand("")
        print self.result
        (result,text) = self.result
        xml  = "<e2simplexmlresult>\n"
        if result:
            xml += "<e2state>True</e2state>\n"
        else:
            xml += "<e2state>False</e2state>\n"            
        xml += "<e2statetext>%s</e2statetext>\n" % text
        xml += "</e2simplexmlresult>\n"
        return xml
    
    text = property(getText)
