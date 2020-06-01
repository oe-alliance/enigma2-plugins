#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright (C) 2011 cmikula

In case of reuse of this source code please do not remove this copyright.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    For more information on the GNU General Public License see:
    <http://www.gnu.org/licenses/>.

For example, if you distribute copies of such a program, whether gratis or for a fee, you 
must pass on to the recipients the same freedoms that you received. You must make sure 
that they, too, receive or can get the source code. And you must show them these terms so they know their rights.
'''
from __future__ import print_function

import SocketServer
import socket

serverInstance = None

def getIpAddress(iface):
    interfaces = []
    # parse the interfaces-file
    try:
        fp = file('/etc/network/interfaces', 'r')
        interfaces = fp.readlines()
        fp.close()
    except:
        print("[AdvancedMovieSelection] interfaces - opening failed")

    currif = ""
    for i in interfaces:
        split = i.strip().split(' ')
        if (split[0] == "iface"):
            currif = split[1]
        if (currif == iface): #read information only for available interfaces
            if (split[0] == "address"):
                return split[1]
    return None

class TCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        try:
            from Client import MessageQueue
            # self.request is the TCP socket connected to the client
            data = self.request.recv(1024).strip()
            #print str(self.client_address[0]), "wrote"
            #print(data)
            self.request.send(MessageQueue.getRequest(data))
        except Exception as e:
            print(e)

class MessageServer():
    def __init__(self):
        global serverInstance
        if serverInstance:
            raise Exception("Only one instance of MessageServer is allowed")
        self.server = None
        self.active_clients = []
        self.host = getIpAddress('eth0')
        self.port = 20000
        self.ip_from = 1
        self.ip_to = 254

    def start(self):
        if not self.host:
            print("[AdvancedMovieSelection] Could not start server, no static host ip")
            return
        import threading
        self.shutdown()
        self.server = SocketServer.TCPServer((self.host, self.port), TCPHandler)
        self.t = threading.Thread(target=self.server.serve_forever)
        self.t.setDaemon(True) # don't hang on exit
        self.t.start()
        print("[AdvancedMovieSelection] Server started:", self.host, self.port)

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            print("[AdvancedMovieSelection] Server stopped:")
        
    def reconnect(self, host=None, port=None):
        if host:
            self.host = host
        if port:
            self.port = port
        self.start()
        
    def getHost(self):
        return self.host
    
    def getPort(self):
        return self.port

    def setPort(self, port):
        self.port = port

    def findClients(self):
        from Client import Client
        self.active_clients = []
        ip = self.host.split(".")
        ip = "%s.%s.%s" % (ip[0], ip[1], ip[2])
        for x in range(self.ip_from, self.ip_to + 1):
            try:
                # Connect to server and send data
                host = "%s.%s" % (ip, x)
                print("[AdvancedMovieSelection] Try connect to: %s:%s" % (host, self.port))
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                sock.connect((host, self.port))
                sock.close()
                client = Client(host, self.port)
                if client.getDeviceName() != "Error":
                    self.active_clients.append(client)
            except:
                pass
            finally:
                sock.close()
        
    def startScanForClients(self):
        import threading
        t = threading.Thread(target=self.findClients)
        t.start()
        
    def getClients(self):
        return self.active_clients
    
    def setSearchRange(self, ip_from, ip_to):
        if ip_from > ip_to or ip_to >= 255:
            return
        self.ip_from = ip_from
        self.ip_to = ip_to
        
serverInstance = MessageServer()
