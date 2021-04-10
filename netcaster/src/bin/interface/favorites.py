from __future__ import print_function
from Plugins.Extensions.NETcaster.StreamInterface import StreamInterface
from Plugins.Extensions.NETcaster.StreamInterface import Stream
from Plugins.Extensions.NETcaster.plugin import myname

from Tools.BoundFunction import boundFunction

from six.moves.configparser import ConfigParser, DuplicateSectionError


####################################################################

class Interface(StreamInterface):
    name= "Your saved Favorites"
    nameshort = "Favorites"
    description = "you can save Streams in your Favorites in a local list, to exec them directly without search for long time."
    selectedStream = None
    def getList(self):
        list = []
        for stream in SHOUTcasterFavorites().getStreams():
            list.append(stream)
        self.list = list
        self.OnListLoaded()
    def getMenuItems(self,selectedStream,generic=False):
        self.selectedStream = selectedStream
        list = []
        if generic is True and selectedStream is not None:
            if selectedStream.isFavorite() is False:
                list.append((_("add stream to favorites"), self.addStream))            
        elif generic is False and selectedStream is not None:
            if selectedStream.isFavorite() is False:
                list.append((_("add stream to favorites"), self.addStream))
            if selectedStream.isFavorite() is True:
                list.append((_("delete stream from favorites"), self.deleteStream))
        return list
    
    def deleteStream(self):
        print("favorites deleteStream")
        if self.selectedStream is not None:
            SHOUTcasterFavorites().deleteStreamWithName(self.selectedStream.getName())
        self.getList()
    def addStream(self):
        print("favorites addStream")
        if self.selectedStream is not None:
            SHOUTcasterFavorites().addStream(self.selectedStream)
        #self.getList()
############################################################################### 
class SHOUTcasterFavorites:
    configfile = "/etc/NETcaster.conf"
    def __init__(self):
        self.configparser = ConfigParser()
        self.configparser.read(self.configfile)
    def getStreams(self):
        streams=[]
        sections = self.configparser.sections()
        print(sections)
        for section in sections:
                stream = self.getStreamByName(section)
                streams.append(stream)
        return streams
    def isStream(self, streamname):
        if self.configparser.has_section(streamname) is True:
            return True
        else:
            return False
    def getStreamByName(self, streamname):
        print("["+myname+"] load "+streamname+" from config")
        if self.isStream(streamname) is True:
            stream = Stream(
                        streamname,
                        self.configparser.get(streamname, "description"),
                        self.configparser.get(streamname, "url"),
                        type=self.configparser.get(streamname, "type")
                    )
            stream.setFavorite(True)
            return stream
        else:
            return False

    def addStream(self, stream):
        print("["+myname+"] adding "+stream.getName()+" to config")
        try:
            self.configparser.add_section(stream.getName())
        except DuplicateSectionError as e:
            print("["+myname+"] error while adding stream to config:", e)
            return False, e
        else:
            # XXX: I hope this still works properly if we make a optimistic
            # return here since otherwise the interface would need to be changed
            # to work with a callback
            stream.getURL(boundFunction(self.addStreamCb, stream))
            return True, "Stream added"

    def addStreamCb(self, stream, url = None):
        self.configparser.set(stream.getName(), "description", stream.getDescription())
        self.configparser.set(stream.getName(), "url", url)
        self.configparser.set(stream.getName(), "type", stream.getType())
        self.writeConfig()

    def changeStream(self, streamold, streamnew):
        if self.configparser.has_section(streamold.getName()) is False:
            return False, "stream not found in config"
        elif self.configparser.has_section(streamnew.getName()) is True:
            return False, "stream with that name exists already"
        else:    
           self.configparser.remove_section(streamold.getName())
           return self.addStream(streamnew)
        
    def deleteStreamWithName(self, streamname):
        self.configparser.remove_section(streamname)
        self.writeConfig()
        
    def writeConfig(self):
        print("["+myname+"] writing config to "+self.configfile)
        
        fp = open(self.configfile, "w")
        self.configparser.write(fp)
        fp.close()
            
