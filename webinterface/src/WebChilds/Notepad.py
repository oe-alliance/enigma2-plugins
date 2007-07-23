from os import path as os_path \
	listdir as os_listdir \
	system as os_system \
	stat as os_stat \
	mkdir as os_mkdir
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
        elif self.getArg("save"):
            return self.do_save()
        elif self.getArg("create"):
            return self.do_create()
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

    def do_show(self,filename,was_saved=False,oldfilename=False):

        if os_path.exists(self.DIR+filename) is not True:
            return self.errorFileNotFound(self.DIR+filename)
        else:    
            details = self.getNotesDetails(filename)
            fp = open(self.DIR+filename)
            con = fp.read()
            fp.close()
            content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            content += "<e2notedetails>\n"
            if was_saved:
                content += "<e2notesaved>True</e2notesaved>\n"
            if oldfilename is not False:
                content += "<e2notenameold>%s</e2notenameold>\n"%oldfilename
                    
            content += "<e2notename>%s</e2notename>\n"%details[0]
            content += "<e2notesize>%s</e2notesize>\n"%details[1]
            content += "<e2notemtime>%s</e2notemtime>\n"%details[2]
            content += "<e2notectime>%s</e2notectime>\n"%details[3]
            content += "<e2notecontent>%s</e2notecontent>\n"%con
            content += "</e2notedetails>"
        return self.send(content)
    
    def do_save(self):
        filename = self.getArg("save")
        filenamenew = self.getArg("namenew")
        content = self.getArg("content")
        if os_path.exists(self.DIR+filename) is not True:
            return self.errorFileNotFound(self.DIR+self.getArg("save"))
        else:  
            newname = False  
            if filename != filenamenew:
                os_system("mv '%s' '%s' " %(self.DIR+filename,self.DIR+filenamenew))
                newname = filename
                filename = filenamenew
                
            fp = open(self.DIR+filename,"w")
            fp.write(content)
            fp.close()
            return self.do_show(filename,was_saved=True,oldfilename=newname)
    def do_create(self):
        import random
        r = str(random.randrange(100000,999999))
        fp = open(self.DIR+'note_'+r,"w")
        fp.write("")
        fp.close()
        return self.send("file created")

    def getNotes(self):
        list = []
        if self.check_dir(force_create=True):
            for i in os_listdir(self.DIR):
                list.append(self.getNotesDetails(i))
        return list

    def getNotesDetails(self,file):
        fstat = os_stat(self.DIR+file)
        size = fstat[-4]
        mtime = fstat[-3]
        ctime = fstat[-1]
        return (file,size,mtime,ctime)
    
    def check_dir(self,force_create=False):
        if os_path.isdir(self.DIR):
            return True
        elif os_path.isdir(self.DIR) is False and force_create is True:
            return os_mkdir(self.DIR)
        else:
            return False
    
    
    def getArg(self,key):
        if self.args.has_key(key):
            return self.args[key][0]
        else:
            return False

    def errorFileNotFound(self,filename):
        content = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"        
        content += "<e2note>\n"
        content += "<e2result>False</e2result>\n"
        content += "<e2resulttext>File '%s' not found</e2resulttext>\n" % (filename)
        content += "</e2note>\n"
        return self.send(content)