from __future__ import print_function
from Plugins.Extensions.Widgets.Widget import Widget
from Components.Label import Label


class TestWidget(Widget):
    def __init__(self, session):
        Widget.__init__(self, session, name="Static Text Widget", description="Example of a simple Widget with static text", version="0.1", author="3c5x9", homepage="cvs://schwerkraft")
        self.elements["testwidget_title"] = Label("ich bin ein test widget")
        self.elements["testwidget_blablub"] = Label("bla bla blub")

    def onLoadFinished(self, instance):
        print("refresh TestWidget")


def get_widget(session):
    return TestWidget(session)
