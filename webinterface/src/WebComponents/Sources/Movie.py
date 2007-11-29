from enigma import eServiceReference, iServiceInformation
from Components.Sources.Source import Source
from Components.config import config
from ServiceReference import ServiceReference
from Tools.Directories import resolveFilename, SCOPE_HDD
from Tools.FuzzyDate import FuzzyTime

from os import path as os_path, stat as os_stat, system as os_system

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
        self.cmd = ""
    
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
        
        #os_system("rm -f %s*" % param)
        try:
            os_system('rm -f "%s"' % param)
            #.ap .cuts .meta
            if os_path.exists("%s.ap" % param):
                os_system('rm -f "%s.ap"' % param)
            
            if os_path.exists("%s.cuts" % param):
                os_system('rm -f "%s.cuts"' % param)
            
            if os_path.exists("%s.meta" % param):
                os_system('rm -f "%s.meta"' % param)
            
            if os_path.exists("%s.eit" % param):
                os_system('rm -f "%s.eit"' % param)
        except OSError:
            return False,"OSErrorSome error occurred while deleting file"
        
        if os_path.exists(param):
            return False,"Some error occurred while deleting file"
        else:
            return True,"File deleted"
   
    def command(self):
        #self.movielist.reload(root=self.root)
        list=[]
        for (serviceref, info, begin,unknown) in self.movielist.list:
            movie = []
            movie.append(serviceref.toString())
            movie.append(ServiceReference(serviceref).getServiceName())
            movie.append(info.getInfoString(serviceref, iServiceInformation.sDescription))
            rtime = info.getInfo(serviceref, iServiceInformation.sTimeCreate)
            movie.append(rtime)
            
            if rtime > 0:
                t = FuzzyTime(rtime)
                begin_string = t[0] + ", " + t[1]
            else:
                begin_string = "undefined"
            movie.append(begin_string)
            
            
            if config.plugins.Webinterface.loadmovielength.value:
                len =  info.getLength(serviceref)
                if len > 0:
                    len = "%d:%02d" % (len / 60, len % 60)
                else:
                    len = "?:??"
            else:
                len="disabled"
            movie.append(len)
            
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
            movie.append(os_stat(filename)[6])
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
           ,"Time": 3
           ,"TimeString": 4
           ,"Length": 5
           ,"ServiceName": 6
           ,"Tags": 7
           ,"DescriptionExtended": 8
           ,"Filename": 9
           ,"Filesize": 10
           }

