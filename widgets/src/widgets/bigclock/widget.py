from Plugins.Extensions.Widgets.Widget import Widget
from Components.Label import Label
#from Components.Clock import Clock
from enigma import eSize, ePoint


class BigclockWidget(Widget):
    def __init__(self, session):
        Widget.__init__(self, session, name="Big Clock Widget", description="a simple big clock", version="0.1", author="3c5x9", homepage="cvs://schwerkraft")


def get_widget(session):
    return BigclockWidget(session)
