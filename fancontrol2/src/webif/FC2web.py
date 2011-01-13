from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Plugins.Extensions.FanControl.FC2webSite import FC2web, FC2webLog, FC2webChart
root = FC2web()
root.putChild("log", FC2webLog())
root.putChild("chart", FC2webChart())
addExternalChild( ("fancontrol", root) )