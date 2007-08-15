from enigma import eConsoleAppContainer

from twisted.web2 import resource, stream, responsecode, http, http_headers

from os import path as os_path, remove as os_remove

class GrabResource(resource.Resource):
    """
        this is a interface to Seddis AiO Dreambox Screengrabber
    """
    grab_bin = "/usr/bin/grab" 
    grab_target = "/tmp/screenshot.bmp"
    
    def render(self, req):
        class GrabStream(stream.ProducerStream):
            def __init__(self,cmd,target=None,save=False):
                self.cmd = cmd
                self.target = target
                self.save = save
                self.output = ""
                stream.ProducerStream.__init__(self)
                
                self.container = eConsoleAppContainer()
                self.container.appClosed.get().append(self.cmdFinished)
                self.container.dataAvail.get().append(self.dataAvail)
                self.container.execute(cmd)

            def cmdFinished(self,data):
                if int(data) is 0 and self.target is not None:
                    try:
                        fp = open(self.target)
                        self.write(fp.read())
                        fp.close()
                        if self.save is False:
                            os_remove(self.target)
                    except Exception,e:
                        self.write("internal error while reading target file")                        
                elif int(data) is 0 and self.target is None:
                    self.write(self.output)
                elif int(data) is 1:
                    self.write(self.output)
                else:
                    self.write("internal error")
                self.finish()    
                    
            def dataAvail(self,data):
                self.output += data
            
        if req.args.has_key("filename"):
            filetarget = req.args['filename'][0]
        else:
            filetarget = self.grab_target
        
        if req.args.has_key("save"):
            save_image = True
        else:
            save_image = False
        
        headers = http_headers.Headers()
        headers.addRawHeader('Content-Disposition', 'inline; filename=screenshot.bmp;')
        headers.addRawHeader('Content-Type','image/bmp')
        
        if os_path.exists(self.grab_bin) is not True:
            return    http.Response(responsecode.OK,stream="grab is not installed at '%s'. go and fix it."%self.grab_bin)
        elif req.args.has_key("command"): 
            cmd = req.args['command'][0].replace("-","")
            if cmd == "o":
                return http.Response(responsecode.OK,headers,stream=GrabStream(self.grab_bin+" -o "+filetarget,target=filetarget,save=save_image))
            elif cmd == "v":
                return http.Response(responsecode.OK,headers,stream=GrabStream(self.grab_bin+" -v "+filetarget,target=filetarget,save=save_image))
            elif cmd == "":
                return http.Response(responsecode.OK,headers,stream=GrabStream(self.grab_bin+" "+filetarget,target=filetarget,save=save_image))
            else:
                return http.Response(responsecode.OK,headers,stream=GrabStream(self.grab_bin+" -h"))
        else:
            return http.Response(responsecode.OK,headers,stream=GrabStream(self.grab_bin+" "+filetarget,target=filetarget,save=save_image))
