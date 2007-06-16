from twisted.web2 import resource, stream, responsecode, http, http_headers

from Plugins.Extensions.WebInterface import webif

import os


"""
    define all files in /web to send no  XML-HTTP-Headers here
    all files listed here will get an Content-Type: application/xhtml+xml charset: UTF-8
"""
AppTextHeaderFiles = ['stream.m3u.xml','ts.m3u.xml',] 

"""
 Actualy, the TextHtmlHeaderFiles should contain the updates.html.xml, but the IE then
 has problems with unicode-characters
"""
TextHtmlHeaderFiles = ['wapremote.xml','stream.xml',] 

"""
    define all files in /web to send no  XML-HTTP-Headers here
    all files listed here will get an Content-Type: text/html charset: UTF-8
"""
NoExplicitHeaderFiles = ['getpid.xml','tvbrowser.xml',] 

class ScreenPage(resource.Resource):
    def __init__(self, session,path):
        self.session = session
        self.path = path

    def render(self, req):
        #if self.session is not True:
        #    return http.Response(responsecode.OK, stream="please wait until enigma has booted")

        class myProducerStream(stream.ProducerStream):
            def __init__(self):
                stream.ProducerStream.__init__(self)
                self.closed_callback = None

            def close(self):
                if self.closed_callback:
                    self.closed_callback()
                    self.closed_callback = None
                stream.ProducerStream.close(self)

        if os.path.isfile(self.path):
            s=myProducerStream()
            webif.renderPage(s, self.path, req, self.session)  # login?
            if self.path.split("/")[-1] in AppTextHeaderFiles:
                return http.Response(responsecode.OK,{'Content-type': http_headers.MimeType('application', 'text', (('charset', 'UTF-8'),))},stream=s)
            elif self.path.split("/")[-1] in TextHtmlHeaderFiles:
                return http.Response(responsecode.OK,{'Content-type': http_headers.MimeType('text', 'html', (('charset', 'UTF-8'),))},stream=s)
            elif self.path.split("/")[-1] in NoExplicitHeaderFiles:
                return http.Response(responsecode.OK,stream=s)
            else:
                return http.Response(responsecode.OK,{'Content-type': http_headers.MimeType('application', 'xhtml+xml', (('charset', 'UTF-8'),))},stream=s)
        else:
            return http.Response(responsecode.NOT_FOUND)

    def locateChild(self, request, segments):
        path = self.path+'/'+'/'.join(segments)
        if path[-1:] == "/":
            path += "index.html"
        path +=".xml"
        return ScreenPage(self.session,path), ()
