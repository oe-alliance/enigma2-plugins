from os import statvfs, path as os_path, system as os_system, chmod as os_chmod
from twisted.web2 import resource, responsecode, http, http_headers

class UploadResource(resource.PostableResource):
    default_uploaddir = "/tmp/"
    
    def render(self, req):
        self.args = req.args
        #############
        uploaddir=self.default_uploaddir
        if self.getArg("path"):
            if os_path.isdir(self.getArg("path")):
                uploaddir= self.getArg("path")
                if uploaddir[-1] != "/":
                    uploaddir += "/"
            else:
                return http.Response(responsecode.OK,{'content-type': http_headers.MimeType('text', 'html')},"path '%s' to upload not existing!"%self.getArg("path"))
        #########
        if len(req.files):
            #static.destination = uploaddir
            return self.do_upload(req,uploaddir)
        else:
            return self.do_indexpage(req)
    
    def do_upload(self,req,uploaddir):
        for file in req.files:
            import tempfile
            (filename,mimetype,filehandler) = req.files[file][0]
#            filehandler.name = tempfile.mktemp(suffix=os_path.splitext(filename)[1], dir=uploaddir)
            print "filehandler.name: ",filehandler.name
            filehandler.seek(0, 2)  # Seek to the end of the file.
            filesize = filehandler.tell()  # Get the position of EOF.
            filehandler.seek(0)  # Reset the file position to the beginning.
            if filesize <=0:
                os_system("rm '%s'" %filehandler.name)
                return http.Response(responsecode.OK,{'content-type': http_headers.MimeType('text', 'html')},"filesize was 0, not uploaded")
            else:
                os_system("mv '%s' '%s' " %(filehandler.name,uploaddir+filename))
                os_chmod(uploaddir+filename, 0755)
                return http.Response(responsecode.OK,{'content-type': http_headers.MimeType('text', 'html')},"uploaded to %s"%uploaddir+filename)
    
    def do_indexpage(self,req):
        try:
            stat = statvfs("/tmp/")
        except OSError:
            return -1
        
        freespace = stat.f_bfree / 1000 * stat.f_bsize / 1000
        
        return http.Response(responsecode.OK,
                             {'content-type': http_headers.MimeType('text', 'html')},
        """
                <form method="POST" enctype="multipart/form-data">
                <table>
                <tr><td>Path to save (default is '%s')</td><td><input name="path"></td></tr>
                <tr><td>File to upload</td><td><input name="file" type="file"></td></tr>
                <tr><td colspan="2">Filesize must not be greather than %dMB! /tmp/ has not more free space!</td></tr>
                <tr><td colspan="2"><input type="submit"></td><tr>
                </table>
                </form>
                
        """%(self.default_uploaddir,freespace))

    def getArg(self,key):
        if self.args.has_key(key):
            return self.args[key][0]
        else:
            return False
