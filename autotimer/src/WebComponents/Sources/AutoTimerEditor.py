from Components.Sources.Source import Source
from os import remove, path, popen
from re import compile as re_compile

class AutoTimerEditor(Source):
	BACKUP = 0
	RESTORE = 1

	BACKUP_PATH = "/tmp"
	BACKUP_FILENAME = "autotimer_backup.tar"

	def __init__(self, session, func=BACKUP):
		Source.__init__(self)
		self.func = func
		self.session = session
		self.command = None
		self.bouquet_rootstr = ""
		self.result = ( False, "one two three four unknown command" )

	def handleCommand(self, cmd):
		print "[WebComponents.AutoTimerEditor] handleCommand with cmd = ", cmd
		if self.func is self.BACKUP:
			self.result = self.backupFiles(cmd)
		elif self.func is self.RESTORE:
			self.result = self.restoreFiles(cmd)
		else:
			self.result = ( False, "one two three four unknown command" )

	def backupFiles(self, param):
		filename = param
		if not filename:
			filename = self.BACKUP_FILENAME
		invalidCharacters= re_compile(r'[^A-Za-z0-9_. ]+|^\.|\.$|^ | $|^$')
		tarFilename= "%s.tar" % invalidCharacters.sub('_', filename)
		backupFilename = path.join(self.BACKUP_PATH, tarFilename)
		if path.exists(backupFilename):
			remove(backupFilename)
		checkfile = path.join(self.BACKUP_PATH,'.autotimeredit')
		f = open(checkfile, 'w')
		if f:
			files = []
			f.write('created with AutoTimerWebEditor')
			f.close()
			files.append(checkfile)
			files.append("/etc/enigma2/autotimer.xml")
			tarFiles = ""
			for arg in files:
				if not path.exists(arg):
					return (False, "Error while preparing backup file, %s does not exists." % arg)
				tarFiles += "%s " % arg
			lines = popen("tar cvf %s %s" % (backupFilename,tarFiles)).readlines()
			remove(checkfile)
			return (True, tarFilename)
		else:
			return (False, "Error while preparing backup file.")

	def restoreFiles(self, param):
		backupFilename = param
		if path.exists(backupFilename):
			check_tar = False
			lines = popen('tar -tf %s' % backupFilename).readlines()
			for line in lines:
				pos = line.find('tmp/.autotimeredit')
				if pos != -1:
					check_tar = True
					break
			if check_tar:
				lines = popen('tar xvf %s -C /' % backupFilename).readlines()

				from Plugins.Extensions.AutoTimer.plugin import autotimer
				if autotimer is not None:
					try:
						# Force config reload
						autotimer.configMtime = -1
						autotimer.readXml()
					except Exception:
						# TODO: proper error handling
						pass
				
				remove(backupFilename)
				return (True, "AutoTimer-settings were restored successfully")
			else:
				return (False, "Error, %s was not created with AutoTimerWebEditor..." % backupFilename)
		else:
			return (False, "Error, %s does not exists, restore is not possible..." % backupFilename)
