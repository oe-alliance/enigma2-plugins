from enigma import *
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor

class TuxComStarter(Screen):
	skin = """
		<screen position="1,1" size="1,1" title="TuxCom" >
                </screen>"""

        def __init__(self, session, args = None):
        	self.skin = TuxComStarter.skin
		Screen.__init__(self, session)
		self.container=eConsoleAppContainer()
		self.container.appClosed.append(self.finished)
		self.runapp()
		
	def runapp(self):
		eDBoxLCD.getInstance().lock()
		eRCInput.getInstance().lock()
		fbClass.getInstance().lock()
		if self.container.execute("/usr/bin/tuxcom"):
			self.finished(-1)

	def finished(self,retval):
		fbClass.getInstance().unlock()
		eRCInput.getInstance().unlock()
		eDBoxLCD.getInstance().unlock()
		self.close()

def main(session, **kwargs):
	session.open(TuxComStarter)

def Plugins(**kwargs):
	return PluginDescriptor(name="TuxCom", description="TuxBox Commander", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
	
