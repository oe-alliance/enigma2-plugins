from Plugins.Extensions.Widgets.Widget import Widget
from Components.Label import Label


class FrontendstatusWidget(Widget):
    def __init__(self, session):
        Widget.__init__(self, session, name="FrontendStatus", description="shows the Frontend Status of the tuned service", version="0.1", author="3c5x9", homepage="cvs://schwerkraft")
        self.elements["frontendstatuswidget_SNR"] = Label(_("SNR") + ":")
        self.elements["frontendstatuswidget_AGC"] = Label(_("AGC") + ":")
        self.elements["frontendstatuswidget_BER"] = Label(_("BER") + ":")


def get_widget(session):
    return FrontendstatusWidget(session)
