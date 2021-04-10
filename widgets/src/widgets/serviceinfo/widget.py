from Plugins.Extensions.Widgets.Widget import Widget


class ServiceinfoWidget(Widget):
    def __init__(self, session):
        Widget.__init__(self, session, name="Service Info", description="NIM and Position data", version="0.1", author="3c5x9", homepage="cvs://schwerkraft")


def get_widget(session):
    return ServiceinfoWidget(session)
