import os
from twisted.web2 import resource, responsecode, http,http_headers

class NotepadResource(resource.Resource):
    DIR = "/etc/enigma2/notes/"
    
    def render(self, req):
        self.args = req.args
        
        self.format = "xml"
        if self.getArg("format"):
            if self.getArg("format") == "html":
                self.format = "html"
        
        if self.getArg("show"):
            return self.do_show(self.getArg("show"))
        else:
            return self.do_index()
            
    def send(self,content):
        if self.format == "xml":
            ctype = http_headers.MimeType('application', 'xhtml+xml', (('charset', 'UTF-8'),))
        else:
            ctype = http_headers.MimeType('text', 'html', (('charset', 'UTF-8'),))
        return http.Response(responsecode.OK,{'content-type': ctype},content)                

    def do_index(self):
        content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        content += "<e2noteslist>\n"
        for note in self.getNotes():
            content += "<e2note>\n"
            content += "<e2notename>%s</e2notename>\n"%note[0]
            content += "<e2notesize>%s</e2notesize>\n"%note[1]
            content += "<e2notemtime>%s</e2notemtime>\n"%note[2]
            content += "<e2notectime>%s</e2notectime>\n"%note[3]
            content += "</e2note>\n"
        content += "</e2noteslist>"
        return self.send(content)

    def do_show(self,filename):
        content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        if os.path.exists(self.DIR+filename) is not True:
            content += "<e2note>\n"
            content += "<e2result>False</e2result>\n"
            content += "<e2resulttext>File '%s' not found</e2resulttext>\n" % (self.DIR+filename)
            content += "</e2note>\n"
        else:    
            details = self.getNotesDetails(filename)
            fp = open(self.DIR+filename)
            con = fp.read()
            fp.close()
            content += "<e2notedetails>\n"
            content += "<e2notename>%s</e2notename>\n"%details[0]
            content += "<e2notesize>%s</e2notesize>\n"%details[1]
            content += "<e2notemtime>%s</e2notemtime>\n"%details[2]
            content += "<e2notectime>%s</e2notectime>\n"%details[3]
            content += "<e2notecontent>%s</e2notecontent>\n"%con
            content += "</e2notedetails>"
        return self.send(content)
    
    def getNotes(self):
        list = []
        if self.check_dir(force_create=True):
            for i in os.listdir(self.DIR):
                list.append(self.getNotesDetails(i))
        return list

    def getNotesDetails(self,file):
        fstat = os.stat(self.DIR+file)
        size = fstat[-4]
        mtime = fstat[-3]
        ctime = fstat[-1]
        return (file,size,mtime,ctime)
    
    def check_dir(self,force_create=False):
        if os.path.isdir(self.DIR):
            return True
        elif os.path.isdir(self.DIR) is False and force_create is True:
            return os.mkdir(self.DIR)
        else:
            return False
    
    
    def getArg(self,key):
        if self.args.has_key(key):
            return self.args[key][0]
        else:
            return False
