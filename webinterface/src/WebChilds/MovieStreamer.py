from twisted.web2 import resource, stream, responsecode, http, http_headers
import os

class MovieStreamer(resource.Resource):
    addSlash = True
    
    def render(self, req):
        class myFileStream(stream.FileStream):
            """
                because os.fstat(f.fileno()).st_size returns negative values on 
                large file, we set read() to a fix value
            """
            readsize = 10000    
            
            def read(self, sendfile=False):
                if self.f is None:
                    return None
        
                length = self.length
                if length == 0:
                    self.f = None
                    return None
        
                if sendfile and length > SENDFILE_THRESHOLD:
                    # XXX: Yay using non-existent sendfile support!
                    # FIXME: if we return a SendfileBuffer, and then sendfile
                    #        fails, then what? Or, what if file is too short?
                    readSize = min(length, SENDFILE_LIMIT)
                    res = SendfileBuffer(self.f, self.start, readSize)
                    self.length -= readSize
                    self.start += readSize
                    return res
        
                if self.useMMap and length > MMAP_THRESHOLD:
                    readSize = min(length, MMAP_LIMIT)
                    try:
                        res = mmapwrapper(self.f.fileno(), readSize,
                                          access=mmap.ACCESS_READ, offset=self.start)
                        #madvise(res, MADV_SEQUENTIAL)
                        self.length -= readSize
                        self.start += readSize
                        return res
                    except mmap.error:
                        pass
                # Fall back to standard read.
                readSize = self.readsize #this is the only changed line :} 3c5x9 #min(length, self.CHUNK_SIZE)
                
                self.f.seek(self.start)
                b = self.f.read(readSize)
                bytesRead = len(b)
                if not bytesRead:
                    raise RuntimeError("Ran out of data reading file %r, expected %d more bytes" % (self.f, length))
                else:
                    self.length -= bytesRead
                    self.start += bytesRead
                    return b
        try:
            w1 = req.uri.split("?")[1]
            w2 = w1.split("&")
            parts= {}
            for i in w2:
                w3 = i.split("=")
                parts[w3[0]] = w3[1]
        except:
            return http.Response(responsecode.OK, stream="no file given with file=???")            
        if parts.has_key("file"):
            path = "/hdd/movie/"+self.decodeURI(parts["file"])
            if os.path.exists(path):
                self.filehandler = open(path,"r")
                s = myFileStream(self.filehandler)
                return http.Response(responsecode.OK, {'Content-type': http_headers.MimeType('video', 'ts')},stream=s)
            else:
                return http.Response(responsecode.OK, stream="file '%s' was not found in /media/hdd/movie/"%self.decodeURI(parts["file"]))            
        else:
            return http.Response(responsecode.OK, stream="no file given with file=???")            
    
    def decodeURI(self,uri):
        """
        i dont have found a function that will do it in a clean way, so i do it like this
        change it, if you have foound one    
        """
        new = uri.encode("UTF-8").replace("%20"," ").replace("+"," ")
        new = new.replace("%C3%B6","ö")
        new = new.replace("%C3%96","Ö")
        new = new.replace("%C3%A4'","ä")
        new = new.replace("%C3%84'","Ä")
        new = new.replace("%C3%BC","ü")
        new = new.replace("%C3%9C","Ü")
        new = new.replace("%C3%9F","ß")
        
        return new