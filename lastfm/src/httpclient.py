
import base64

import socket
import string

True = 1
False = 0

class httpclient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.status = None
        self.headers = None
        self.response = None

    def readline(self, s):
        res = ""
        while True:
            try:
                c = s.recv(1)
            except:
                break
            res = res + c
            if c == '\n':
                break
            if not c:
                break
        #print res
        return res

    def req(self, url):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
#        if config.useproxy:
#            s.connect((config.proxyhost, config.proxyport))
#            s.send("GET http://" + self.host + ":" + str(self.port) + url + " HTTP/1.0\r\n")
#            if config.proxyuser != "":
#                s.send("Proxy-Authorization: Basic " + base64.b64encode(config.proxyuser + ":" + config.proxypass) + "\r\n")
#        else:
#            print "reg: ",self.host, self.port,url
            s.connect((self.host, self.port))
            s.send("GET " + url + " HTTP/1.0\r\n")
            s.send("Host: " + self.host + "\r\n")
            s.send("\r\n")

            line = self.readline(s)
            #print line
            self.status = string.rstrip(line)
            
            self.headers = {}
            while True:
                line = self.readline(s)
                if not line:
                    break
                if line == "\r\n":
                    break
                tmp = string.split(line, ": ")
                try:
                  self.headers[tmp[0]] = string.rstrip(tmp[1])
                except:
                  print "BUG"
                  print "self.headers[tmp[0]] = string.rstrip(tmp[1]) has no tmp[1]"
                  print line
                  print tmp              
            self.response = ""
            while True:
                line = self.readline(s)
                if not line:
                    break
                self.response = self.response + line
            s.close()
        except socket.error,e:
            print e
            self.response = ""
            return False,e
