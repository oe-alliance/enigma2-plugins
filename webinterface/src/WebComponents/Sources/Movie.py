from enigma import *
from enigma import eServiceReference, iServiceInformation
from Components.Sources.Source import Source
from ServiceReference import ServiceReference,eServiceCenter
#from Components.MovieList import MovieList
from Tools.Directories import resolveFilename,SCOPE_HDD

import os
#import sys, traceback

class Movie( Source):
    LIST = 0
    DEL = 1
    TAGS = 2
    
    def __init__(self, session,movielist,func = LIST):
        Source.__init__(self)
        self.func = func
        self.session = session
        self.root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD))
        self.movielist = movielist#MovieList(self.root)
        self.movielist.load(self.root,None)
    
    def handleCommand(self,cmd):
        self.cmd = cmd
        if self.func is self.DEL:
            self.result = self.delMovieFiles(cmd)
        else:
            self.result = False,"unknown command"

           
    def delMovieFiles(self,param):
        print "delMovieFiles:",param
        
        if param is None:
            return False,"title missing"
        
        #os.system("rm -f %s*" % param)
        try:
            os.system('rm -f "%s"' % param)
            #.ap .cuts .meta
            if os.path.exists("%s.ap" % param):
                os.system('rm -f "%s.ap"' % param)
            
            if os.path.exists("%s.cuts" % param):
                os.system('rm -f "%s.cuts"' % param)
            
            if os.path.exists("%s.meta" % param):
                os.system('rm -f "%s.meta"' % param)
            
            if os.path.exists("%s.eit" % param):
                os.system('rm -f "%s.eit"' % param)
        except OSError:
            return False,"OSErrorSome error occurred while deleting file"
        
        if os.path.exists(param):
            return False,"Some error occurred while deleting file"
        else:
            return True,"File deleted"
   
    def command(self):
        self.movielist.reload(root=self.root)
        list=[]
        for (serviceref, info, begin,unknown) in self.movielist.list:
            movie = []
            movie.append(serviceref.toString())
            movie.append(ServiceReference(serviceref).getServiceName())
            movie.append(info.getInfoString(serviceref, iServiceInformation.sDescription))
            
            sourceERef =info.getInfoString(serviceref, iServiceInformation.sServiceref)
            sourceRef= ServiceReference(sourceERef)
            
            movie.append(sourceRef.getServiceName())
            movie.append(info.getInfoString(serviceref, iServiceInformation.sTags))
            event = info.getEvent(serviceref)
            if event is not None:
                text = event.getEventName()
                short = event.getShortDescription()
                ext = event.getExtendedDescription()
                movie.append(ext)
            else:
                movie.append("")
            filename = "/"+"/".join(serviceref.toString().split("/")[1:])
            movie.append(filename)
            if info.getInfoString(serviceref, iServiceInformation.sTags).lower().find(self.cmd.lower())>=0:
                """ add movie only to list, if a givven tag is applied to the movie """
                list.append(movie)
        return list

    def getText(self):
        if self.func is self.DEL: 
            (result,text) = self.result
            xml  = "<e2simplexmlresult>\n"
            if result:
                xml += "<e2state>True</e2state>\n"
            else:
                xml += "<e2state>False</e2state>\n"            
            xml += "<e2statetext>%s</e2statetext>\n" % text
            xml += "</e2simplexmlresult>\n"
            return xml
        elif self.func is self.TAGS:
            xml = "<e2movietags>\n"
            for tag in self.movielist.tags:
                xml += "<e2movietag>%s</e2movietag>\n"%tag
            xml += "</e2movietags>\n"
            return xml
            
    text = property(getText)        
    
    list = property(command)
    lut = {"ServiceReference": 0
           ,"Title": 1
           ,"Description": 2
           ,"ServiceName": 3
           ,"Tags": 4
           ,"DescriptionExtended": 5
           ,"Filename": 6
           }

