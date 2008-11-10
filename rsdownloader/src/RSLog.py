##
## RS Downloader
## by AliAbdul
##
from RSConfig import config
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
