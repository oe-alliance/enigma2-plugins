from __future__ import print_function
from Plugins.Extensions.Widgets.Widget import Widget
from Components.Label import Label
from enigma import eTimer


class CounterWidget(Widget):
    def __init__(self, session):
        Widget.__init__(self, session, name="Simple Counter Widget", description="Example of a Widget with dynamicly changing Text", version="0.1", author="3c5x9", homepage="cvs://schwerkraft")
        self.elements["counter_title"] = Label("0")
        self.Timer = eTimer()
        self.Timer.callback.append(self.TimerFire)
        self.counter = 0
       
    def onLoadFinished(self, instance):
        self.instance = instance
        print("refresh CounterWidget")
        
        self.getElement("counter_title").setText("###")
        self.Timer.start(200)
        
    def onClose(self):
        self.Timer.stop()
        
    def TimerFire(self):
        #print "TimerFire"
        self.counter += 1
        try:
            self.getElement("counter_title").setText(str(self.counter))
            self.Timer.start(200)
        except Exception as e:
            pass
        

def get_widget(session):
    return CounterWidget(session)
