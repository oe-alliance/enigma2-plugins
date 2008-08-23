from enigma import eConsoleAppContainer

from twisted.web2 import resource, stream, responsecode, http, http_headers

from os import path as os_path, remove as os_remove

class GrabResource(resource.Resource):
    """
        this is a interface to Seddis AiO Dreambox Screengrabber 
        version 0.8 or lower
    """
    grab_bin = "/usr/bin/grab"
    
    def render(self, req):
        grab_command = self.grab_bin+" "
        
        #choosing what to grab
        if req.args.has_key("command"):
            # using 'command' for older versions
            cmd = req.args['command'][0].replace("-","")
            if cmd == "o":
                #-o only grab osd (framebuffer)
                grab_command += " -o "
            elif cmd == "v":
                #-v only grab video
                grab_command += " -v "
        elif req.args.has_key("o"):
            grab_command += " -o "
        elif req.args.has_key("v"):
            grab_command += " -v " 
                  
        #chossing the imageformat
        if req.args.has_key("format"):
            formatraw = req.args["format"][0]
            if formatraw == "png":
                #-p produce png files instead of bmp
                imageformat = "png"
                grab_command += " -p "
            elif formatraw == "jpg":
                #-j (quality) produce jpg files instead of bmp (quality 0-100)
                imageformat = "jpg"
                if req.args.has_key("jpgquali"):
                    grab_command += " -j %s "%req.args["jpgquali"][0]
                else:    
                    grab_command += " -j 80 "
            else:
                imageformat = "bmp"
        else:
            imageformat = "bmp"

        
        #-d always use osd resolution (good for skinshots)
        if req.args.has_key("d"):
            grab_command += " -d " 

        #-n dont correct 16:9 aspect ratio
        if req.args.has_key("n"):
            grab_command += " -n " 
            
        #-r (size) resize to to a fixed width, maximum: 1920
        if req.args.has_key("r"):
            grab_command += " -r %s " % req.args['r'][0]

        #-l always 4:3, create letterbox if 16:9
        if req.args.has_key("l"):
            grab_command += " -l "

        #target filename
        if req.args.has_key("filename"):
            filetarget = req.args['filename'][0]
        else:
            filetarget = "/tmp/screenshot."+imageformat

        # choose if we leave the file in /tmp
        if req.args.has_key("save"):
            save_image = True
        else:
            save_image = False

        if os_path.exists(self.grab_bin) is not True:
            return http.Response(responsecode.OK,stream="grab is not installed at '%s'. go and fix it."%self.grab_bin)
        else:
            headers = http_headers.Headers()
            headers.addRawHeader('Content-Disposition', 'inline; filename=screenshot.%s;'%imageformat)
            headers.addRawHeader('Content-Type','image/%s'%imageformat)
            return http.Response(responsecode.OK,headers,stream=GrabStream(grab_command+filetarget,target=filetarget,save=save_image))
       
class GrabStream(stream.ProducerStream):
    """
        used to start the grab-bin in the console in the background
        while this takes some time, the browser must wait until the grabis finished
    """
    def __init__(self,cmd,target=None,save=False):
        self.cmd = cmd
        self.target = target
        self.save = save
        self.output = ""
        stream.ProducerStream.__init__(self)

        self.container = eConsoleAppContainer()
        self.container.appClosed.get().append(self.cmdFinished)
        self.container.dataAvail.get().append(self.dataAvail)
        print "AiO grab starting aio grab with cmdline:",self.cmd
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
        print "AiO grab:",data
