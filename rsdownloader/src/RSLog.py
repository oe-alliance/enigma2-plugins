##
## RS Downloader
## by AliAbdul
##
from Components.ActionMap import ActionMap
from Components.ScrollLabel import ScrollLabel
from RSConfig import config
from RSTranslation import TitleScreen
from time import strftime, time, localtime

##############################################################################

def writeLog(message):
	mayWrite = config.plugins.RSDownloader.write_log.value
	
	if mayWrite:
		log_file = "/tmp/rapidshare.log"
		
		try:
			f = open(log_file, "r")
			log = f.read()
			f.close()
		except:
			log = ""
		
		log = log + strftime("%c", localtime(time())) + " - " + message + "\n"
		
		try:
			f = open(log_file, "w")
			f.write(log)
			f.close()
		except:
			pass
##############################################################################

class RSLogScreen(TitleScreen):
	skin = """
		<screen position="100,100" size="520,400" title="RS Downloader" >
			<widget name="label" position="0,0" size="520,400" font="Regular;20" />
		</screen>"""

	def __init__(self, session):
		TitleScreen.__init__(self, session)
		
		try:
			f = open("/tmp/rapidshare.log")
			log = f.read()
			f.close()
		except:
			log = ""
		self["label"] = ScrollLabel(log)
		
		self["actions"] = ActionMap(["WizardActions"],
			{
				"ok": self.close,
				"back": self.close,
				"up": self["label"].pageUp,
				"down": self["label"].pageDown,
				"left": self["label"].pageUp,
				"right": self["label"].pageDown
			}, -1)
