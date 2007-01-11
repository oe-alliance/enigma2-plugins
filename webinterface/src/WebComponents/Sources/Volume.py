from Components.Sources.Source import Source
from GlobalActions import globalActionMap

from time import time

class Volume( Source):
    def __init__(self, navcore):
        Source.__init__(self)
        
        
    def handleCommand(self, cmd):
        global globalActionMap
        if cmd == "up":
            globalActionMap.actions["volumeUp"]()
        elif cmd == "down":
            globalActionMap.actions["volumeDown"]()
        elif cmd == "mute":
            globalActionMap.actions["volumeMute"]()
        elif cmd == "value":
            pass 
        else:
            print "unknow Volume handle command",cmd
        