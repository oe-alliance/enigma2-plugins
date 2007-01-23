from enigma import *
from Components.Sources.Source import Source
from Screens.MessageBox import MessageBox

class Message( Source):
        
    def __init__(self,session):
        self.cmd = []
        self.session = session
        Source.__init__(self)

    def handleCommand(self, cmd):
        self.cmd = cmd
        
    def do_func(self):
        list = []
        
        if self.cmd['text'] == "" or self.cmd['text'] is None:
            return [[False,"no text for message"]]
        else:
            mtext = self.cmd['text']

        try:
            typeint = int(self.cmd['type'])
        except ValueError,e:
            return [[False,"type %s is not a number"%self.cmd['type']]]   
            
        if typeint == MessageBox.TYPE_YESNO:
            #dont know how to give the result to the webif back 
            mtype= MessageBox.TYPE_YESNO
        elif typeint == MessageBox.TYPE_INFO:
            mtype= MessageBox.TYPE_INFO
        elif typeint == MessageBox.TYPE_WARNING:
            mtype= MessageBox.TYPE_WARNING
        elif typeint == MessageBox.TYPE_ERROR:
            mtype= MessageBox.TYPE_ERROR
        else:
            return [[False,"unsupported type %s"%self.cmd['type']]]   
        
        try:
            mtimeout = int(self.cmd['timeout'])
        except ValueError,e:
            mtimeout = -1   
        
        self.session.open(MessageBox, mtext, type = mtype ,timeout = mtimeout)
        
        return [[True,"Message send to screen"]]
    
    list = property(do_func)
    lut = {"Result": 0
           ,"ResultText": 1
           }

