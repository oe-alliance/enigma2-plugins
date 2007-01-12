from enigma import *
from enigma import eServiceReference, iServiceInformation
from Components.Sources.Source import Source
from ServiceReference import ServiceReference
from Components.MovieList import MovieList
from Tools.Directories import *
class Movie( Source):
    
    def __init__(self, session):
        Source.__init__(self)        
        self.session = session
        self.root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD))
        self.movielist = MovieList(self.root)
        self.movielist.load(self.root,None)
        
    def command(self):
        self.movielist.reload(root=self.root)
        list=[]
        for (serviceref, info, begin,unknown) in self.movielist.list:
            movie = []
            movie.append(serviceref.toString())
            movie.append(ServiceReference(serviceref).getServiceName())
            movie.append(info.getInfoString(serviceref, iServiceInformation.sDescription))
            #movie.append("eventdaten")#info.getEvent(serviceref).getExtendedDescription())
            
            sourceERef =info.getInfoString(serviceref, iServiceInformation.sServiceref)
            sourceRef= ServiceReference(sourceERef)
            #sourceInfo= sourceRef and sourceRef.info()
            
            movie.append(sourceRef.getServiceName())
            #movie.append("")#sourceInfo.getInfo(sourceRef,iServiceInformation.sProvider))
            
            #movie.append("x")
            #movie.append("y")
            movie.append(info.getInfoString(serviceref, iServiceInformation.sTags))
            list.append(movie)
        print "tags",self.movielist.tags
        return list
        
    list = property(command)
    lut = {"ServiceReference": 0
           ,"Title": 1
           ,"Description": 2
           ,"ServiceName": 3
           ,"Tags": 4
           }

