#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2012 cmikula
#
#    In case of reuse of this source code please do not remove this copyright.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    For more information on the GNU General Public License see:
#    <http://www.gnu.org/licenses/>.
#
#    For example, if you distribute copies of such a program, whether gratis or for a fee, you
#    must pass on to the recipients the same freedoms that you received. You must make sure
#    that they, too, receive or can get the source code. And you must show them these terms so they know their rights.
#

from __future__ import print_function
import os
import ping


class Network():
    AUTO_NETORK = "/etc/auto.network"
    AUTO_MASTER = "/etc/auto.master"

    def __init__(self):
        self.auto_network = []
        self.mount_path = "/media/net"

    def isMountOnline(self, mount_dir):
        try:
            if mount_dir == "/":
                return True
            for network in self.auto_network:
                if mount_dir.startswith(network[0]):
                    print("check mount:", network[1] + ":" + mount_dir)
                    delay = ping.do_one(network[1], 0.2)
                    if delay:
                        print("success", delay)
                        return True
                    else:
                        print("failed")
                        return False
            return True
        except Exception as e:
            print(e)
            return True

    def getOnlineMount(self, dirs):
        online = []
        for directory in dirs:
            if not autoNetwork.isMountOnline(directory): # or not os.path.exists(directory):
                continue
            online.append(directory)
        return online

    def updateAutoNetwork(self):
        self.auto_network = []
        try:
            print("update auto.network")
            if os.path.exists(self.AUTO_MASTER):
                rfile = open(self.AUTO_MASTER, 'r')
                for x in rfile.readlines():
                    if self.AUTO_NETORK in x:
                        self.mount_path = x.split(" ")[0]
                        print("update from auto.master:", self.mount_path)
            if os.path.exists(self.AUTO_NETORK):
                rfile = open(self.AUTO_NETORK, 'r')
                for x in rfile.readlines():
                    val = x.strip().split(' ')
                    if len(val) >= 2 and not '#' in val[0]:
                        val[2] = val[2].replace('://', '').replace(':/', '/', 1) # only for cifs mount
                        dest_addr = val[2].split('/')[0]
                        self.auto_network.append((os.path.join(self.mount_path, val[0]), dest_addr))
            print(self.auto_network)
        except Exception as e:
            print(e)


autoNetwork = Network()
