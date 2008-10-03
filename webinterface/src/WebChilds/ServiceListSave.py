from twisted.web2 import resource, http, responsecode, http_headers
from twisted.web2 import server,fileupload
from enigma import eDVBDB
import os
from xml.dom.minidom import parseString as xml_dom_minidom_parseString
from urllib import unquote as urllib_unquote
##########################
class ServiceList(resource.Resource):
    def __init__(self,session):
        self.session = session
        resource.Resource.__init__(self)
        self.putChild("reload",ServiceListReload())
        self.putChild("save",ServiceListSave())
        
class ServiceListReload(resource.Resource):
    def render(self, req):
        headers = http_headers.Headers()
        try:
            db = eDVBDB.getInstance()
            #db.reloadServicelist() # reloading only lamedb
            db.reloadBouquets() # reloading *.tv and *.radio
            return http.Response(responsecode.OK,headers,stream="Servicelist reloaded")
        except Exception,e:
            return http.Response(responsecode.OK,headers,stream="Error while loading Servicelist!")
        
        
class ServiceListSave(resource.PostableResource):
    TYPE_TV = 0
    TYPE_RADIO = 1
    EXTENSIONS = ['.tv','.radio']
    DIR = "/etc/enigma2/"
    undefinded_tag = "%n/a%"
    undefinded_and = "%und%"
    
    def http_POST(self, request):
        """
        overwriten, because we need a custom parsePOSTData
        """
        return self.parsePOSTData(request).addCallback(
            lambda res: self.render(request))
        
    def parsePOSTData(self,request):
        """
        overwriten, because we need to set higher values to fileupload.parse_urlencoded
        """
        if request.stream.length == 0:
            return defer.succeed(None)
    
        parser = None
        ctype = request.headers.getHeader('content-type')
        print "#"*20,ctype
        if ctype is None:
            return defer.succeed(None)
    
        def updateArgs(data):
            args = data
            request.args.update(args)
    
        def updateArgsAndFiles(data):
            args, files = data
            request.args.update(args)
            request.files.update(files)
    
        def error(f):
            f.trap(fileupload.MimeFormatError)
            raise http.HTTPError(responsecode.BAD_REQUEST)
    
        if ctype.mediaType == 'application' and ctype.mediaSubtype == 'x-www-form-urlencoded':
            d = fileupload.parse_urlencoded(request.stream, maxMem=100*1024*1024, maxFields=1024)
            d.addCallbacks(updateArgs, error)
            return d
        else:
            raise http.HTTPError(responsecode.BAD_REQUEST)
 

    def render(self, req):
        XML_HEADER = {'Content-type': http_headers.MimeType('application', 'xhtml+xml', (('charset', 'UTF-8'),))}
        
        try:
            content = req.args['content'][0].replace("<n/a>",self.undefinded_tag).replace('&',self.undefinded_and)            
            if content.find('undefined')!=-1:
                fp = open('/tmp/savedlist','w')
                fp.write(content)
                fp.close()
                result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
                        <e2simplexmlresult>\n
                            <e2state>false</e2state>
                            <e2statetext>found string 'undefined in XML DATA... a copie was saved to '/tmp/savedlist'.</e2statetext>
                        </e2simplexmlresult>\n
                     """    
                return http.Response(responsecode.OK,XML_HEADER,stream=result)

            (bouqets_tv,bouqets_radio) = self.parseXML( content)
            #print "having num %i TV Bouqets and num %i Radio Bouqets" %(len(bouqets_tv),len(bouqets_radio))
                
            #deleting old files
            os.system("rm "+self.DIR+"userbouquet*.tv ")
            os.system("rm "+self.DIR+"userbouquet*.radio ")
            os.system("rm "+self.DIR+"bouquets.tv ")
            os.system("rm "+self.DIR+"bouquets.radio ")
                
            #writing new files
            self.createIndexFile(self.TYPE_TV, bouqets_tv)
            counter = 0
            for bouqet in bouqets_tv:
                self.createBouqetFile(self.TYPE_TV, bouqet['bname'], bouqet['services'],counter)
                counter = counter +1
            
            self.createIndexFile(self.TYPE_RADIO, bouqets_radio)
            counter = 0
            for bouqet in bouqets_radio:
                self.createBouqetFile(self.TYPE_RADIO, bouqet['bname'], bouqet['services'],counter)
                counter = counter +1
                
            # reloading *.tv and *.radio
            db = eDVBDB.getInstance()
            db.reloadBouquets() 
            print "servicelists reloaded"
            result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
                        <e2simplexmlresult>\n
                            <e2state>true</e2state>
                            <e2statetext>servicelist saved with %i TV und %i Radio Bouquets and was reloaded</e2statetext>
                        </e2simplexmlresult>\n
                     """ %(len(bouqets_tv),len(bouqets_radio))       
            return http.Response(responsecode.OK,XML_HEADER,stream=result)
        except Exception,e:
            print e
            result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n
                        <e2simplexmlresult>\n
                            <e2state>false</e2state>
                            <e2statetext>%s</e2statetext>
                        </e2simplexmlresult>\n
                     """%e        
            return http.Response(responsecode.OK,XML_HEADER,stream=result)

        
    def parseXML(self,xmldata):
        print "parsing xmldata with length", len(xmldata)
        xmldoc = xml_dom_minidom_parseString(xmldata);
        blist = xmldoc.getElementsByTagName("e2bouqetlist")[0]
        print "Num TV Bouqets",len(blist.getElementsByTagName('e2tvbouqetlist')[0].getElementsByTagName('e2bouqet'))
        print "Num RADIO Bouqets",len(blist.getElementsByTagName('e2radiobouqetlist')[0].getElementsByTagName('e2bouqet'))
        
        bouqets_tv =self.parseBouqets(blist.getElementsByTagName('e2tvbouqetlist')[0])
        bouqets_radio =self.parseBouqets(blist.getElementsByTagName('e2radiobouqetlist')[0])
        return bouqets_tv,bouqets_radio
    
    def parseBouqets(self,xmlnode):
        #print "parsing Bouqets", xmlnode
        list = []
        for bouqet in xmlnode.getElementsByTagName('e2bouqet'):
            bref = urllib_unquote(bouqet.getElementsByTagName('e2bouqetreference')[0].childNodes[0].data)
            bname = urllib_unquote(bouqet.getElementsByTagName('e2bouqetname')[0].childNodes[0].data)
            #print "BOUQET",bref,bname
            list.append({'bname':bname,'bref':bref,'services':self.parseServices(bouqet)})
        return list
    
    def parseServices(self,xmlnode):
        #print "parsing Services", xmlnode
        list = []
        for service in xmlnode.getElementsByTagName('e2servicelist')[0].getElementsByTagName('e2service'):
            sref = urllib_unquote(service.getElementsByTagName('e2servicereference')[0].childNodes[0].data)
            sname = urllib_unquote(service.getElementsByTagName('e2servicename')[0].childNodes[0].data)
            sname = sname.replace(self.undefinded_tag,"<n/a>").replace(self.undefinded_and,"&")
            #print sref,sname
            list.append({'sref':sref,'sname':sname})
        return list
    
    def createBouqetFile(self,type,bname,list_services,counter):
        print "creating file for bouqet",bname,"with",len(list_services),"services for type",type
        filename  = self.getFilenameForBouqet(type,bname,counter)
        fcontent  = "#NAME %s\n" %bname  
        for service in list_services:
            fcontent += "#SERVICE %s\n" % service['sref']        
            fcontent += "#DESCRIPTION %s\n" % service['sname']    
        fcontent=fcontent.encode('utf-8')
        fp = open(self.DIR+filename,"w")
        fp.write(fcontent)
        fp.close()
        
    def createIndexFile(self,type, bouqets):
        print "creating Indexfile with",len(bouqets),"num bouqets for type",type
        filename  = self.getFilenameForIndex(type)
        if(type == self.TYPE_TV):
            fcontent  = "#NAME User - bouquets (TV)\n"
        else:  
            fcontent  = "#NAME User - bouquets (Radio)\n"
        counter = 0;    
        for bouqet in bouqets:
            fcontent += "#SERVICE: 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET \"%s\" ORDER BY bouquet\n" %self.getFilenameForBouqet(type, bouqet['bname'],counter)
            counter = counter+1

        fp = open(self.DIR+filename,"w")
        fp.write(fcontent)
        fp.close()
        
    def getFilenameForBouqet(self,type,bouqetname,counter):
        if bouqetname == "Favourites (TV)" and type == self.TYPE_TV:
            s =  "userbouquet.favourites%s" %self.EXTENSIONS[type]
        elif bouqetname == "Favourites (Radio)" and type == self.TYPE_RADIO:
            s =  "userbouquet.favourites%s" %self.EXTENSIONS[type]
        else:
            s =  "userbouquet.%i%s" %(counter,self.EXTENSIONS[type])
        return s
    
    def getFilenameForIndex(self,type):
        return "bouquets"+self.EXTENSIONS[type]

