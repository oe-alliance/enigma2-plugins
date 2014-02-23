# -*- coding: UTF-8 -*-

from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop

from . import _

# Error-print
from traceback import print_exc
from sys import stdout

# SH-Script
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
import os
SH_EXEC_FILE = resolveFilename(SCOPE_PLUGINS, "Extensions/EPGRefresh/EPGBackup.sh")
SH_TMP_OUTPUT="/tmp/.EPGBackup.sh.output"
BOOTCOUNTERFILE="/tmp/.EPGBackup.boot.counter"

FORCEBACKUPNOFILES="FORCEBACKUP_NOFILES"
FORCEBACKUPCANCEL="FORCEBACKUP_CANCEL"
EPGBACKUP_SHELL_CONSTANTS = { 'INSTALL': 'install',
		'UNINSTALL': 'uninstall',
		'SETFORCERESTORE': 'setforcefile',
		'EPGINFO': 'epginfo',
		'EPGINFOSORTSIZE': 'bySize',
		'ISPATCHED': 'ispatched',
		'STRINGBIGGEST': 'biggest',
		'STRINGYOUNGEST': 'youngest',
		'STRINGFORCED': 'force',
}
class EPGBackupSupport:
	"""Class for the Backup-Functionality"""

	def __init__(self, session):
		# Initialize
		self.session = session
		
		# We have succesfully booted, so delete the counter-File
		if os.path.exists(BOOTCOUNTERFILE):
			os.remove(BOOTCOUNTERFILE)

	def forceBackup(self):
		self._forceBackup()
		
	def forceBackupBySize(self):
		self._forceBackup(EPGBACKUP_SHELL_CONSTANTS["EPGINFOSORTSIZE"])
		
	def _forceBackup(self, sortMode = ""):
		backupList = self._getBackupFiles(sortMode)
		if len(backupList) == 0:
			backupList.append((_("No Backupfiles found"), FORCEBACKUPNOFILES))
		backupList.insert(0, (_("Cancel"), FORCEBACKUPCANCEL))
		self.session.openWithCallback(self._forceBackupCB,
			ChoiceBox, _("Select a file to force a Backup"), backupList)
	
	def _forceBackupCB(self, backupinfo):
		if backupinfo is None:
			return
		else:
			backupfile = backupinfo [1].rstrip()
			if backupfile[1] and FORCEBACKUPCANCEL != backupfile and FORCEBACKUPNOFILES != backupfile:
				self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["SETFORCERESTORE"], backupinfo[1].rstrip())
				self.session.openWithCallback(self._restartGUICB, MessageBox, \
					_("To load the Backupfile the GUI has to be restarted.\nDo you want to restart the GUI now?"), \
					MessageBox.TYPE_YESNO, timeout =  30, default = False)

	def _restartGUICB(self, answer):
		if answer is True:
			self.session.open(TryQuitMainloop, 3)
	
	def _getBackupFiles(self, sortMode):
		try:
			backupList = []
			backupStrList = self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["EPGINFO"], sortMode, True)
			if backupStrList:
				backupfiles = backupStrList.split("\n")
			if backupfiles:
				for file in backupfiles:
					if file:
						file = file.replace(EPGBACKUP_SHELL_CONSTANTS["STRINGBIGGEST"], _("FILELIST_BIGGEST"))
						file = file.replace(EPGBACKUP_SHELL_CONSTANTS["STRINGYOUNGEST"], _("FILELIST_YOUNGEST"))
						file = file.replace(EPGBACKUP_SHELL_CONSTANTS["STRINGFORCED"], _("FILELIST_FORCED"))
						backupList.append(( file, file.split(" ")[0] ))
		except:
			print("[EPGRefresh] getBackupFiles Error")
			print_exc(file=stdout)
		return backupList
	
	def install(self):
		self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["INSTALL"])
	
	def uninstall(self):
		self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["UNINSTALL"])

	def isPatched(self):
		ispatched = False
		ispatchedtxt = self.executeShScript(EPGBACKUP_SHELL_CONSTANTS["ISPATCHED"], getoutput = True)
		if ispatchedtxt == "true":
			ispatched = True
		return ispatched

	def executeShScript(self, sh_action, param1 = "", getoutput = False):
		outtext = ""
		if getoutput:
			os.system(SH_EXEC_FILE + " %s %s > %s" %(sh_action, param1, str(SH_TMP_OUTPUT)))
			fo=open(str(SH_TMP_OUTPUT))
			line = fo.readline()
			while (line):
				outtext += line
				line = fo.readline()
			fo.close
		else:
			print("[EPGRefresh] execute sh wiht params %s %s" %(sh_action, param1))
			os.system(SH_EXEC_FILE + " %s %s" %(sh_action, param1))
		return outtext



