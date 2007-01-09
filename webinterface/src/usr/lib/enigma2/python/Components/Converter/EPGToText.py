# -*- coding: utf-8 -*-
from Converter import Converter
from xml.dom.minidom import Document
class EPGToText(Converter, object):
    
    def __init__(self, type):
        Converter.__init__(self, type)
        print "Converter.EPGToText type=",type
        self.type = type
    def getHTML(self,value):
        print "Converter.getHTML value=",value       
        return self.getText();
    def getText(self):
        if self.type == "search":
            return self.EPGListToXML(self.source.searchEvent())
        elif self.type == "service":
            return self.EPGListToXML(self.source.getEPGofService())
        elif self.type == "nownext":
            return self.EPGListToXML(self.source.getEPGNowNext())
        else:
            return "unknown type ",type
    def EPGListToXML(self,epglist):
        if epglist :
            xmlDocument = Document()
            rootNode = xmlDocument.createElement('EPGList')
            for row in epglist:
                itemnode = xmlDocument.createElement('EPGEvent')
                for key, val in row.items():
                        keynode = xmlDocument.createElement(key)
                        textnode = xmlDocument.createTextNode(val)
                        keynode.appendChild(textnode)
                        itemnode.appendChild(keynode);
                rootNode.appendChild(itemnode)
                xmlDocument.appendChild(rootNode)
            return xmlDocument.toxml()
        else:
            return "no data"
            
    text = property(getText,getHTML)