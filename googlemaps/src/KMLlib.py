###############################################################################
# Copyright (c) 2008 Rico Schulte, 3c5x9. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
###############################################################################

from globalmaptiles import GlobalMercator
from xml.dom.minidom import parse
from os import listdir
    
class KmlPlace:
    def __init__(self,kmlnode):
        self.kmlnode = kmlnode
        self.name = kmlnode.getElementsByTagName('name')[0].firstChild.data.encode("utf-8")
        lons = kmlnode.getElementsByTagName('LookAt')[0].getElementsByTagName('longitude')[0].firstChild.data.encode("utf-8")
        lats = kmlnode.getElementsByTagName('LookAt')[0].getElementsByTagName('latitude')[0].firstChild.data.encode("utf-8")
                    
        lat = float(lats)
        lon = float(lons)
        if lat<0.0:
            lat = lat*(-1.0)
        if lon<0.0:
            lon=lon*(-1.0)
        self.lat = lat
        self.lon = lon
    
    def getTile(self,zoomlevel):
        mercator = GlobalMercator()
        mx, my = mercator.LatLonToMeters( self.lat, self.lon )
        tminx, tminy = mercator.MetersToTile( mx, my, zoomlevel )
        gx, gy = mercator.GoogleTile(tminx, tminy, zoomlevel)#+1?
        return gx,gy,zoomlevel

    def __str__(self):
        return "KmlPlace ('"+self.name+"','"+str(self.lat)+"','"+str(self.lon)+"')"
    
class KmlFolder:
    parent = None
    def __init__(self,kmlnode):
        self.kmlnode = kmlnode
        self.name = kmlnode.getElementsByTagName('name')[0].firstChild.data.encode("utf-8")
    
    def getFolders(self):
        list = []
        for i in self.kmlnode.getElementsByTagName('Folder'):
            folder = KmlFolder(i)
            folder.parent = self
            list.append(folder)
        #list.pop(0)
        return list
    
    def getPlacemarks(self):
        list = []
        for i in self.kmlnode.getElementsByTagName('Placemark'):
            point = KmlPlace(i)
            try: # test if we can handle this coords
                point.getTile(15)# 15 is just a zoomlevel in the middle :)
                list.append(point)
            except ValueError,e:
                print "Import Error: ",point.name,e
        return list
            
class RootFolder:
    extension = '.kml' 
    def __init__(self):
        pass
    
    def getFolderFromFile(self,filepath):
        return KmlFolder(self.parseFile(filepath))
    
    def parseFile(self,filepath):
        print "parsing ",filepath
        return parse(filepath)        

    def getFiles(self,path):
        list = []
        for file in listdir(path):
            if file.endswith(self.extension):
                list.append((file.split('.')[0],path+file))
        return list

