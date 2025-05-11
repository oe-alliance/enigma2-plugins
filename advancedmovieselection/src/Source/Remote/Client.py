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
from __future__ import absolute_import

from .MessageServer import serverInstance
import socket


class MessageQueue:
    @staticmethod
    def getRequest(data):
        request = data
        if data == "isRecording":
            import NavigationInstance
            if NavigationInstance.instance.getRecordings():
                request = "True"
            else:
                request = "False"
        elif data == "getDeviceName":
            from Components.SystemInfo import BoxInfo
            request = BoxInfo.getItem("model")
        elif data == "inStandby":
            import Screens
            request = str(Screens.Standby.inStandby is not None)
        elif data.startswith("setPort"):
            try:
                from Components.config import config
                port = int(data.replace("setPort", ""))
                serverInstance.reconnect(port=port)
                config.AdvancedMovieSelection.server_port.value = port
                config.AdvancedMovieSelection.server_port.save()
            except Exception as e:
                print(e)
        elif data == "nextTrashEvent":
            from Components.config import config
            if config.AdvancedMovieSelection.auto_empty_wastebasket.value == "-1":
                return "-1"
            request = str(config.AdvancedMovieSelection.next_auto_empty_wastebasket.value)
        elif data == "lastTrashEvent":
            from Components.config import config
            if config.AdvancedMovieSelection.auto_empty_wastebasket.value == "-1":
                return "-1"
            request = str(config.AdvancedMovieSelection.last_auto_empty_wastebasket.value)
        return request


def getClients():
    return serverInstance.active_clients


def isAnyRecording():
    clients = getClients()
    for client in clients:
        if client.isRecording():
            return True
    return False


class Client:
    def __init__(self, ip, port):
        print(ip, port)
        self.ip = ip
        self.port = port
        self.device = self.sendData("getDeviceName")
        self.name = ""  # self.sendData("getName")

    def sendData(self, data):
        request = "Error"
        try:
            # Connect to server and send data
            print("[AdvancedMovieSelection] Send message to: %s:%s" % (self.ip, self.port), data)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((self.ip, self.port))
            sock.send(data)
            # Receive data from the server and shut down
            request = sock.recv(1024)
        except:
            pass
        finally:
            sock.close()
        print("[AdvancedMovieSelection] Get request:", request)
        return request

    def setPort(self, port):
        self.sendData("setPort" + str(port))
        self.port = port

    def getAddress(self):
        return self.ip

    def getPort(self):
        return self.port

    def getDeviceName(self):
        return self.device

    def getName(self):
        return self.name

    def isRecording(self):
        return self.sendData("isRecording") == "True"

    def inStandby(self):
        return self.sendData("inStandby") == "True"

    def nextTrashEvent(self):
        ev = 0
        try:
            ev = int(self.sendData("nextTrashEvent"))
        except:
            pass
        return ev

    def lastTrashEvent(self):
        ev = 0
        try:
            ev = int(self.sendData("lastTrashEvent"))
        except:
            pass
        return ev


if __name__ == "__main__":
    print(Client("192.168.0.97", 20000).isRecording())
