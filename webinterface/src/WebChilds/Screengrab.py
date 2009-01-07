from enigma import eConsoleAppContainer

from twisted.web2 import resource, stream, responsecode, http, http_headers

from os import path as os_path, remove as os_remove

class GrabResource(resource.Resource):
    '''
        this is a interface to Seddis AiO Dreambox Screengrabber
    '''
    GRAB_BIN = '/usr/bin/grab'
    SPECIAL_ARGS = ['format', 'filename', 'save'] 
    
    def render(self, req):
        self.baseCmd = ['/usr/bin/grab', '/usr/bin/grab']
        self.args = []
        
        # some presets
        filename = 'screenshot'
        imageformat = '.bmp'
        osdOnly = False
        videoOnly = False
        save = False
        
        for key, value in req.args.items():
            if key in GrabResource.SPECIAL_ARGS:                
                
                if key == 'format':                
                    format = req.args['format'][0]
                    
                    if format == 'png':
                        #-p produce png files instead of bmp
                        imageformat = ".%s" %format
                        self.args.append('-p')
                    elif format == 'jpg':
                        #-j (quality) produce jpg files instead of bmp
                    
                        imageformat = ".%s" %format
                        self.args.append('-j')
                        #Quality Setting                    
                        if req.args.has_key("jpgquali"):
                            self.args.append("%s" %(req.args["jpgquali"][0]) )
                        else:                            
                            self.args.append('80')
                
                elif key == 'filename':
                    filename = req.args['filename'][0]
                
                elif key == 'save':
                    save = True
                                                
            else:
                if key == "o" and videoOnly is True:
                    continue
                if key == "v" and osdOnly is True:
                    continue                                        
                                
                self.args.append("-%s" %key )
                
                if value is not None:
                    if len(value[0]) > 0:
                        self.args.append("%s" %value[0])
                

        if not os_path.exists(self.GRAB_BIN):
            return http.Response(responsecode.OK,stream='Grab is not installed at %s. Please install package aio-grab.' %self.GRAB_BIN)
        else:
            headers = http_headers.Headers()
            headers.addRawHeader('Content-Disposition', 'inline; filename=screenshot.%s;'%imageformat)
            headers.addRawHeader('Content-Type','image/%s'%imageformat)
            
            filename = filename+imageformat
            self.args.append(filename)
            cmd = self.baseCmd + self.args
            
            return http.Response(responsecode.OK,headers,stream=GrabStream(cmd, filename, save))
       
class GrabStream(stream.ProducerStream):
    '''
        used to start the grab-bin in the console in the background
        while this takes some time, the browser must wait until the grabis finished
    '''
    def __init__(self, cmd, target=None, save=False):
        self.target = target
        self.save = save
        self.output = ''
        stream.ProducerStream.__init__(self)

        self.container = eConsoleAppContainer()
        self.container.appClosed.append(self.cmdFinished)
        self.container.dataAvail.append(self.dataAvail)
        
        print '[Screengrab.py] starting AiO grab with cmdline:', cmd
        self.container.execute(*cmd)

    def cmdFinished(self, data):
        print '[Screengrab.py] cmdFinished'
        if int(data) is 0 and self.target is not None:
            try:
                fp = open(self.target)
                self.write(fp.read())
                fp.close()
                if self.save is False:
                    os_remove(self.target)
                    print '[Screengrab.py] %s removed' %self.target
            except Exception,e:
                self.write('Internal error while reading target file')
        elif int(data) is 0 and self.target is None:
            self.write(self.output)
        elif int(data) is 1:
            self.write(self.output)
        else:
            self.write('Internal error')
        self.finish()

    def dataAvail(self, data):
        print '[Screengrab.py] data Available ', data
