from __future__ import print_function
import skin
from Components.Label import Label

class Widget:
    
    
    def __init__(self, session, name="no Name", description="unknown Description", version="unknown Version", author="unknown Author", homepage="http://www.unknown.de"):
        self.name = name
        self.author = author
        self.description = description
        self.version = version
        self.homepage = homepage
        self.session = session
        self.dir = "" # the directory the widget is saved in the filesystem
        self.elements = {} # contains all Labels etc. 
        self.prefix = "" # the prefix of the name of the elements after it is patched into the main screen skin depending on its place in the widgetdesktop 
        self.wname = "" # the place name, the widget is placed and running in
        
    def setDir(self, directory):
        """ called after the import """
        self.dir = directory
            
    def setPositionname(self, wname):
        """ called after the widget is placed at a place at the widgetdesktop """
        self.wname = wname
        self.prefix = wname + "_e_"
    
    def getElement(self, elementname):
        """ returns the intance of an element of self.elements """
        return self.instance[self.prefix + elementname]  
    
    def onLoadFinished(self, instance):
        """ overwrite this in your widget to do things after the widget is shown on the widgetdesktop """
        self.instance = instance
    
    def onClose(self):
        """ overwrite this, if you have to stop things when the widgetdesktop """
        pass
    
    def onInfo(self):
        """ overwrite this, if you whant to do something if the user presses the info-key and your widget is selected """
        print("unhandled infokey")
