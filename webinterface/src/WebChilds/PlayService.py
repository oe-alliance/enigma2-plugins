from enigma import eServiceReference
from twisted.web2 import resource, stream, responsecode, http
import os

class ServiceplayerResource(resource.Resource):
    def __init__(self,session):
        resource.Resource.__init__(self)
        self.session = session
        self.oldservice = None
        
    def render(self, req):
        if req.args.has_key("file"):
            output = self.playFile(req.args['file'][0])
        elif req.args.has_key("url"):
            output = self.playURL(req.args['url'][0])
        elif req.args.has_key("stop"):
            output = self.stopServicePlay()
        else:
            output = True,"unknown command"
        return http.Response(responsecode.OK,stream=output[1])
    
    def playFile(self,path):
        print "[ServiceplayerResource] playing file",path
        if os.path.exists(path) is not True:
            return False,"given path is not existing, %s"%path
        else:
            sref = "4097:0:0:0:0:0:0:0:0:0:%s"%path
            self.startServicePlay(eServiceReference(sref))
            return True,"playing path started, %s"%path
        
    def playURL(self,url):
        #url= url.replace("%3a",":").replace("%20"," ")
        #print "[ServiceplayerResource] playing url",url
        #sref = "4097:0:0:0:0:0:0:0:0:0:%s"%url
        #self.startServicePlay(eServiceReference(sref))
        return False,"Not implemented"
    
    def startServicePlay(self,esref):
        print "[ServiceplayerResource] playing sref",esref.toString()
        csref = self.session.nav.getCurrentlyPlayingServiceReference()
        if csref is not None:
            if csref.toString().startswith("4097") is not True:
                self.oldservice = csref.toString(),csref
        
        self.session.nav.stopService()
        self.session.nav.playService(esref)
        
    def stopServicePlay(self):
        print "[ServiceplayerResource] stopping service",self.oldservice
        self.session.nav.stopService()
        if self.oldservice is not None:
            self.session.nav.playService(self.oldservice[1])
            return True, "[ServiceplayerResource] stopped, now playing old service, %s"%self.oldservice[0]
        else:
            return True, "[ServiceplayerResource] stopped"