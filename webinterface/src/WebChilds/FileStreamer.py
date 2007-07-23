from twisted.web2 import resource, stream, responsecode, http, http_headers
from os import path as os_path

class FileStreamer(resource.Resource):
    addSlash = True
    
    def render(self, req):
        try:
            w1 = req.uri.split("?")[1]
            w2 = w1.split("&")
            parts= {}
            for i in w2:
                w3 = i.split("=")
                parts[w3[0]] = w3[1]
        except:
            return http.Response(responsecode.OK, stream="no file given with file=???")
        root = "/hdd/movie/"
        if parts.has_key("root"):
            root = parts["root"].replace("%20"," ")
        if parts.has_key("file"):
            filename = parts["file"].replace("%20"," ")
            path = root+filename
            if os_path.exists(path):
                s = stream.FileStream(open(path,"r"))
                type = path.split(".")[-1]
                header = http_headers.MimeType('video', 'ts')
                if type == "mp3" or type == "ogg" or type == "wav":
                    header = http_headers.MimeType('audio', 'x-mpeg')
                elif type == "avi" or type == "mpg":
                    header = http_headers.MimeType('video', 'x-msvideo')
                elif type == "jpg" or type == "jpeg" or type == "jpe":
                    header = http_headers.MimeType('image', 'jpeg')
                
                resp =  http.Response(responsecode.OK, {'Content-type': header},stream=s)
                resp.headers.addRawHeader('Content-Disposition','attachment; filename="%s"'%filename)
                return resp
            else:
                return http.Response(responsecode.OK, stream="file '%s' was not found"%path)            
        else:
            return http.Response(responsecode.OK, stream="no file given with file=???")            
    
