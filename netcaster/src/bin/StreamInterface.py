from urllib import urlopen

valid_types = ("MP3","PLS") #list of playable mediatypes

class StreamInterface:
    def __init__(self,session,cbListLoaded=None):
        self.session = session
        self.cbListLoaded = cbListLoaded
        
        self.list= [] # contains the streams in this iface
        
    def getList(self):
        #loads a list auf Streams into self.list
        pass
    
    def getMenuItems(self,selectedStream,generic=False):
        # this return a list of MenuEntries of actions of this iterface
        # list=(("item1",func1),("item2",func2), ... )
        #
        # generic=True indicates, that items of the returned list are services 
        # in any context (like saving a stream to the favorites)
        return []
    
    def OnListLoaded(self):
        # called from the interface, if list was loaded
        if self.cbListLoaded is not None:
            self.cbListLoaded(self.list)
    
############################################################################### 
class Stream:
    isfavorite = False
    def __init__(self,name,description,url,type="mp3"):
        self.name = name
        self.description = description
        self.url = url
        self.type=type
    def getName(self):
        return self.name
    def getDescription(self):
        return self.description
    def setName(self,name):
        self.name = name
    def setDescription(self,description):
        self.description = description
    def setURL(self,url):
        self.url = url
    def getURL(self):
        if self.type.lower() == "pls":
            return self.getPLSContent()
        else:
            return self.url

    def getPLSContent(self):
        print "loading PLS of stream ",self.name,self.url
        url = None
        try:
            fp = urlopen(self.url)
            plslines = fp.read()
            fp.close()
            print plslines
            plslines = plslines.split("\n")
            for line in plslines:
                if line.startswith("File"):
                    url = line.split("=")[1].rstrip().strip()              
        except IOError,e:
            print "Error while loading PLS of stream ",self.getName(),"! ",e
        return url
        
    def setFavorite(self,TrueFalse):
        self.isfavorite = TrueFalse
    def isFavorite(self):
        return self.isfavorite
    def setType(self,type):
        self.type=type
    def getType(self):
        return self.type
    