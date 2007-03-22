from Plugins.Extensions.NETcaster.StreamInterface import StreamInterface
from Plugins.Extensions.NETcaster.StreamInterface import Stream
from Plugins.Extensions.NETcaster.StreamInterface import valid_types
from Plugins.Extensions.NETcaster.plugin import myname
from Screens.ChoiceBox import ChoiceBox

import urllib,re

####
genres = [
    "TopTen",
    "Alternative",
    "College",
    "Industrial",
    "Punk",
    "Hardcore",
    "Ska",
    "Americana",
    "Blues",
    "Folk",
    "Cajun",
    "Bluegrass",
    "Classical",
    "Opera",
    "Symphonic",
    "Western Swing",
    "New Country",
    "Electronic",
    "Ambient",
    "Drum and Bass",
    "Trance",
    "Techno",
    "House",
    "Downtempo",
    "Breakbeat",
    "Acid Jazz",
    "Hip Hop",
    "Turntablism",
    "Old School",
    "New School",
    "Jazz",
    "Swing",
    "Big Band",
    "Smooth",
    "Pop/Rock",
    "Oldies",
    "80s",
    "Top 40",
    "Metal",
    "Rock",
    "R&B/Soul",
    "Contemporary",
    "Classic",
    "Funk",
    "Urban",
    "Spiritual",
    "Pop",
    "Gospel",
    "Country",
    "Spoken",
    "Talk",
    "Comedy",
    "Spoken Word",
    "World",
    "Reggae",
    "African",
    "Latin",
    "European",
    "Middle Eastern",
    "Asian",
    "Other/Mixed",
    "Eclectic",
    "Film",
    "Instrumental"]



class Interface(StreamInterface):
    name= "listen to SHOUTcast Streams"
    nameshort = "SHOUTcast"
    description = "This is a Plugin to browse www.shoutcast.com and listen to webradios listed there."
    
    def getList(self):
        glist=[]
        for i in SHOUTcastRipper().getGenreList():
            glist.append((i,i))
        self.session.openWithCallback(self.GenreSelected,ChoiceBox,_("select Genre to search for streams"),glist)

    def GenreSelected(self,selectedGenre):
        if selectedGenre is not None:
            streams = SHOUTcastRipper().getGenre(selectedGenre[1])
            print "["+myname+"] found ",len(streams),"in Genre ",selectedGenre[1]
            listnew=[]
            for i in streams:
                stream = Stream(i.getTitle(),"Bitrate: "+i.getBitrate()+", Type: "+i.getType(),i.getPlaylist(),type="pls")
                listnew.append(stream)
            
            self.list = listnew
        self.OnListLoaded()


##########################################################################    

class SHOUTcastRipper:
    def __init__(self):
        pass
    def getTopTen(self):
        return self.getGenre("TopTen")
    def getGenreList(self):
        genres.sort()
        return genres
    def getGenre(self,genre):
        genre = genre.replace(" ","%20")
        genre = genre.replace("&","%26")
        return self.read_doc("http://www.shoutcast.com/directory/?orderby=bitrate&s=%s"%genre)
    
    def read_doc(self,url):
        print "["+myname+"] loading url",url
        fp = urllib.urlopen(url)
        html = fp.read()
        streams=[]
        trs = html.split("<tr")
        for tr in trs:
            if tr.find("&file=filename.pls") is not -1:
                stream = self.parse_item(tr)
                if self.isValiteStream(stream):
                    streams.append(stream)
        fp.close()
        return streams

    def isValiteStream(self,stream):
        for type in valid_types:
            if stream.getType().lower().startswith(type.lower()):
                return True
            else:
                return False
    def parse_item(self,item):
        
        x = item.splitlines()
        if item.find("Now Playing:") is not -1:
            offset = 0
        else:
            offset = -1
        stream = SHOUTcastStream()
        stream.setPlaylist(self.parse_pls(x[3]))
        stream.setTitle(self.parse_title(x[5]))
        stream.setBitrate(self.parse_Bitrate(x[11+offset]))
        stream.setType(self.parse_type(x[16+offset]))
        
        return stream
    
    def parse_Bitrate(self,item):
        item = re.sub(r'<(.*?)>(?uism)', '', "<td"+item)
        item = item.replace("\n","")
        item = item.rstrip().strip()
        return item
    
    def parse_type(self,item):
        item = re.sub(r'<(.*?)>(?uism)', '',item)
        item = item.replace("\n","")
        item = item.rstrip().strip()
        return item
    def parse_pls(self,item):
        print "+",item
        istart = item.find("<a href=\"")
        istop = item.find("\">",istart)
        item = item[(istart+9):istop]
        print "*",item
        return "http://www.shoutcast.com"+item
    
    def parse_title(self,item):
        istart = item.find("<a id=\"listlinks\"")
        istop = item.find("</a>",istart)
        item = item[istart:(istop+4)]
        item = re.sub(r'<(.*?)>(?uism)', '',item)    
        return item
    
##########################################################################    
class SHOUTcastStream:
    title= ""
    playlist= ""
    bitrate= ""
    type=""
    def __init__(self):
        pass
    def setTitle(self,title):
        self.title= title
    def getTitle(self):
        return self.title
    def setPlaylist(self,url):
        self.playlist = url
    def getPlaylist(self):
        return self.playlist
    def setBitrate(self,bitrate):
        self.bitrate = bitrate
    def getBitrate(self):
        return self.bitrate
    def setType(self,type):
        self.type = type
    def getType(self):
        return self.type
    def toString(self):
        return "SHOUTcastStream ("+self.getTitle()+", "+self.getPlaylist()+", "+self.getBitrate()+", "+self.getType()+")\n"

